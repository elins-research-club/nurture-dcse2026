# 🌿 Nurture — Smart Farming IoT Platform

Platform monitoring, analitik cerdas, dan manajemen perangkat IoT terintegrasi untuk pertanian presisi (*smart agriculture*). Nurture menghubungkan stasiun sensor dan aktuator di lapangan dengan antarmuka web modern dan aplikasi mobile secara *real-time* untuk memantau kondisi tanah, iklim mikro, status perangkat keras, serta menyediakan laporan agronomi eksekutif dan deteksi anomali otomatis.

---

## 📐 Arsitektur Sistem

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             LAPANGAN / AGRICULTURAL FIELD                              │
│                                                                                        │
│   [Sensor Node 1 - Blok A]         [Sensor Node 2 - Blok B]          [Sensor Node N]   │
│   (Suhu, Kelembaban Tanah, pH, EC, NPK Soil, Suhu IoT, Status Modbus & Aktuator)       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Kirim Data Telemetri (HTTP / MQTT)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               THINGSPEAK CLOUD IOT                                     │
│                    Penerima & Penyimpan Data Sensor Lapangan                           │
│                Dual-Channel Aggregation & MQTT Push (<1 Detik)                         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ MQTT Stream & HTTP Poller Fallback
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND — FastAPI (Python 3.11)                             │
│                                                                                        │
│  ┌─────────────────┐   ┌──────────────────────┐   ┌─────────────────────────────────┐  │
│  │ RESTful API     │   │ WebSocket Broadcaster│   │ ThingSpeak MQTT & Poller        │  │
│  │ (/api/v1/..)    │   │ (/ws/dashboard)      │   │ (Connection Pooling + Cache)    │  │
│  └────────┬────────┘   └──────────┬───────────┘   └───────────────┬─────────────────┘  │
│           │                       │                               │                    │
│           └───────────────────────┴───────────────────────────────┘                    │
│                                   │                                                    │
│  ┌─────────────────────────────┐  │  ┌──────────────────────────────────────────────┐  │
│  │ PostgreSQL 15 Database      │◄─┘  │ Telegram Bot Alert Notification              │  │
│  │ (Async SQLAlchemy + AsyncPG)│     │ (Deteksi Anomali Ambang Batas & Offline)     │  │
│  └─────────────────────────────┘     └──────────────────────────────────────────────┘  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ REST API + WebSocket (Low-Latency)
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
┌───────────────────────────────────────┐       ┌────────────────────────────────────────┐
│     FRONTEND — Vue 3 + TypeScript     │       │   📱 MOBILE APP — Flutter & Riverpod   │
│                                       │       │                                        │
│  📊 Dashboard Telemetri Real-time     │       │  🍏 iPhone Liquid Glassmorphism Cards  │
│  🖥️ Manajemen Stasiun & Sensor IoT    │       │  📍 Two-Line Station Selector Drawer   │
│  🗺️ Peta GIS Satelit Google Hybrid    │       │  💎 Guest Screen & Midnight VIP Banner │
│  📄 3-Step CSV & PDF Export Wizard    │       │  ⚡ Live Stream WebSocket Sync         │
│  📜 Log Anomali & Kontrol Aktuator    │       │  📱 Cross-Platform (Android/iOS/Web)   │
└───────────────────────────────────────┘       └────────────────────────────────────────┘
```

### ⚡ Alur Data Real-Time & Event Engine
* **Push Telemetri Lapangan:** Sensor $\rightarrow$ ThingSpeak $\rightarrow$ MQTT Subscriber Backend $\rightarrow$ WebSocket Broadcast $\rightarrow$ Pinia Store (Web) / Riverpod State (Mobile).
* **Deteksi Anomali & Peringatan Dini:** Evaluasi otomatis ambang batas agronomi (NPK kritis, tanah kering, suhu boks panel tinggi) $\rightarrow$ Penyimpanan `EventLog` $\rightarrow$ Notifikasi Telegram Otomatis & Visual Alert Badge.

---

## ✨ Fitur Unggulan Platform

1. **📊 Executive Hero Telemetry Cards:**
   * **Keseimbangan Hara NPK:** Rasio proporsi nitrogen, fosfor, kalium dengan progress track multi-warna.
   * **Kondisi & Kelembaban Tanah:** Pemantauan multi-probe (Lengas Tanah %, pH, EC Konduktivitas µS, Suhu Tanah °C).
   * **Status Termal & Boks IoT:** Pemantauan suhu enclosure panel, suhu lingkungan, kelembaban udara, dan tegangan aki solar.
2. **📱 Modern Mobile Experience (Flutter):**
   * Desain **iPhone Liquid Frosted Glassmorphism** dengan pendaran ambient mesh lembut.
   * **Two-Line Modern Station Selector** terintegrasi dengan **Modal Bottom Sheet Drawer**.
   * Mode Tamu (*Guest Dashboard*) dengan **Midnight Obsidian VIP Card**.
3. **🗺️ Peta Satelit Interaktif (GIS):**
   * Peta Google Maps Hybrid Satellite Tiles resolusi tinggi via Leaflet.
   * Visualisasi pin marker stasiun lahan, status online/offline, dan drag-to-update koordinat GPS.
4. **📄 Generator Laporan PDF & CSV Eksekutif:**
   * **Laporan Resmi PDF:** Tata letak dokumen resmi berlogo 4 institusi (UGM, DIKE, ELINS, Nurture), evaluasi batas agronomi, dan metadata GPS.
   * **CSV Export Wizard:** 3-step wizard interaktif (pilihan stasiun, rentang waktu kustom, agregasi rata-rata).
5. **🔔 Notifikasi Anomali Telegram:**
   * Pengiriman otomatis pesan peringatan dini saat parameter sensor melampaui batas kritis atau perangkat *offline*.

---

## 🗂️ Struktur Proyek

```
GGGCONNECT/
├── backend/                       # Aplikasi FastAPI Core (REST API, WebSocket, Poller)
│   ├── app/
│   │   ├── core/                  # Konfigurasi aplikasi, Database Async, Autentikasi JWT
│   │   ├── dependencies/          # Injeksi dependensi (Auth, User Session)
│   │   ├── models/                # SQLAlchemy ORM Models (User, Node, Sensor, Channel, EventLog)
│   │   ├── repositories/          # Abstraksi kueri database asinkron
│   │   ├── routers/               # API Endpoints (Auth, Nodes, Sensors, Telemetry, Logs, Push)
│   │   ├── schemas/               # Pydantic v2 validation schemas
│   │   ├── services/              # Logika bisnis (MQTT, Poller, Ring-Buffer, Telegram Bot)
│   │   └── main.py                # Titik masuk aplikasi backend
│   ├── dummy.py                   # Simulator telemetri IoT & pengujian spike anomali
│   ├── create_admin.py            # Skrip pembuat akun administrator awal
│   ├── requirements.txt           # Dependensi pustaka Python
│   └── Dockerfile
├── frontend/                      # Aplikasi Web Frontend (Vue 3 + TypeScript + Vite)
│   ├── src/
│   │   ├── assets/                # CSS global, Tailwind CSS v4 tokens, font, ikon
│   │   ├── components/            # Komponen modular (UI shadcn, Layout, Dashboard, Modals)
│   │   │   ├── dashboard/         # NodeDashboard, SensorCard, ExportTelemetryModal, ReportPreviewModal
│   │   │   ├── layout/            # DashboardLayout, Sidebar, Navbar
│   │   │   └── ui/                # Button, Card, Badge, Dialog, Dropdown, Input, Label
│   │   ├── composables/           # TanStack Query hooks, WebSocket client, Geocoding
│   │   ├── stores/                # Pinia state stores (Auth, Telemetry, UI)
│   │   ├── views/                 # Halaman utama (Login, Dashboard, Nodes, Map, Alerts, Settings)
│   │   ├── router/                # Vue Router navigation guards
│   │   └── main.ts                # Titik masuk aplikasi frontend
│   ├── package.json
│   └── vite.config.ts             # Optimasi Vite, proxy API, vendor chunks
├── mobile/                        # Aplikasi Mobile Flutter (Android / iOS / Web)
│   ├── lib/
│   │   ├── core/                  # App theme, constants, color tokens, API client
│   │   ├── models/                # Data models (NodeModel, SensorModel, Telemetry, User)
│   │   ├── providers/             # State management Riverpod (Auth, Nodes, Telemetry)
│   │   ├── presentation/          # Antarmuka & Layar
│   │   │   ├── screens/           # DashboardScreen, GuestDashboardScreen, LoginScreen
│   │   │   └── widgets/           # StationHeroHeader, NpkSummaryCard, SoilConditionCard, ThermalIotCard
│   │   └── main.dart              # Titik masuk aplikasi Flutter
│   └── pubspec.yaml               # Dependensi pustaka Flutter
├── docker-compose.yml             # Orkestrasi Docker (Full Stack / Database Only)
└── README.md
```

---

## 🛠️ Tech Stack

| Lapisan Sistem | Teknologi & Pustaka Utama |
|---|---|
| **Web Frontend** | **Vue 3** (Composition API, `<script setup>`), **TypeScript**, **Vite** |
| **Mobile App** | **Flutter 3.x**, **Dart**, **Flutter Riverpod**, **Lucide Icons Flutter** |
| **Styling & UI Kit** | **Tailwind CSS v4**, **shadcn/ui** (Radix UI Vue primitives), **iOS Liquid Glassmorphism** |
| **Data Viz & Charts** | **Apache ECharts** (`vue-echarts`), Algoritma LTTB (*Largest-Triangle-Three-Buckets*) |
| **GIS & Pemetaan** | **Leaflet**, Google Maps Hybrid High-Resolution Satellite Tiles |
| **PDF & Dokumen** | **jsPDF**, **jspdf-autotable**, **html2canvas** (Lazy Loaded) |
| **State & Fetching** | **Pinia**, **Riverpod**, **TanStack Query (Vue Query)**, Native WebSocket Client |
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
* [Flutter SDK 3.x](https://flutter.dev/) (untuk menjalankan aplikasi mobile)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (opsional untuk database terisolasi)

---

### Metode 1: Mode Pengembangan Cepat (*Hybrid Development* ⚡)

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

#### 3. Menjalankan Web Frontend Vue 3
Buka terminal kedua:
```bash
cd frontend

