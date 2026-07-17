import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { registerSW } from 'virtual:pwa-register'
import './index.css'
import App from './App.tsx'

// Register service worker for offline support
// autoUpdate: reloads silently when a new version is deployed
registerSW({
  onNeedRefresh() {
    // New version available - auto update
    console.log('[PWA] New content available, updating...');
  },
  onOfflineReady() {
    console.log('[PWA] App is ready for offline use.');
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
