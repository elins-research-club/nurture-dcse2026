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

export interface SensorMetricSummary {
  id: string;
  name: string;
  type: string;
  unit: string;
  thingspeak_field: string;
  channel_id?: string | null;
  field_key: string;
  current_value?: number | null;
  min_recorded?: number | null;
  max_recorded?: number | null;
  min_threshold?: number | null;
  max_threshold?: number | null;
  status?: string | null;
}

export interface PowerMetrics {
  tegangan_in?: number | null;
  tegangan_out?: number | null;
  arus_in?: number | null;
  arus_out?: number | null;
  daya_in?: number | null;
  daya_out?: number | null;
  satuan?: { tegangan: string; arus: string; daya: string };
  catatan?: string;
}

export interface DashboardSummaryResponse {
  node_id: string;
  node_name?: string | null;
  last_seen?: string | null;
  is_active: boolean;
  sensors: SensorMetricSummary[];
  npk_sensors: SensorMetricSummary[];
  soil_probes: SensorMetricSummary[];
  soil_metrics: {
    ph?: SensorMetricSummary | null;
    soil_temp?: SensorMetricSummary | null;
    ec?: SensorMetricSummary | null;
    avg_moisture?: SensorMetricSummary | null;
  };
  iot_metrics: {
    enclosure_temp?: SensorMetricSummary | null;
    air_temp?: SensorMetricSummary | null;
    humidity?: SensorMetricSummary | null;
    modbus?: SensorMetricSummary | null;
  };
  power_metrics?: PowerMetrics;
  soil_health?: any | null;
  aktuator?: Record<string, boolean> | null;
}