# Install dependensi Node.js
npm install

# Jalankan Vite development server
npm run dev
```
* Akses aplikasi web di: `http://localhost:5173/login`

#### 4. Menjalankan Aplikasi Mobile Flutter
Buka terminal ketiga:
```bash
cd mobile

# Unduh dependensi Flutter
flutter pub get

# Jalankan di Web Browser (Hot-Reload aktif):
flutter run -d chrome
# Atau jalankan di Web Server (Port 8085):
flutter run -d web-server --web-port 8085
```
* Akses aplikasi mobile web di: `http://localhost:8085`

#### 5. Menjalankan Simulator Telemetri IoT (Opsional)
Buka terminal keempat untuk menyimulasikan aliran data sensor dan spike ambang batas:
```bash
# Dari direktori root project
backend\venv\Scripts\python.exe -u dummy.py --spike-interval 3
```

---

### Metode 2: Full Docker Container 🐳
Menjalankan seluruh aplikasi dalam kontainer Docker:
```bash
# Build dan jalankan seluruh container di background
docker-compose up -d --build

# Inisialisasi akun admin awal
docker exec -it gconnect_backend python create_admin.py
```

| Service | Port / URL Akses |
|---|---|
| 🖥️ Frontend Web App | `http://localhost:5173` |
| 📱 Mobile Web App | `http://localhost:8085` |
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
| `/ws/dashboard` | `WebSocket` | Stream broadcast data sensor real-time ke antarmuka web & mobile |

---

## 👥 Tim Pengembang & Kolaborasi

**Nurture Smart Farming Platform**  
Program Pengabdian Masyarakat — Laboratorium Elektronika dan Instrumentasi (ELINS)  
Departemen Ilmu Komputer dan Elektronika, Fakultas MIPA, Universitas Gadjah Mada

| Peran | Nama / Kontributor |
|---|---|
| 💻 **Software Developer** | Hanif (ELINS 23) |
| 👥 **Team Member** | Donny (ELINS 25) |
| 👥 **Team Member** | Sulthon (ELINS 25) |

---

<p align="center">
  <sub>&copy; 2026 NURTURE &bull; Laboratorium ELINS DIKE Universitas Gadjah Mada</sub>
</p>
