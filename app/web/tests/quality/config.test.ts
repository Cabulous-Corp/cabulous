import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

describe('Quality config', () => {
  it('vitest can discover this test file', () => {
    // If this test runs, vitest collection works.
    expect(true).toBe(true)
  })

  it('eslint config applies max-lines-per-function: 50', () => {
    const configPath = resolve(__dirname, '../../eslint.config.mjs')
    const raw = readFileSync(configPath, 'utf-8')
    expect(raw).toContain('max-lines-per-function')
    expect(raw).toContain('50')
  })

  it('vitest.config.ts exists', () => {
    const configPath = resolve(__dirname, '../../vitest.config.ts')
    const raw = readFileSync(configPath, 'utf-8')
    expect(raw.length).toBeGreaterThan(0)
  })
})
