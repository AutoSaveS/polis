import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // maplibre-gl ships its own worker chunk; Vite's dep optimizer loses it
  optimizeDeps: { exclude: ['maplibre-gl'] },
})
