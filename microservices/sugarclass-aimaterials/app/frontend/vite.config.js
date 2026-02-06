import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/services/aimaterials/',
  server: {
    host: '0.0.0.0',  // Allow external access (ngrok)
    port: 5173,
    allowedHosts: ['yuri-oversorrowful-seminervously.ngrok-free.app'],
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/images': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/generated_images': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/qa_images': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/exercise_images': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
