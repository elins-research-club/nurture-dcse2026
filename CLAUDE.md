# G-Connect — Catatan untuk Claude Code

Proyek monitoring IoT pertanian: 2x ESP32-S3 (NODE-01 "Kebun Blok A", NODE-02
"Kebun Blok B") → ThingSpeak → backend FastAPI (`backend/`) → frontend Vue 3
(`frontend/`). Tiap node punya 2 channel ThingSpeak: **Utama** (NPK, pH, EC,
iklim) dan **Pendukung** (suhu tanah, baterai, panel, aktuator).

Sumber kebenaran untuk field-field di bawah ini adalah halaman "Channel
Settings" ThingSpeak masing-masing channel, bukan tebakan dari kode. Kalau
field di ThingSpeak berubah lagi, mapping di bawah dan template seed di
`backend/app/routers/channels.py` (`TEMPLATE_UTAMA_NODE1/2`,
`TEMPLATE_PENDUKUNG_NODE1/2`) harus diperbarui bersamaan, lalu jalankan
`python -m scripts.remap_sensors` supaya baris sensor yang sudah ada di
database ikut disesuaikan (template cuma berlaku untuk channel baru).

## Channel map (revisi INA226, 2026-09)

Node 1 dan Node 2 **tidak** berbagi mapping field yang identik sejak revisi
ini — field6 ke atas artinya beda posisi antar node, bukan cuma beda label.

### NODE 1 — Utama (channel ID 3461921)
| Field | Nama | Satuan | `type` sensor |
|---|---|---|---|
| field1 | Nitrogen | mg/kg | `npk_n` |
| field2 | Fosfor | mg/kg | `npk_p` |
| field3 | Kalium | mg/kg | `npk_k` |
| field4 | pH Tanah | pH | `soil_ph` |
| field5 | EC Tanah | uS/cm | `soil_ec` |
| field6 | Rata-rata Kelembapan Tanah | % | `soil_probe` |
| field7 | Suhu Luar Rata-Rata | C | `air_temp` |
| field8 | Lembab Luar Rata-Rata | % | `air_humidity` |

### NODE 1 — Pendukung (channel ID 3461926)
| Field | Nama | Satuan | `type` sensor |
|---|---|---|---|
| field1 | Suhu Tanah | C | `soil_temp` |
| field2 | Tegangan Baterai | V | `batt_volt` |
| field3 | Tegangan Load | V | `batt_volt` |
| field4 | Arus Baterai | A | `current` |
| field5 | Arus Load | A | `current` |
| field6 | Suhu Dalam Panel | C | `box_temp` |
| field7 | Status Aktuator | — | `actuator` |
| field8 | Konsumsi Daya Sistem | W | `power` |

### NODE 2 — Utama (channel ID 3461925)
| Field | Nama | Satuan | `type` sensor |
|---|---|---|---|
| field1 | Nitrogen | mg/kg | `npk_n` |
| field2 | Fosfor | mg/kg | `npk_p` |
| field3 | Kalium | mg/kg | `npk_k` |
| field4 | pH Tanah | pH | `soil_ph` |
| field5 | EC Tanah | uS/cm | `soil_ec` |
| field6 | Suhu Luar Rata-Rata | C | `air_temp` |
| field7 | Lembab Luar Rata-Rata | % | `air_humidity` |
| field8 | Daya Beban Aktual | W | `power` |

### NODE 2 — Pendukung (channel ID 3461928)
| Field | Nama | Satuan | `type` sensor |
|---|---|---|---|
| field1 | Suhu Tanah | C | `soil_temp` |
| field2 | Kelembapan Probe NPK | % | `probe_moist` |
| field3 | Tegangan Baterai | V | `batt_volt` |
| field4 | Tegangan Load | V | `batt_volt` |
| field5 | Arus Baterai | A | `current` |
| field6 | Arus Load | A | `current` |
| field7 | Suhu Dalam Panel | C | `box_temp` |
| field8 | Status Aktuator | — | `actuator` |

## Hal-hal yang tidak jelas dari tabel di atas

- **Firmware menghilangkan field saat pembacaan gagal** (tidak pernah
  mengirim 0). Ingest wajib memperlakukan field yang tidak ada sebagai "tidak
  ada pembacaan", bukan nol — lihat `field_decoder.extract_channel_fields`.
- **Status Aktuator** adalah bitmask 4-bit (0-15): bit0 kipas, bit1 lampu,
  bit2 valve, bit3 valve_timeout. Node 2 tidak punya valve (bit2/bit3 selalu
  mati) — `field_decoder.has_valve(layout)`. **Posisi field-nya beda per
  node**: field7 di Node 1, field8 di Node 2 — `field_decoder.actuator_field(layout)`.
  Jangan diberi ambang batas: angkanya bitmask, bukan besaran yang punya urutan.
- **Tegangan/Arus Baterai vs Load**: field-nya beda posisi per node (lihat
  tabel), jadi kode yang perlu membedakan "baterai" dari "load" harus
  mencocokkan lewat **nama sensor**, bukan nomor field —
  lihat `_peran_sensor()` di `backend/app/routers/telemetry.py` dan
  `sensorPeran()` di `frontend/src/components/dashboard/NodeDashboard.vue`.
- **Konsumsi Daya Sistem / Daya Beban Aktual** (field8) adalah pengukuran daya
  langsung dari hardware, dan **itulah angka daya yang dipakai** portlet
  "Daya & Baterai" di dashboard. Daya tidak pernah lagi diturunkan sendiri
  dari V x A — perhitungan itu sudah dihapus dari backend (`power_metrics`
  tidak punya `daya_in`/`daya_out`) maupun frontend. Sensornya dicari lewat
  `type == 'power'` karena namanya berbeda antar node, dan tiap node cuma
  punya satu.
- **`nodes.field_layout`**: kolom di database bernilai `'node1_packed'` atau
  `'node2_plain'`. Namanya sisa dari revisi sebelum ini, waktu Node 1 betulan
  memampatkan dua arus jadi satu field (field5). Sejak revisi INA226, Node 1
  **tidak lagi memampatkan apa pun** — nilainya tetap dipakai sebagai
  identitas "Node 1 vs Node 2" (field7 aktuator, ada valve, dst.) supaya baris
  database yang sudah ada tidak perlu migrasi ulang.
- **Data historis dari sebelum revisi ini** (Node 1) masih dalam format lama
  (arus dipampatkan di field5). Backend tidak lagi membongkarnya — rentang
  waktu yang mencakup tanggal revisi bisa menampilkan arus Node 1 yang tidak
  masuk akal untuk titik data lama. Ini keterbatasan yang disengaja.
- **`backend/scripts/remap_sensors.py`**: jalankan setelah mengubah template
  di `channels.py`. `--dry-run` dulu untuk melihat rencana (buat/ubah/hapus)
  sebelum benar-benar menulis ke database.
- **`dummy.py`** (root repo): simulator lokal yang menulis payload dummy ke
  keempat channel ThingSpeak di atas, dipakai untuk menguji backend/frontend
  tanpa hardware ESP32 asli. Ikuti mapping di atas kalau field berubah lagi.