export const useTelemetryStore = defineStore("telemetry", () => {
  const authStore = useAuthStore();

  // State: Structured Dashboard Summaries directly from PostgreSQL Backend API
  const dashboardSummaries = ref<Record<string, DashboardSummaryResponse>>({});
  const isDashboardLoading = ref<Record<string, boolean>>({});

  // State: NodeId -> Live telemetry feeds (index 0 is newest, updated by WS)
  const telemetryHistory = ref<Record<string, any[]>>({});
  // State: NodeId -> Static Archive telemetry feeds (oldest first, for historical ranges 1w, 1M, custom)
  const archiveHistory = ref<Record<string, any[]>>({});
  const isArchiveLoading = ref<Record<string, boolean>>({});
  const isConnected = ref(false);

  // Sensor per node, disimpan supaya handler WebSocket bisa membaca ambangnya
  // tanpa menembak API tiap kali ada pesan masuk.
  const sensorsByNode = ref<Record<string, any[]>>({});

  // Status aktuator sudah didekode backend (services/aktuator.py), yang tahu
  // maskanya 4 bit dan tahu node mana yang punya valve. Dulu nilai ini dibuang
  // di sini lalu didekode ulang di NodeDashboard dengan batas 0-7, sehingga
  // valve_timeout (bit3) menghapus SELURUH pembacaan aktuator.
  const aktuatorByNode = ref<Record<string, any>>({});

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
    try {
      const reg = await navigator.serviceWorker.getRegistration("/sw.js");
      const sub = reg ? await reg.pushManager.getSubscription() : null;
      if (!sub) {
        webpushAktif.value = false;
        return false;
      }
      // Jika browser memiliki subscription, sinkronkan ke backend agar tidak out-of-sync
      if (authStore.token) {
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
      }
      webpushAktif.value = true;
      return true;
    } catch {
      webpushAktif.value = false;
      return false;
    }
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

  const batalWebpush = async () => {
    try {
      if (!("serviceWorker" in navigator)) {
        webpushAktif.value = false;
        return true;
      }

      let endpoint = "";
      try {
        const regs = await navigator.serviceWorker.getRegistrations();
        for (const reg of regs) {
          const sub = await reg.pushManager.getSubscription();
          if (sub) {
            endpoint = sub.endpoint;
            await sub.unsubscribe().catch(() => {});
          }
        }
      } catch (e) {
        console.warn("[TelemetryStore] Warning saat membaca push subscription:", e);
      }

      if (authStore.token && endpoint) {
        try {
          await fetch(`${API_BASE_URL}/push/unsubscribe`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${authStore.token}`,
            },
            body: JSON.stringify({ endpoint }),
          });
        } catch (e) {
          console.warn("[TelemetryStore] Gagal request hapus ke backend:", e);
        }
      }

      webpushAktif.value = false;
      return true;
    } catch (e) {
      console.error("[TelemetryStore] Gagal membatalkan Web Push", e);
      webpushAktif.value = false;
      return true;
    }
  };

  // Ambang OPERATOR dari database. Bukan kelas pustaka -- vonis terhadap
  // standar terbit datang dari backend lewat dashboardSummaries.soil_health.
  const cekAmbang = (nodeId: string, feed: Record<string, any>) => {
    const daftar = sensorsByNode.value[nodeId];
    if (!daftar?.length) return;
    const namaNode = dashboardSummaries.value[nodeId]?.node_name || nodeId;

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
        let ambangStr = "";
        const u = s.unit || "";
        if (s.min_threshold != null && s.max_threshold != null) {
          ambangStr = `${s.min_threshold} - ${s.max_threshold} ${u}`.trim();
        } else if (s.max_threshold != null) {
          ambangStr = `Maks. ${s.max_threshold} ${u}`.trim();
        } else if (s.min_threshold != null) {
          ambangStr = `Min. ${s.min_threshold} ${u}`.trim();
        }

        const statusKondisi = terlaluTinggi ? "Tinggi" : "Rendah";
        const judul = `⚠️ Peringatan: ${namaNode}`;
        const isi = `${s.name} mencapai ${nilai} ${u} (${statusKondisi} | Ambang batas: ${ambangStr})`.trim();

        tampilkanNotif(judul, isi, `sensor-${s.id}`);
      }

      statusAlert[s.id] = diLuar;
    }
  };

  let ws: WebSocket | null = null;
  let reconnectTimer: any = null;
  let reconnectAttempts = 0;
  const maxReconnectDelay = 30000;

  // Batching & RAF Throttling for Realtime WebSocket Telemetry Stream
  let pendingFeeds: Record<string, any> = {};
  let rafId: number | null = null;

  const flushPendingUpdates = () => {
    rafId = null;
    for (const [nodeId, newFeed] of Object.entries(pendingFeeds)) {
      const current = telemetryHistory.value[nodeId]
        ? [...telemetryHistory.value[nodeId]]
        : [];
      current.unshift(newFeed);
      // Retain live window stream (up to 500 recent points)
      telemetryHistory.value[nodeId] = current.slice(0, 500);
      cekAmbang(nodeId, newFeed);
    }
    pendingFeeds = {};
  };

  const scheduleReconnect = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    // Exponential backoff: 1.5s, 2.25s, 3.3s, ... max 30s + random jitter 0-500ms
    const delay = Math.min(1500 * Math.pow(1.5, reconnectAttempts), maxReconnectDelay) + Math.random() * 500;
    reconnectAttempts++;
    reconnectTimer = setTimeout(connectWebSocket, delay);
  };

  const connectWebSocket = () => {
    if (ws) return;

    try {
      const url = new URL(WS_URL);
      if (authStore.token) {
        url.searchParams.append("token", authStore.token);
      }

      ws = new WebSocket(url.toString());

      ws.onopen = () => {
        isConnected.value = true;
        reconnectAttempts = 0;
        console.log("[TelemetryStore] WebSocket connected");
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg?.event === "sensor_update" && msg.node_id) {
            const nodeId = msg.node_id;
            const current = telemetryHistory.value[nodeId]
              ? telemetryHistory.value[nodeId]
              : [];
            const previousFeed = pendingFeeds[nodeId] || current[0] || {};

            // Merge multi-channel fields so fields from channel 1 and channel 2 never erase each other
            const newFeed = {
              ...previousFeed,
              ...msg.data,
              created_at: msg.created_at || new Date().toISOString(),
            };

            pendingFeeds[nodeId] = newFeed;

            // Dikirim backend di tiap pesan; sebelumnya diabaikan total.
            if (msg.aktuator !== undefined) {
              aktuatorByNode.value[nodeId] = msg.aktuator;
            }

            // Batch reactive update into next browser animation frame (60 FPS smooth rendering)
            if (!rafId) {
              if (typeof requestAnimationFrame !== "undefined") {
                rafId = requestAnimationFrame(flushPendingUpdates);
              } else {
                flushPendingUpdates();
              }
            }
          }
        } catch (e) {
          console.error("[TelemetryStore] Failed to parse message", e);
        }
      };

      ws.onclose = () => {
        isConnected.value = false;
        ws = null;
        scheduleReconnect();
      };

      ws.onerror = (err) => {
        console.error("[TelemetryStore] WebSocket error", err);
      };
    } catch (err) {
      console.error("[TelemetryStore] Failed to init WebSocket", err);
      scheduleReconnect();
    }
  };

  const disconnectWebSocket = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (rafId && typeof cancelAnimationFrame !== "undefined") {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    if (ws) {
      ws.close();
      ws = null;
    }
    isConnected.value = false;
    pendingFeeds = {};
  };

  const fetchSensors = async (nodeId: string) => {
    try {
      const headers: Record<string, string> = {};
      if (authStore.token) {
        headers["Authorization"] = `Bearer ${authStore.token}`;
      }
      const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/sensors/`, { headers });
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
      const headers: Record<string, string> = {};
      if (authStore.token) {
        headers["Authorization"] = `Bearer ${authStore.token}`;
      }
      const res = await fetch(
        `${API_BASE_URL}/nodes/${nodeId}/telemetry/history?${params.toString()}`,
        { headers },
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

  // --- Centralized Single Source of Truth: Node Online/Offline Status ---
  const OFFLINE_THRESHOLD_MINS = 15;

  const getNodeLastSeen = (nodeId: string, fallbackLastSeen?: string | null): string | undefined => {
    return telemetryHistory.value[nodeId]?.[0]?.created_at || fallbackLastSeen || undefined;
  };

  const isNodeOnline = (nodeId: string, fallbackLastSeen?: string | null): boolean => {
    const lastSeen = getNodeLastSeen(nodeId, fallbackLastSeen);
    if (!lastSeen) return false;
    try {
      const dateStr = String(lastSeen).endsWith("Z") ? String(lastSeen) : String(lastSeen) + "Z";
      const diffMinutes = (Date.now() - new Date(dateStr).getTime()) / (1000 * 60);
      return diffMinutes < OFFLINE_THRESHOLD_MINS;
    } catch {
      return false;
    }
  };

  const getFormattedLastSeen = (nodeId: string, fallbackLastSeen?: string | null): string => {
    const lastSeen = getNodeLastSeen(nodeId, fallbackLastSeen);
    if (!lastSeen) return "--";
    try {
      const dateStr = String(lastSeen).endsWith("Z") ? String(lastSeen) : String(lastSeen) + "Z";
      const d = new Date(dateStr);
      return d.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) + " WIB";
    } catch {
      return "--";
    }
  };

  const fetchDashboardSummary = async (nodeId: string): Promise<DashboardSummaryResponse | null> => {
    isDashboardLoading.value[nodeId] = true;
    try {
      const headers: Record<string, string> = {};
      if (authStore.token) {
        headers["Authorization"] = `Bearer ${authStore.token}`;
      }
      const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/telemetry/dashboard`, { headers });
      if (res.ok) {
        const data: DashboardSummaryResponse = await res.json();
        dashboardSummaries.value[nodeId] = data;
        return data;
      } else {
        console.error(`[TelemetryStore] Failed to fetch dashboard summary, status: ${res.status}`);
      }
    } catch (e) {
      console.error(`[TelemetryStore] Failed to fetch dashboard summary for ${nodeId}`, e);
    } finally {
      isDashboardLoading.value[nodeId] = false;
    }
    return dashboardSummaries.value[nodeId] ?? null;
  };

  return {
    dashboardSummaries,
    isDashboardLoading,
    fetchDashboardSummary,
    telemetryHistory,
    archiveHistory,
    isArchiveLoading,
    isConnected,
    connectWebSocket,
    disconnectWebSocket,
    fetchSensors,
    fetchHistory,
    aktuatorByNode,
    getLatest,
    getChartData,
    getNodeLastSeen,
    isNodeOnline,
    getFormattedLastSeen,
    notifAktif,
    mintaIzinNotif,
    webpushAktif,
    cekWebpush,
    daftarWebpush,
    batalWebpush,
  };
});
