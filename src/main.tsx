import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { setWorkerUrl } from 'maplibre-gl'
import './index.css'
import App from './App.tsx'

setWorkerUrl(new URL('./maplibre-gl-worker.mjs', window.location.href).toString())

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
