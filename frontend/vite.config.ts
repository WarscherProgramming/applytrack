import path from 'node:path';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The browser talks to the API directly via VITE_API_URL in development and on
// Vercel. If VITE_API_URL is unset, the bundle uses relative /api/* paths for
// same-origin Docker/nginx-style hosting. No dev server proxy is required here.
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
