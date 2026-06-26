import path from 'node:path';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The browser talks to the API directly via VITE_API_URL in development
// (the backend container exposes :8000 on the host and its CORS policy allows
// http://localhost:5173). In production VITE_API_URL is unset and the bundle
// uses relative /api/* paths, which nginx proxies to the backend. Because of
// that, no dev server proxy is required here.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 5173,
  },
  build: {
    rollupOptions: {
      output: {
        // Split heavy, independently-cacheable vendors into their own chunks so
        // the main bundle stays lean and charts load only where needed.
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
          query: ['@tanstack/react-query'],
        },
      },
    },
  },
});
