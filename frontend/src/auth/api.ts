export type AuthUser = {
  id: number
  email: string
  name: string
  is_default: boolean
}

export type AuthMeResponse = {
  authenticated: boolean
  user: AuthUser | null
  default_user_mode: boolean
}

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json()
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.detail)) {
      return (
        data.detail
          .map((d: { msg?: string }) => d.msg)
          .filter(Boolean)
          .join(', ') || res.statusText
      )
    }
  } catch {
    /* ignore */
  }
  return res.statusText || 'Request failed'
}

export async function fetchMe(): Promise<AuthMeResponse> {
  const res = await fetch('/api/auth/me', { credentials: 'include' })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function signup(input: {
  name: string
  email: string
  password: string
}): Promise<AuthUser> {
  const res = await fetch('/api/auth/signup', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error(await readError(res))
  const data = await res.json()
  return data.user
}

export async function login(input: {
  email: string
  password: string
}): Promise<AuthUser> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error(await readError(res))
  const data = await res.json()
  return data.user
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
}

export async function defaultSession(): Promise<AuthUser> {
  const res = await fetch('/api/auth/default-session', {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) throw new Error(await readError(res))
  const data = await res.json()
  return data.user
}
