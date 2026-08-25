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
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
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
