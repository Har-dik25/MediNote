import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // During local dev, proxy /api to your backend so cookies (session auth)
    // work without CORS gymnastics. Point VITE_DEV_API_PROXY at your API host.
    proxy: process.env.VITE_DEV_API_PROXY ? {
      '/api': {
        target: process.env.VITE_DEV_API_PROXY,
        changeOrigin: true,
        secure: true
      }
    } : undefined
  },
  build: {
    sourcemap: true,
    outDir: 'dist'
  }
});
