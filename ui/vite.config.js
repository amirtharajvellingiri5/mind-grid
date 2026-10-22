import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// /api/* is proxied to the GridMind API so the browser never needs CORS or the basic-auth creds.
// API_TARGET defaults to a local API (or an SSH tunnel to the VPS on :8000).
// For the public URL: API_TARGET=https://mind-grid.147.93.154.37.sslip.io API_AUTH=user:pass npm run dev
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.API_TARGET || 'http://localhost:8000',
        auth: process.env.API_AUTH,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
})
