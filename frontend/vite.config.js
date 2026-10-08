import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const apiTarget = env.VITE_API_PROXY_TARGET
  const proxy = env.VITE_API_BASE_URL || !apiTarget
    ? undefined
    : Object.fromEntries(
      ['/auth', '/tokenauth', '/health', '/ready'].map((path) => [
        path,
        { target: apiTarget, changeOrigin: true },
      ]),
    )

  return {
    plugins: [react()],
    server: { proxy },
  }
})
