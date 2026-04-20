import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Login from './Login'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      signInWithOtp: vi.fn(),
    },
  },
}))

import { useAuth } from '../context/AuthContext'

function AppLocation() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

describe('Login safe next handling', () => {
  it('falls back to /app for protocol-relative next values', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: '123' } as never,
      loading: false,
      session: null,
      signOut: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/login?next=//evil.example/path']}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/app" element={<AppLocation />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByTestId('location')).toHaveTextContent('/app')
  })

  it('preserves valid in-app next values', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: '123' } as never,
      loading: false,
      session: null,
      signOut: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/login?next=/app/preferences']}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/app/preferences" element={<AppLocation />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByTestId('location')).toHaveTextContent('/app/preferences')
  })
})
