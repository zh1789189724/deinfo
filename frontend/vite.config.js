/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'path'

// Plugin to mock CSS imports in tests
function cssMockPlugin() {
  return {
    name: 'css-mock',
    enforce: 'pre',
    transform(code, id) {
      if (process.env.VITEST && id.endsWith('.css')) {
        return { code: 'export default undefined', map: null }
      }
    },
  }
}

const isTest = process.env.VITEST === 'true'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: isTest ? [] : [ElementPlusResolver()],
    }),
    Components({
      resolvers: isTest ? [] : [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{js,ts}'],
    setupFiles: ['./src/tests/setup.js'],
    server: {
      deps: {
        fallbackCJS: true,
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
