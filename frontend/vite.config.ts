import path from "node:path"
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('echarts') || id.includes('zrender') || id.includes('vue-echarts')) {
              return 'vendor-echarts'
            }
            if (id.includes('leaflet')) {
              return 'vendor-leaflet'
            }
            if (id.includes('lucide-vue-next')) {
              return 'vendor-icons'
            }
            if (id.includes('vue') || id.includes('pinia') || id.includes('@tanstack/vue-query')) {
              return 'vendor-core'
            }
          }
        }
      }
    }
  },
  server: {
    host: true,
    allowedHosts: [
      'unaugmented-unfine-charles.ngrok-free.dev',
      '.ngrok-free.dev',
      '.ngrok-free.app',
      '.ngrok.io',
    ],
    // Frontend memanggil "/api/v1/..." ke dirinya sendiri, lalu Vite yang
    // meneruskan ke backend. Tanpa ini alamat backend harus ditulis lengkap
    // di kode, dan itu langsung rusak begitu dibuka dari perangkat lain --
    // "localhost" di HP menunjuk ke HP itu sendiri, bukan ke laptop.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
})
