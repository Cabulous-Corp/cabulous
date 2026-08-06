import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { Input } from '../../components/ui/input'

describe('Input', () => {
  it('leaves password length validation to the caller', () => {
    const loginMarkup = renderToStaticMarkup(<Input type="password" />)
    const passwordCreationMarkup = renderToStaticMarkup(<Input type="password" minLength={8} />)

    expect(loginMarkup).not.toContain('minLength="8"')
    expect(passwordCreationMarkup).toContain('minLength="8"')
  })
})
