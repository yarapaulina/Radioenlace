import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Em desenvolvimento, as chamadas /api são redirecionadas ao backend FastAPI (porta 8000).
// Em produção, o build (dist/) é servido diretamente pelo FastAPI.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
