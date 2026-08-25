import { defineStore } from "pinia";
import { ref } from "vue";
import { useAuthStore } from "./auth";

const API_BASE_URL = "/api/v1";
// Ikut alamat halaman, bukan ditulis mati. Lewat tunnel HTTPS, "ws://" akan
// ditolak browser -- harus "wss://" -- dan host-nya pun bukan localhost lagi.
const WS_URL = `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws/dashboard`;

export interface HistoryOptions {
  range?: "1h" | "1d" | "1w" | "1M";
  start?: string;
  end?: string;
  results?: number;
  average?: number;
  force?: boolean;
}

export const useTelemetryStore = defineStore("telemetry", () => {
  const authStore = useAuthStore();

  // State: NodeId -> Live telemetry feeds (index 0 is newest, updated by WS)
  const telemetryHistory = ref<Record<string, any[]>>({});
  // State: NodeId -> Static Archive telemetry feeds (oldest first, for historical ranges 1w, 1M, custom)
  const archiveHistory = ref<Record<string, any[]>>({});
  const isArchiveLoading = ref<Record<string, boolean>>({});
  const isConnected = ref(false);

  // Sensor per node, disimpan supaya handler WebSocket bisa membaca ambangnya
  // tanpa menembak API tiap kali ada pesan masuk.
  const sensorsByNode = ref<Record<string, any[]>>({});

  // {sensorId: sedang di luar ambang} -- supaya notifikasi muncul sekali saat
  // melewati batas dan sekali saat pulih, bukan tiap pembacaan.
  const statusAlert: Record<string, boolean> = {};

  const notifAktif = ref(
    typeof Notification !== "undefined" &&
      Notification.permission === "granted",
  );

  const mintaIzinNotif = async () => {
    if (typeof Notification === "undefined") return false;
    const hasil = await Notification.requestPermission();
    notifAktif.value = hasil === "granted";
    return notifAktif.value;
  };

  const tampilkanNotif = (judul: string, isi: string, tag: string) => {
    // Dibaca langsung dari browser, bukan dari notifAktif. Ref itu cuma potret
    // saat store dibuat, sementara izin bisa berubah setelahnya tanpa halaman
    // dimuat ulang -- dan kalau itu terjadi, notifikasi hilang tanpa jejak.
    if (
      typeof Notification === "undefined" ||
      Notification.permission !== "granted"
    )
      return;
    try {
      // tag: notifikasi bertag sama saling menimpa, jadi satu sensor tidak
      // menumpuk banyak gelembung di layar.
      new Notification(judul, { body: isi, tag, icon: "/favicon.svg" });
    } catch (e) {
      console.error("[TelemetryStore] Gagal menampilkan notifikasi", e);
    }
  };

  // --- Web Push: notifikasi tetap datang walau dashboard ditutup ---

  const webpushAktif = ref(false);

  // Kunci VAPID datang sebagai base64url; pushManager menuntut Uint8Array.
  const kunciKeBytes = (base64: string) => {
    const padding = "=".repeat((4 - (base64.length % 4)) % 4);
    const b64 = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
    const mentah = atob(b64);
    return Uint8Array.from([...mentah].map((c) => c.charCodeAt(0)));
  };

  const cekWebpush = async () => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) return false;
    const reg = await navigator.serviceWorker.getRegistration("/sw.js");
    const sub = reg ? await reg.pushManager.getSubscription() : null;
    webpushAktif.value = !!sub;
    return webpushAktif.value;
  };

  const daftarWebpush = async () => {
    // Service worker hanya jalan di HTTPS atau localhost. Dari HP lewat
    // http://<ip-laptop>:5173 ia tidak akan terdaftar sama sekali.
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      console.warn("[TelemetryStore] Browser tidak mendukung Web Push");
      return false;
    }

    try {
      if ((await Notification.requestPermission()) !== "granted") return false;

      const reg = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;

      const res = await fetch(`${API_BASE_URL}/push/public-key`);
      if (!res.ok) return false;
      const { public_key } = await res.json();

      const sub =
        (await reg.pushManager.getSubscription()) ||
        (await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: kunciKeBytes(public_key),
        }));

      const simpan = await fetch(`${API_BASE_URL}/push/subscribe`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authStore.token}`,
        },
        body: JSON.stringify(sub.toJSON()),
      });

      webpushAktif.value = simpan.ok;
      return simpan.ok;
    } catch (e) {
      console.error("[TelemetryStore] Gagal mendaftar Web Push", e);
      return false;
    }
  };

  const cekAmbang = (nodeId: string, feed: Record<string, any>) => {
    const daftar = sensorsByNode.value[nodeId];
    if (!daftar?.length) return;

    for (const s of daftar) {
      if (!s.enabled) continue;
      if (s.min_threshold == null && s.max_threshold == null) continue;

      const mentah = feed[`${s.channel_id}_${s.thingspeak_field}`];
      // null berarti sensornya gagal dibaca, bukan nilainya nol. Jangan
      // dibandingkan dengan ambang -- itu akan memicu alert palsu.
      if (mentah == null) continue;
      const nilai = Number(mentah);
      if (!Number.isFinite(nilai)) continue;

      const terlaluTinggi = s.max_threshold != null && nilai > s.max_threshold;
      const terlaluRendah = s.min_threshold != null && nilai < s.min_threshold;
      const diLuar = terlaluTinggi || terlaluRendah;
      const sebelumnya = statusAlert[s.id] || false;

      if (diLuar && !sebelumnya) {
        const batas = terlaluTinggi ? s.max_threshold : s.min_threshold;
        tampilkanNotif(
          `${s.name} ${terlaluTinggi ? "terlalu tinggi" : "terlalu rendah"}`,
          `${nilai} ${s.unit} (batas ${batas} ${s.unit})`,
          `sensor-${s.id}`,
        );
      } else if (!diLuar && sebelumnya) {
        tampilkanNotif(
          `${s.name} kembali normal`,
          `${nilai} ${s.unit}`,
          `sensor-${s.id}`,
        );
      }

      statusAlert[s.id] = diLuar;
    }
  };

  let ws: WebSocket | null = null;
  let reconnectTimer: any = null;

  const connectWebSocket = () => {
    if (ws || !authStore.token) return;

    try {
      const url = new URL(WS_URL);
      url.searchParams.append("token", authStore.token);

      ws = new WebSocket(url.toString());

      ws.onopen = () => {
        isConnected.value = true;
        console.log("[TelemetryStore] WebSocket connected");
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg?.event === "sensor_update" && msg.node_id) {
            const nodeId = msg.node_id;
            const current = telemetryHistory.value[nodeId]
              ? [...telemetryHistory.value[nodeId]]
              : [];
            const previousFeed = current[0] || {};

            // Merge multi-channel fields so fields from channel 1 and channel 2 never erase each other
            const newFeed = {
              ...previousFeed,
              ...msg.data,
              created_at: msg.created_at || new Date().toISOString(),
            };

            current.unshift(newFeed);
            // Retain live window stream (up to 500 recent points)
            telemetryHistory.value[nodeId] = current.slice(0, 500);

            cekAmbang(nodeId, newFeed);
          }
        } catch (e) {
          console.error("[TelemetryStore] Failed to parse message", e);
        }
      };

      ws.onclose = () => {
        isConnected.value = false;
        ws = null;
        if (authStore.isAuthenticated()) {
          reconnectTimer = setTimeout(connectWebSocket, 3000);
        }
      };

      ws.onerror = (err) => {
        console.error("[TelemetryStore] WebSocket error", err);
      };
    } catch (err) {
      console.error("[TelemetryStore] Failed to init WebSocket", err);
    }
  };

  const disconnectWebSocket = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (ws) {
      ws.close();
      ws = null;
    }
    isConnected.value = false;
  };

  const fetchSensors = async (nodeId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/sensors/`, {
        headers: { Authorization: `Bearer ${authStore.token}` },
      });
      if (res.ok) {
        const data = await res.json();
        sensorsByNode.value[nodeId] = data;
        return data;
      }
    } catch (e) {
      console.error(
        "[TelemetryStore] Failed to fetch sensors from PostgreSQL",
        e,
      );
    }
    return [];
  };

  const fetchHistory = async (nodeId: string, options?: HistoryOptions) => {
    const isLiveWindow =
      !options?.range || options.range === "1d" || options.range === "1h";
    const isCustom = !!(options?.start || options?.end);
    const force = options?.force ?? false;

    // If live window and not forced and already in store, return cached live data
    if (
      isLiveWindow &&
      !isCustom &&
      !force &&
      telemetryHistory.value[nodeId]?.length > 0
    ) {
      return telemetryHistory.value[nodeId];
    }

    const params = new URLSearchParams();
    if (options?.range) params.append("range", options.range);
    else if (!isCustom) params.append("range", "1d");

    if (options?.start) params.append("start", options.start);
    if (options?.end) params.append("end", options.end);
    if (options?.results) params.append("results", String(options.results));
    if (options?.average) params.append("average", String(options.average));

    if (!isLiveWindow || isCustom) {
      isArchiveLoading.value[nodeId] = true;
    }

    try {
      const res = await fetch(
        `${API_BASE_URL}/nodes/${nodeId}/telemetry/history?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${authStore.token}` },
        },
      );
      if (res.ok) {
        const data = await res.json();
        if (data.feeds && Array.isArray(data.feeds)) {
          if (isLiveWindow && !isCustom) {
            telemetryHistory.value[nodeId] = [...data.feeds].reverse();
            return telemetryHistory.value[nodeId];
          } else {
            archiveHistory.value[nodeId] = data.feeds;
            return archiveHistory.value[nodeId];
          }
        }
      }
    } catch (e) {
      console.error("[TelemetryStore] Failed to fetch history", e);
    } finally {
      if (!isLiveWindow || isCustom) {
        isArchiveLoading.value[nodeId] = false;
      }
    }

    return isLiveWindow && !isCustom
      ? telemetryHistory.value[nodeId] || []
      : archiveHistory.value[nodeId] || [];
  };

  const getLatest = (nodeId: string) => {
    return telemetryHistory.value[nodeId]?.[0] ?? null;
  };

  const getChartData = (nodeId: string, isArchive = false) => {
    if (isArchive) {
      return archiveHistory.value[nodeId] || [];
    }
    return [...(telemetryHistory.value[nodeId] || [])].reverse();
  };

  return {
    telemetryHistory,
    archiveHistory,
    isArchiveLoading,
    isConnected,
    connectWebSocket,
    disconnectWebSocket,
    fetchSensors,
    fetchHistory,
    getLatest,
    getChartData,
    notifAktif,
    mintaIzinNotif,
    webpushAktif,
    cekWebpush,
    daftarWebpush,
  };
});
