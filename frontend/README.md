# 🌿 G-Connect — Frontend Application

Aplikasi web dashboard real-time untuk platform IoT Smart Farming G-Connect, dibangun menggunakan **Vue 3**, **TypeScript**, **Vite**, dan **TailwindCSS v4**.

---

## 🛠️ Fitur & Teknologi Frontend

- **Vue 3 + Composition API (`<script setup>`)**
- **TailwindCSS v4 + Radix UI / shadcn components**
- **Pinia Store:** Manajemen state global terpusat (`telemetryStore`, `authStore`)
- **Apache ECharts (`vue-echarts`):** Grafik telemetri dinamis dengan pills kategori dan agregasi waktu
- **Leaflet GIS:** Peta satelit interaktif Google Maps Hybrid Tiles dengan draggable marker
- **TanStack Query (Vue Query):** Cache & data fetching asinkron
- **WebSocket Streaming:** Sinkronisasi status node dan stream sensor real-time

---

## 🚀 Menjalankan Frontend

```bash
# Install dependencies
npm install

# Jalankan development server
npm run dev

# Build untuk production
npm run build
```

