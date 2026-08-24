# 🌿 G-Connect — Smart Farming IoT Platform

Platform monitoring dan manajemen perangkat IoT untuk pertanian cerdas (smart farming). G-Connect menghubungkan sensor dan aktuator di lapangan dengan dashboard web real-time untuk memantau kondisi lahan, status perangkat, serta memberikan peringatan (alert) terhadap kondisi yang memerlukan perhatian.

---

## 📐 Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                        LAPANGAN / FIELD                         │
│                                                                 │
│   [Sensor Node 1]  [Sensor Node 2]  [Sensor Node N]             │
│   (suhu, kelembapan, soil moisture, dll)                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │ kirim data (HTTP/MQTT)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     THINGSPEAK (Cloud)                          │
│              Penerima & penyimpan data sensor                   │
│         api.thingspeak.com/channels/{id}/feeds.json             │
└──────────────────────┬──────────────────────────────────────────┘
                       │ MQTT Push (mqtt3.thingspeak.com:1883)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND — FastAPI (Python)                     │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐     │
│  │ REST API    │  │  WebSocket   │  │  MQTT Subscriber    │     │
│  │ /api/v1/..  │  │  /ws/..      │  │  thingspeak_mqtt    │     │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘     │
│         │                │                     │                │
│         └────────────────┴─────────────────────┘                │
│                          │                                      │
│  ┌────────────┐          │  ┌──────────────────────────┐        │
│  │ PostgreSQL │◄─────────┘  │  *Telegram Bot API       │        │
│  │  Database  │             │  (alert offline/online)  │        │
│  └────────────┘             └──────────────────────────┘        │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP + WebSocket (Real-Time)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FRONTEND — Vue 3 + TypeScript                   │
│                                                                 │
│  📊 Dashboard   🖥️ Nodes   🗺️ Map   🔔 Alerts   ⚙️ Settings     │
│                                                                 │
│  Data real-time via WebSocket, GIS Satellite via Leaflet,       │
│  grafik historis via REST API & Pinia Global Store              │
└─────────────────────────────────────────────────────────────────┘
```

### Alur Data Real-time (Event-Driven / Push)

```
Sensor → ThingSpeak → [MQTT Push <1s] → Backend Subscriber → WebSocket Broadcast → Frontend (Pinia Store)
```

### Alur Alert Offline

```
Poller → last_seen > 15 menit → EventLog (DB) + Telegram Notification
```

---

## 🗂️ Struktur Proyek

```
G-CONNECT2026/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── core/             # Config, Database, Security
│   │   ├── models/           # SQLAlchemy ORM Models
│   │   ├── schemas/          # Pydantic Schemas
│   │   ├── repositories/     # Database Query Logic
│   │   ├── routers/          # API Endpoints
│   │   ├── services/         # Business Logic (Poller, Telegram, WebSocket)
│   │   └── main.py           # App Entry Point
│   ├── migrations/           # Alembic Database Migrations
│   ├── .env                  # Environment variables (lokal)
│   ├── .env.example          # Template environment variables
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Vue 3 + TypeScript + Vite
│   ├── src/
│   │   ├── views/            # Halaman (Dashboard, Nodes, Map, Alerts, Settings)
│   │   ├── components/       # Komponen UI (Sidebar, Chart, Map, dll)
│   │   ├── composables/      # TanStack Query & WebSocket hooks
│   │   ├── stores/           # Pinia state management
│   │   └── router/           # Vue Router
│   ├── .env.example
│   └── Dockerfile
├── scripts/                  # Helper scripts
├── docker-compose.yml        # Orchestration (Full Docker / DB only)
├── .env.example              # Template environment root
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Teknologi |
|---|---|
| **Frontend** | Vue 3, TypeScript, Vite, TailwindCSS v4, Apache ECharts (`vue-echarts`), Leaflet, Pinia, TanStack Query, Lucide Icons |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy (async), Pydantic v2, Uvicorn |
| **Database** | PostgreSQL 15 |
| **IoT Data Source** | ThingSpeak API (Dual-Channel Merging + Forward-Fill + Aggregation) |
| **Peta Satelit** | Leaflet + Google Maps Satellite Hybrid |
| **Notifikasi** | Telegram Bot API |
| **Containerization** | Docker, Docker Compose |

---

## 🚀 Cara Instalasi

