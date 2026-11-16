import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

const apiTarget = process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000"

const apiProxy = {
  "/api": {
    target: apiTarget,
    changeOrigin: true,
    secure: false,
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "127.0.0.1",
    proxy: apiProxy,
  },
  preview: {
    port: 5173,
    host: "0.0.0.0",
    proxy: apiProxy,
  },
})
