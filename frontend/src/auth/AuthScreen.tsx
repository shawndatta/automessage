import { useState, type FormEvent } from 'react'
import { MessageCircle } from 'lucide-react'
import './auth.css'

type Mode = 'signin' | 'signup'

type Props = {
  hasUsers: boolean
  onSuccess: () => void
}

export function AuthScreen({ hasUsers, onSuccess }: Props) {
  const [mode, setMode] = useState<Mode>(hasUsers ? 'signin' : 'signup')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const { login, signup } = await import('./api')
      if (mode === 'signup') {
        await signup({ name: name.trim(), email: email.trim(), password })
      } else {
        await login({ email: email.trim(), password })
      }
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <div className="auth-brand">
          <div className="auth-mark">
            <MessageCircle size={22} fill="currentColor" />
          </div>
          <div>
            <strong>AutoMessage</strong>
            <span>Self-hosted DM automation</span>
          </div>
        </div>

        <h1>{mode === 'signin' ? 'Sign in' : 'Create your account'}</h1>
        <p className="auth-lead">
          {mode === 'signin'
            ? 'Welcome back. Sign in to continue to your workspace.'
            : 'Set up the owner account for this local AutoMessage instance.'}
        </p>

        <div className="auth-tabs">
          <button
            type="button"
            className={mode === 'signin' ? 'active' : ''}
            onClick={() => {
              setMode('signin')
              setError(null)
            }}
          >
            Sign in
          </button>
          <button
            type="button"
            className={mode === 'signup' ? 'active' : ''}
            onClick={() => {
              setMode('signup')
              setError(null)
            }}
          >
            Sign up
          </button>
        </div>

        <form className="auth-form" onSubmit={submit}>
          {mode === 'signup' && (
            <label>
              <span>Name</span>
              <input
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Your name"
              />
            </label>
          )}
          <label>
            <span>Email</span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@company.com"
            />
          </label>
          <label>
            <span>Password</span>
            <input
              type="password"
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={mode === 'signup' ? 8 : 1}
              placeholder={mode === 'signup' ? 'At least 8 characters' : 'Your password'}
            />
          </label>

          {error && <div className="auth-error">{error}</div>}

          <button className="auth-submit" type="submit" disabled={busy}>
            {busy ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <p className="auth-footnote">
          Accounts stay on this machine in your local SQLite database. For a disposable demo
          login, run <code>automessage start default</code>.
        </p>
      </div>
    </div>
  )
}