### Prasyarat

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (untuk metode Docker)
- [Python 3.11+](https://www.python.org/) (untuk metode Lokal)
- [Node.js 20+](https://nodejs.org/) (untuk metode Lokal)

---

## Metode 1: Full Docker (Paling Mudah) 🐳

Semua komponen (Frontend, Backend, Database) berjalan di dalam Docker.

**1. Clone repository**
```bash
git clone <url-repo>
cd G-CONNECT2026
```

**2. Buat file environment**
```bash
cp .env.example .env
```

Edit `.env` sesuai kebutuhan (opsional untuk pengembangan lokal):
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=gconnect
SECRET_KEY=ganti-dengan-string-random-panjang-minimal-32-karakter

# Opsional — untuk notifikasi Telegram
TELEGRAM_BOT_TOKEN=token_dari_botfather
TELEGRAM_CHAT_ID=id_chat_kamu
```

**3. Build dan jalankan semua service**
```bash
docker-compose up -d --build
```

**4. Buat akun admin pertama**
```bash
docker exec -it gconnect_backend python create_admin.py
```

**5. Akses aplikasi**
| Service | URL |
|---|---|
| 🖥️ Frontend | http://localhost:5173 |
| ⚙️ Backend API | http://localhost:8000 |
| 📄 Swagger Docs | http://localhost:8000/docs |
| 🗄️ Adminer (DB) | http://localhost:8080 |

**Perintah berguna:**
```bash
# Lihat log backend secara live
docker logs -f gconnect_backend

# Stop semua service
docker-compose down

# Stop dan hapus semua data (HATI-HATI!)
docker-compose down -v
```

---

## Metode 2: Hybrid — Hanya Database di Docker (Untuk Development) ⚡

Cara ini yang paling nyaman untuk *development* karena backend dan frontend mendukung *hot-reload*.

> Database berjalan di Docker, Backend dan Frontend berjalan langsung di lokal.

### Langkah 1 — Jalankan Database PostgreSQL via Docker

```bash
docker-compose up -d postgres
```

Database akan berjalan di port **5433** (bukan 5432 standar, untuk menghindari konflik jika sudah ada PostgreSQL terpasang di laptop).

---

### Langkah 2 — Setup Backend

**Masuk ke folder backend:**
```bash
cd backend
```

**Buat virtual environment Python:**
```bash
python -m venv venv
```

**Aktifkan virtual environment:**
```bash
# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Buat file environment:**
```bash
cp .env.example .env
```

Edit `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/gconnect
SECRET_KEY=ganti-dengan-string-random-panjang-minimal-32-karakter

# Opsional — untuk notifikasi Telegram
TELEGRAM_BOT_TOKEN=token_dari_botfather
TELEGRAM_CHAT_ID=id_chat_kamu

# Opsional — konfigurasi lainnya
OFFLINE_THRESHOLD_MINUTES=15
THINGSPEAK_POLL_INTERVAL=15
```

**Buat akun admin pertama:**
```bash
python create_admin.py
```

**Jalankan backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

Backend siap di: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

---

### Langkah 3 — Setup Frontend

Buka terminal baru, masuk ke folder frontend:
```bash
cd frontend
```

**Install dependencies:**
```bash
npm install
```

**Buat file environment:**
```bash
cp .env.example .env
```

Edit `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

**Jalankan frontend:**
```bash
npm run dev
```

Frontend siap di: http://localhost:5173

---

## 🔌 Menghubungkan Node ke ThingSpeak

Setelah aplikasi berjalan, daftarkan node dan sensor melalui UI atau Swagger (`/docs`):

**1. Daftarkan Node (Beserta Koordinat GPS)**
```http
POST /api/v1/nodes/
{
  "node_id": "NODE-01",
  "name": "Kebun Blok A",
  "location": "Sawah Utara",
  "latitude": -7.7679423,
  "longitude": 110.3765989
}
```

**2. Masukkan Konfigurasi ThingSpeak**
```http
POST /api/v1/nodes/NODE-01/channel/
{
  "channel_id": "123456",
  "read_api_key": "XXXXXXXXXXXXXX",
  "write_api_key": "YYYYYYYYYYYYYY"
}
```

**3. Mapping Sensor ke Field ThingSpeak**
```http
POST /api/v1/nodes/NODE-01/sensors/
{
  "type": "temperature",
  "name": "Sensor Suhu",
  "unit": "°C",
  "thingspeak_field": "field1"
}
```

---

## 🌟 Fitur Unggulan Sistem

### 📈 Sistem Grafik Telemetri Cerdas & Agregasi
* **Category Pills Navigation:** Pemisahan visualisasi ke dalam 4 kategori parameter (**Unsur Hara NPK**, **Kondisi Tanah**, **Lingkungan & Iklim**, dan **Semua Sensor**) agar skala sumbu Y presisi dan grafik tidak saling tumpuk.
* **Live Window Stream (24 Jam):** Mode real-time streaming di mana data terbaru dari WebSocket secara dinamis ditambahkan di ujung kanan grafik.
* **Historical Archive Mode:** Menampilkan data historis rentang panjang (1 Minggu, 1 Bulan, atau Tanggal Kustom) secara statis tanpa terganggu oleh WebSocket.
* **Agregasi Otomatis ThingSpeak (`&average=60`):** Meringkas data 30 hari menjadi resolusi rata-rata per jam (~720 titik alih-alih 86.000 titik mentah) sehingga rendering grafik tetap sangat cepat dan ringan.
* **Interactive DataZoom & Slider:** Pengguna dapat melakukan zoom in / out dan menggeser timeline grafik dengan mulus.

### 🗺️ Peta Satelit Interaktif GIS (`/map`)
* **Google Maps Hybrid Tiles:** Citra satelit resolusi tinggi lengkap dengan label jalan & tempat.
* **Pinpoint & Drag-and-Drop:** Atur lokasi node via input manual koordinat atau geser marker langsung di peta.
* **Live Teleport:** Klik nama node pada floating sidebar untuk terbang langsung (*flyTo*) ke titik perangkat.
* **Real-time NPK Pop-up:** Klik marker untuk melihat data **Nitrogen (N), Fosfor (P), Kalium (K)** dan status online/offline yang ter-update instan via WebSocket.

### ⚙️ Multi-Channel Merge & Forward-Fill Telemetri
* **Dual-Channel ThingSpeak Sync:** Menggabungkan data dari 2 channel ThingSpeak berbeda dalam 1 node dengan pembulatan waktu (15 detik).
* **Forward-Fill Algoritma:** Mengisi kekosongan field akibat keterlambatan request antar-channel dengan nilai valid terakhir (*last known value*).
* **In-Memory Caching (Backend):** Cache telemetri historis dengan TTL dinamis (`telemetry_cache_interval`) untuk efisiensi kuota API ThingSpeak.

### 🔌 Status Aktuator (Bitmask)
Sistem menggunakan teknik **Bitmask** untuk menghemat field ThingSpeak (1 angka integer untuk multi-aktuator):
* Nilai `5` (Biner: `101`):
  * Aktuator 1 ($2^0$) $\rightarrow$ **ON**
  * Aktuator 2 ($2^1$) $\rightarrow$ **OFF**
  * Aktuator 3 ($2^2$) $\rightarrow$ **ON**

---

## 📡 API Reference

Dokumentasi interaktif lengkap: **http://localhost:8000/docs**

| Endpoint | Method | Deskripsi |
|---|---|---|
| `/api/v1/auth/login` | `POST` | Autentikasi & perolehan JWT token |
| `/api/v1/nodes/` | `GET`, `POST` | List semua node & tambah node baru |
| `/api/v1/nodes/{id}` | `GET`, `PUT`, `DELETE` | Detail node, update koordinat/nama, hapus node |
| `/api/v1/nodes/{id}/sensors/` | `GET`, `POST` | Mapping daftar sensor pada node |
| `/api/v1/nodes/{id}/telemetry/latest` | `GET` | Data sensor terbaru |
| `/api/v1/nodes/{id}/telemetry/history` | `GET` | Data historis dengan filter rentang waktu |
| `/api/v1/event-logs/` | `GET` | Riwayat log event (online/offline) |
| `/api/v1/system/config` | `GET`, `PUT` | Baca & perbarui konfigurasi sistem/cache |
| `/ws/{channel}` | `WS` | WebSocket stream data real-time (`/ws/dashboard`) |

### Query Parameter `/telemetry/history`
| Parameter | Contoh | Keterangan |
|---|---|---|
| `range` | `1h`, `1d`, `1w`, `1M` | Preset cepat rentang waktu (1M = 30 hari) |
| `start` / `end` | `2026-08-01T00:00:00` | Rentang waktu kustom (ISO 8601) |
| `results` | `500` | Batas jumlah feed (max 8000) |
| `average` | `10`, `15`, `60` | Agregasi rata-rata per N menit (ThingSpeak) |

---

## 👥 Tim Pengembang

**G-Connect Smart Farming Platform**  
Universitas Gadjah Mada — Pengabdian Masyarakat Lab ELINS

| Peran | Nama |
|---|---|
| 💻 Software Developer | Hanif Elins 23 |
| 👥 Anggota Tim | Donny Elins 25 |
| 👥 Anggota Tim | Sulthon Elins 25 |

