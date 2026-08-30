# 🌿 G-Connect — Smart Farming IoT Platform

Platform monitoring, analitik cerdas, dan manajemen perangkat IoT terintegrasi untuk pertanian presisi (*smart agriculture*). G-Connect menghubungkan stasiun sensor dan aktuator di lapangan dengan antarmuka web modern secara *real-time* untuk memantau kondisi tanah, iklim mikro, status perangkat keras, serta menyediakan laporan agronomi eksekutif dan deteksi anomali otomatis.

---

## 📐 Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            LAPANGAN / AGRICULTURAL FIELD                        │
│                                                                                 │
│   [Sensor Node 1 - Blok A]       [Sensor Node 2 - Blok B]       [Sensor Node N] │
│   (Suhu, Kelembaban Tanah, pH, EC, NPK Soil, Suhu IoT, Status Modbus & Aktuator)│
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Kirim Data Telemetri (HTTP / MQTT)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              THINGSPEAK CLOUD IOT                               │
│                   Penerima & Penyimpan Data Sensor Lapangan                     │
│               Dual-Channel Aggregation & MQTT Push (<1 Detik)                   │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ MQTT Stream & HTTP Fallback
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND — FastAPI (Python 3.11)                       │
│                                                                                 │
│  ┌────────────────┐  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │ RESTful API    │  │ WebSocket Broadcaster│ │ ThingSpeak MQTT & Poller     │  │
│  │ (/api/v1/..)   │  │ (/ws/dashboard)     │  │ (Connection Pooling + Cache) │  │
│  └───────┬────────┘  └──────────┬──────────┘  └──────────────┬───────────────┘  │
│          │                      │                            │                  │
│          └──────────────────────┴────────────────────────────┘                  │
│                                 │                                               │
│  ┌───────────────────────────┐  │  ┌─────────────────────────────────────────┐  │
│  │ PostgreSQL 15 Database    │◄─┘  │ Telegram Bot Alert Notification         │  │
│  │ (Async SQLAlchemy + AsyncPG)    │ (Deteksi Anomali Ambang Batas & Offline)│  │
│  └───────────────────────────┘     └─────────────────────────────────────────┘  │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ REST API + WebSocket (Low-Latency)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND — Vue 3 + TypeScript                          │
│                                                                                 │
│  📊 Dashboard Telemetri   🖥️ Manajemen Alat IoT   🗺️ Peta Satelit Lahan        │
│  📜 Log Aktivitas Event   📄 Ekspor PDF Eksekutif  ⚙️ Pengaturan Sistem         │
│                                                                                 │
│  Antarmuka Reaktif Tailwind CSS v4 & shadcn/ui, Visualisasi ECharts LTTB,       │
│  State Management Pinia, & Komposisi TanStack Query                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### ⚡ Alur Data Real-Time & Event Engine
* **Push Telemetri Lapangan:** Sensor $\rightarrow$ ThingSpeak $\rightarrow$ MQTT Subscriber Backend $\rightarrow$ WebSocket Broadcast $\rightarrow$ Pinia Store Reactive UI.
* **Deteksi Anomali & Peringatan Dini:** Evaluasi otomatis ambang batas agronomi (misal: NPK rendah, tanah kering, suhu IoT tinggi) $\rightarrow$ Penyimpanan `EventLog` $\rightarrow$ Notifikasi Telegram & Badge Visual.

---

## 🗂️ Struktur Proyek

