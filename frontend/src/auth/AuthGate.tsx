import { useEffect, useState } from 'react'
import App from '../App'
import { AuthScreen } from './AuthScreen'
import {
  defaultSession,
  fetchMe,
  logout,
  type AuthUser,
} from './api'
import './auth.css'

type BootState = {
  loading: boolean
  user: AuthUser | null
  hasUsers: boolean
  error: string | null
}

export function AuthGate() {
  const [boot, setBoot] = useState<BootState>({
    loading: true,
    user: null,
    hasUsers: false,
    error: null,
  })

  async function refresh() {
    setBoot((b) => ({ ...b, loading: true, error: null }))
    try {
      const [me, state] = await Promise.all([
        fetchMe(),
        fetch('/api/state', { credentials: 'include' }).then(async (r) => {
          if (!r.ok) throw new Error('Failed to load app state')
          return r.json() as Promise<{ has_users: boolean; default_user_mode: boolean }>
        }),
      ])

      if (!me.authenticated && me.default_user_mode) {
        const user = await defaultSession()
        setBoot({ loading: false, user, hasUsers: true, error: null })
        return
      }

      setBoot({
        loading: false,
        user: me.user,
        hasUsers: state.has_users,
        error: null,
      })
    } catch (err) {
      setBoot({
        loading: false,
        user: null,
        hasUsers: false,
        error: err instanceof Error ? err.message : 'Failed to start',
      })
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  if (boot.loading) {
    return <div className="auth-loading">Starting AutoMessage…</div>
  }

  if (boot.error && !boot.user) {
    return (
      <div className="auth-loading">
        <div>
          <p>{boot.error}</p>
          <button type="button" onClick={() => void refresh()}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!boot.user) {
    return <AuthScreen hasUsers={boot.hasUsers} onSuccess={() => void refresh()} />
  }

  return (
    <App
      user={boot.user}
      onSignOut={async () => {
        await logout()
        setBoot({ loading: false, user: null, hasUsers: true, error: null })
      }}
    />
  )
}
