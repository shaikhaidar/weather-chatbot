import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'WeatherBot AI',
        short_name: 'WeatherBot',
        description: 'AI-powered weather prediction and analysis chatbot',
        theme_color: '#1e1b4b',
        background_color: '#0f0e17',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        // Cache all static assets
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // Cache API responses with network-first strategy
        runtimeCaching: [
          {
            urlPattern: /^\/api\/predictions\/iot/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'iot-api-cache',
              expiration: { maxEntries: 10, maxAgeSeconds: 300 },
              networkTimeoutSeconds: 5,
            },
          },
          {
            urlPattern: /^\/api\/datasets/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'datasets-api-cache',
              expiration: { maxEntries: 20, maxAgeSeconds: 86400 },
              networkTimeoutSeconds: 10,
            },
          },
          {
            urlPattern: /^\/api\/history/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'history-api-cache',
              expiration: { maxEntries: 50, maxAgeSeconds: 3600 },
              networkTimeoutSeconds: 10,
            },
          },
        ],
      },
    }),
  ],
  server: {
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