```
GGGCONNECT/
├── backend/                       # Aplikasi FastAPI Core
│   ├── app/
│   │   ├── core/                  # Konfigurasi, Database Async, Autentikasi JWT
│   │   ├── dependencies/          # Injeksi dependensi (Auth, User Session)
│   │   ├── models/                # SQLAlchemy ORM Models (User, Node, Sensor, Channel, EventLog)
│   │   ├── repositories/          # Abstraksi kueri database asinkron
│   │   ├── routers/               # API Endpoints (Auth, Nodes, Sensors, Telemetry, Logs, Push)
│   │   ├── schemas/               # Pydantic v2 validation schemas
│   │   ├── services/              # Logika bisnis (MQTT, Poller, Ring-Buffer, Telegram)
│   │   └── main.py                # Titik masuk aplikasi backend
│   ├── dummy.py                   # Simulator telemetri IoT & pengujian spike anomali
│   ├── create_admin.py            # Skrip pembuat akun administrator awal
│   ├── requirements.txt           # Dependensi pustaka Python
│   └── Dockerfile
├── frontend/                      # Aplikasi Vue 3 + TypeScript + Vite
│   ├── src/
│   │   ├── assets/                # CSS global, Tailwind CSS v4 tokens, font, animasi
│   │   ├── components/            # Komponen modular (UI shadcn, Layout, Dashboard, Modals)
│   │   │   ├── dashboard/         # NodeDashboard, SensorCard, SensorLineChart, ReportModal
│   │   │   ├── layout/            # DashboardLayout, Sidebar, Navbar
│   │   │   └── ui/                # Button, Card, Badge, Dialog, Dropdown, Input, Label
│   │   ├── composables/           # TanStack Query hooks, WebSocket client, Geocoding
│   │   ├── stores/                # Pinia state stores (Auth, Telemetry, UI)
│   │   ├── views/                 # Halaman utama (Login, Dashboard, Nodes, Map, Alerts, Settings)
│   │   ├── router/                # Vue Router navigation guards
│   │   └── main.ts                # Titik masuk aplikasi frontend
│   ├── package.json
│   └── vite.config.ts             # Optimasi Vite, manual vendor chunks, proxy API
├── docker-compose.yml             # Orkestrasi Docker (Full Stack / Database Only)
└── README.md
```

---

## 🛠️ Tech Stack

| Lapisan Sistem | Teknologi & Pustaka Utama |
|---|---|
| **Frontend Framework** | **Vue 3** (Composition API, `<script setup>`), **TypeScript**, **Vite** |
| **Styling & UI Kit** | **Tailwind CSS v4**, **shadcn/ui** (Radix UI Vue primitives), **Lucide Icons** |
| **Data Viz & Charts** | **Apache ECharts** (`vue-echarts`), Algoritma LTTB (*Largest-Triangle-Three-Buckets*) |
| **GIS & Pemetaan** | **Leaflet**, Google Maps Hybrid High-Resolution Satellite Tiles |
| **PDF & Dokumen** | **jsPDF**, **jspdf-autotable**, **html2canvas** (Lazy Loaded) |
| **State & Fetching** | **Pinia**, **TanStack Query (Vue Query)**, Native WebSocket Client |
| **Backend Core** | **FastAPI**, **Python 3.11**, **Uvicorn**, **Pydantic v2** |
| **Database & ORM** | **PostgreSQL 15**, **SQLAlchemy 2.0 (Async)**, **AsyncPG** Driver |
| **IoT Data Pipeline** | **ThingSpeak REST API & MQTT Broker** (Dual-Channel Merging, Forward-Fill) |
| **Notifikasi Lapangan** | **Telegram Bot API**, Web Push (VAPID) |
| **DevOps & Kontainer** | **Docker**, **Docker Compose** |

---

## 🚀 Panduan Instalasi & Menjalankan Sistem

