import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import ProtectedRoute from './ProtectedRoute'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '../context/AuthContext'

function LoginLocation() {
  const location = useLocation()
  return <div data-testid="login-search">{location.search}</div>
}

describe('ProtectedRoute next param encoding', () => {
  it('redirects unauthenticated users with encoded next query', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      session: null,
      signOut: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/app/items?filter=new arrivals&x=1']}>
        <Routes>
          <Route
            path="/app/items"
            element={(
              <ProtectedRoute>
                <div>Secret page</div>
              </ProtectedRoute>
            )}
          />
          <Route path="/login" element={<LoginLocation />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByTestId('login-search')).toHaveTextContent('?next=%2Fapp%2Fitems%3Ffilter%3Dnew%20arrivals%26x%3D1')
  })
})
