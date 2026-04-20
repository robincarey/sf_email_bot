import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)))

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    fs: {
      strict: true,
      allow: [projectRoot],
      deny: ['.env', '.env.*', '*.pem', '*.crt', '**/.git/**'],
    },
  },
  test: {
    environment: 'happy-dom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
})