### Prasyarat
* [Git](https://git-scm.com/)
* [Python 3.11+](https://www.python.org/)
* [Node.js 20+](https://nodejs.org/) & `npm`
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (opsional untuk database terisolasi)

---

### Metode 1: Mode Pengembangan Cepat (*Hybrid Development* ⚡)
Database berjalan di Docker, sedangkan Backend dan Frontend berjalan di lingkungan lokal untuk mendukung *instant hot-reload*.

#### 1. Jalankan Database PostgreSQL
```bash
docker-compose up -d postgres
```
> *Database PostgreSQL akan aktif di port `5433` (menghindari bentrok dengan PostgreSQL port default 5432).*

#### 2. Menjalankan Backend FastAPI
Buka terminal pertama:
```bash
cd backend

# Buat & aktifkan virtual environment Python
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependensi
pip install -r requirements.txt

# Buat akun administrator pertama (jika belum ada)
python create_admin.py

# Jalankan server FastAPI dengan auto-reload
uvicorn app.main:app --reload --port 8000
```
* Backend API siap di: `http://localhost:8000`
* Swagger Interactive Docs: `http://localhost:8000/docs`

#### 3. Menjalankan Frontend Vue 3
Buka terminal kedua:
```bash
cd frontend

# Install dependensi Node.js
npm install

# Jalankan Vite development server
npm run dev
```
* Akses aplikasi web di: `http://localhost:5173/login`

#### 4. Menjalankan Simulator Telemetri IoT (Opsional)
Buka terminal ketiga untuk menyimulasikan aliran data sensor dan spike ambang batas:
```bash
# Dari direktori root project
backend\venv\Scripts\python.exe -u dummy.py --spike-interval 3
```

---

### Metode 2: Full Docker Container 🐳
Menjalankan seluruh aplikasi (Frontend, Backend, Database PostgreSQL, Adminer) dalam kontainer Docker:
```bash
# Build dan jalankan seluruh container di background
docker-compose up -d --build

# Inisialisasi akun admin awal
docker exec -it gconnect_backend python create_admin.py
```

| Service | Port / URL Akses |
|---|---|
| 🖥️ Frontend Web App | `http://localhost:5173` |
| ⚙️ Backend REST API & Docs | `http://localhost:8000` (`/docs`) |
| 🗄️ Adminer Database GUI | `http://localhost:8080` |

---

## 📡 Ringkasan REST API

Dokumentasi interaktif OpenAPI / Swagger dapat diakses di: **`http://localhost:8000/docs`**

| Endpoint | Metode | Deskripsi |
|---|---|---|
| `/api/v1/auth/login` | `POST` | Autentikasi pengguna & perolehan JWT access token |
| `/api/v1/nodes/` | `GET`, `POST` | Mendapatkan daftar stasiun IoT & mendaftarkan stasiun baru |
| `/api/v1/nodes/{node_id}` | `GET`, `PUT`, `DELETE` | Detail stasiun, pembaruan nama/koordinat, atau penghapusan |
| `/api/v1/nodes/{node_id}/sensors/` | `GET`, `POST` | Konfigurasi sensor dan pemetaan field ThingSpeak |
| `/api/v1/nodes/{node_id}/telemetry/latest` | `GET` | Mengambil data pembacaan telemetri terkini |
| `/api/v1/nodes/{node_id}/telemetry/history` | `GET` | Mengambil arsip telemetri dengan rentang waktu (`1h`, `1d`, `1w`, `1M`, `custom`) |
| `/api/v1/nodes/{node_id}/telemetry/dashboard` | `GET` | Agregasi data komprehensif untuk halaman dashboard |
| `/api/v1/event-logs/` | `GET` | Daftar riwayat log anomali dan event perangkat |
| `/api/v1/system/config` | `GET`, `PUT` | Pengaturan interval polling dan caching telemetri |
| `/ws/dashboard` | `WebSocket` | Stream broadcast data sensor real-time ke antarmuka web |

---

## 👥 Tim Pengembang & Kolaborasi

**G-Connect Smart Farming Platform**  
Program Pengabdian Masyarakat — Laboratorium Elektronika dan Instrumentasi (ELINS)  
Departemen Ilmu Komputer dan Elektronika, Fakultas MIPA, Universitas Gadjah Mada

| Peran | Nama / Kontributor |
|---|---|
| 💻 **Software Developer** | Hanif (ELINS 23) |
| 👥 **Team Member** | Donny (ELINS 25) |
| 👥 **Team Member** | Sulthon (ELINS 25) |

---

<p align="center">
  <sub>&copy; 2026 G-CONNECT &bull; Laboratorium ELINS DIKE Universitas Gadjah Mada</sub>
</p>
