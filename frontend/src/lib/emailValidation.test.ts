import { describe, expect, it } from 'vitest'
import { validateEmailAddress } from './emailValidation'

describe('validateEmailAddress', () => {
  it('accepts a normal email', () => {
    expect(validateEmailAddress('user@gmail.com')).toBeNull()
  })

  it('rejects common TLD typos', () => {
    expect(validateEmailAddress('user@gmail.coms')).toMatch(/typos/)
    expect(validateEmailAddress('user@example.con')).toMatch(/typos/)
  })

  it('rejects malformed addresses', () => {
    expect(validateEmailAddress('not-an-email')).not.toBeNull()
    expect(validateEmailAddress('a@@b.com')).not.toBeNull()
  })
})
