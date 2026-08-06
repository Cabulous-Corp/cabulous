import { resolve } from 'node:path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      '@': resolve(__dirname),
    },
  },
  test: {
    globals: false,
    environment: 'node',
    include: ['tests/**/*.test.{ts,tsx}', '**/__tests__/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      include: ['lib/**/*.ts', 'hooks/**/*.ts', 'components/**/*.ts', 'components/**/*.tsx', 'app/**/*.ts', 'app/**/*.tsx'],
      exclude: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}', '**/*.d.ts', '**/types/**'],
    },
  },
})
