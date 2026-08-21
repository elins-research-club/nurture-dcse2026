# 🌿 G-Connect — Smart Farming IoT Platform

Platform monitoring dan manajemen perangkat IoT untuk pertanian cerdas (*smart farming*). G-Connect menghubungkan sensor di lapangan ke dashboard real-time berbasis web

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
                       │ polling setiap 15 detik
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND — FastAPI (Python)                     │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐     │
│  │ REST API    │  │  WebSocket   │  │  Background Poller  │     │
│  │ /api/v1/..  │  │  /api/v1/ws  │  │  thingspeak_poller  │     │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘     │
│         │                │                     │                │
│         └────────────────┴─────────────────────┘                │
│                          │                                      │
│  ┌────────────┐          │  ┌──────────────────────────┐        │
│  │ PostgreSQL │◄─────────┘  │  *Telegram Bot API       │        │
│  │  Database  │             │  (alert offline/online)  │        │
│  └────────────┘             └──────────────────────────┘        │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP + WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FRONTEND — Vue 3 + TypeScript                   │
│                                                                 │
│  📊 Dashboard   🖥️ Nodes   🔔 Alerts   ⚙️ Settings            │
│                                                                 │
│  Data real-time via WebSocket, grafik historis via REST API     │
└─────────────────────────────────────────────────────────────────┘
```

### Alur Data Real-time

```
Sensor → ThingSpeak → [Poller setiap 15s] → WebSocket Broadcast → Dashboard
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
│   │   ├── views/            # Halaman (Dashboard, Nodes, Alerts, Settings)
│   │   ├── components/       # Komponen UI (Sidebar, Chart, dll)
│   │   ├── composables/      # TanStack Query hooks
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
| **Frontend** | Vue 3, TypeScript, Vite, TailwindCSS v4, Pinia, TanStack Query, Lucide Icons |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy (async), Pydantic v2, Uvicorn |
| **Database** | PostgreSQL 15 |
| **IoT Data Source** | ThingSpeak API |
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

## Metode 3: Full Lokal Tanpa Docker 🖥️

Untuk metode ini kamu membutuhkan **PostgreSQL terinstall langsung** di laptop.

### Prasyarat Tambahan
- [PostgreSQL 15+](https://www.postgresql.org/download/) terinstall dan berjalan

### Langkah 1 — Siapkan Database PostgreSQL

Buka `psql` atau pgAdmin, lalu jalankan:
```sql
CREATE DATABASE gconnect;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE gconnect TO postgres;
```

### Langkah 2 — Setup Backend

Sama seperti **Metode 2 Langkah 2**, tapi gunakan port standar `5432`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gconnect
```

Lanjutkan install dan jalankan backend seperti Metode 2.

### Langkah 3 — Setup Frontend

Sama persis dengan **Metode 2 Langkah 3**.

---

## 🔌 Menghubungkan Node ke ThingSpeak

Setelah aplikasi berjalan, tambahkan node baru melalui Swagger (`/docs`) atau UI:

**1. Daftarkan Node**
```http
POST /api/v1/nodes/
{
  "node_id": "NODE-01",
  "name": "Kebun Blok A",
  "location": "Sawah Utara"
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

Setelah itu, poller otomatis akan mulai mengambil data dari ThingSpeak dan menyiarkannya ke dashboard secara real-time.

---

## ⚙️ Cara Kerja Status Aktuator (Bitmask)

Sistem menggunakan teknik **Bitmask** untuk menghemat penggunaan *field* di ThingSpeak saat mengirimkan status hidup/mati dari beberapa aktuator sekaligus (Pompa, Kipas, dsb) dalam 1 angka (Integer). 

1. Di database, buat satu sensor dengan nama **"Status aktuator"**.
2. Angka dari *field* ThingSpeak tersebut akan diubah ke biner di frontend.
3. Misalnya, nilai `5` (Biner: `101`) berarti:
   - Aktuator 1 (Bit 1 = $2^0$) -> **ON**
   - Aktuator 2 (Bit 2 = $2^1$) -> **OFF**
   - Aktuator 3 (Bit 3 = $2^2$) -> **ON**

---

## 📡 API Reference

Dokumentasi lengkap tersedia di: **http://localhost:8000/docs**

| Endpoint | Deskripsi |
|---|---|
| `POST /api/v1/auth/login` | Login dan dapatkan JWT token |
| `GET /api/v1/nodes/` | Daftar semua node |
| `POST /api/v1/nodes/` | Tambah node baru |
| `GET /api/v1/nodes/{id}/telemetry/latest` | Data sensor terbaru dari ThingSpeak |
| `GET /api/v1/nodes/{id}/telemetry/history` | Data historis dengan filter waktu |
| `GET /api/v1/event-logs/` | Riwayat event (online/offline log) |
| `GET /api/v1/system/config` | Ambil konfigurasi global sistem |
| `PUT /api/v1/system/config` | Update konfigurasi global sistem |
| `WS /ws/{channel}` | WebSocket stream data real-time (contoh: /ws/dashboard) |

### Query Parameter `/telemetry/history`
| Parameter | Contoh | Keterangan |
|---|---|---|
| `range` | `1h`, `1d`, `1w` | Shortcut preset rentang waktu |
| `start` | `2026-08-01T00:00:00` | Awal rentang (ISO 8601) |
| `end` | `2026-08-18T23:59:59` | Akhir rentang (ISO 8601) |
| `results` | `500` | Jumlah data (max 8000) |

---

## 👥 Tim

**G-Connect Smart Farming Platform**  
Universitas Gadjah Mada — Pengabdian Masyarakat Lab ELINS

| Peran | Nama |
|---|---|
| 💻 Software Developer | Hanif |
| 👥 Anggota Tim | Donny |
| 👥 Anggota Tim | Sulthon |
