import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: env.VITE_DEV_API_PROXY ? {
        '/api': {
          target: env.VITE_DEV_API_PROXY,
          changeOrigin: true,
          secure: false
        }
      } : undefined
    },
    build: {
      sourcemap: true,
      outDir: 'dist'
    }
  };
});
