import { Component, useEffect, useState, type FormEvent, type PropsWithChildren } from 'react';
import { Link, NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { api, ApiError, type Cases, type Me } from './api';
import { useAuth } from './auth';
import { routes } from './routes';
import { getSupabase } from './supabase';
import { Button, Card, Notice } from './ui';

class ErrorBoundary extends Component<PropsWithChildren, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { /* Do not log potentially sensitive browser state. */ }
  render() { return this.state.failed ? <main className="login-wrap"><Card><h1>Application unavailable</h1><p>Reload the page or contact an administrator.</p></Card></main> : this.props.children; }
}

function Login() {
  const { session, loading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  if (loading) return <main className="login-wrap" role="status">Checking session…</main>;
  if (session) return <Navigate to={routes.dashboard} replace />;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setPending(true);
    try {
      const result = await getSupabase().auth.signInWithPassword({ email, password });
      if (result.error) setError('Sign in failed. Check your credentials and try again.');
      else navigate(routes.dashboard, { replace: true });
    } catch { setError('Sign in is unavailable. Try again shortly.'); }
    finally { setPending(false); }
  }
  return <main className="login-wrap"><div className="login"><p className="brand">Resolaro</p><Card>
    <h1>Sign in</h1><p className="muted">Resolution operations for your team.</p>
    <Notice>Demo records, when available, use synthetic data.</Notice>
    <form onSubmit={submit}><label className="field">Email<input autoComplete="username" type="email" required value={email} onChange={event => setEmail(event.target.value)} /></label>
      <label className="field">Password<input autoComplete="current-password" type="password" required value={password} onChange={event => setPassword(event.target.value)} /></label>
      {error && <p className="error" role="alert">{error}</p>}<Button type="submit" disabled={pending}>{pending ? 'Signing in…' : 'Sign in'}</Button></form>
    <p className="muted">Access is managed by your organization. Public sign up is unavailable.</p>
  </Card></div></main>;
}

function Protected({ children }: PropsWithChildren) {
  const { loading, session, expired, logout } = useAuth();
  if (loading) return <main className="login-wrap" role="status">Checking session…</main>;
  if (expired) return <main className="login-wrap"><Card><h1>Session expired</h1><p>Sign in again to continue.</p><Button onClick={() => void logout()}>Sign out</Button></Card></main>;
  if (!session) return <Navigate to={routes.login} replace />;
  return children;
}

function Shell({ children, orgName }: PropsWithChildren<{ orgName: string }>) {
  const { session, logout } = useAuth();
  return <div className="app"><a className="skip" href="#main-content">Skip to content</a><aside className="sidebar"><div className="brand">Resolaro</div><p className="muted">{orgName}</p><nav aria-label="Main navigation">
    <NavLink to={routes.dashboard} end>Dashboard</NavLink><NavLink to={routes.cases}>Cases</NavLink><NavLink to={routes.settings}>Settings</NavLink>
  </nav></aside><main id="main-content" className="main"><header className="topbar"><div><p className="muted">Operational console</p></div><div className="topbar-actions"><span>{session?.user.email}</span><Button secondary onClick={() => void logout()}>Sign out</Button></div></header>{children}</main></div>;
}

function Workspace() {
  const { session, markExpired, logout } = useAuth();
  const [me, setMe] = useState<Me | null>(null);
  const [cases, setCases] = useState<Cases | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);
  const token = session!.access_token;
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null);
    void (async () => {
      try {
        const identity = await api.me(token, controller.signal);
        if (controller.signal.aborted) return;
        setMe(identity);
        if (identity.organizations.length) setCases(await api.cases(identity.organizations[0].id, token, controller.signal));
        else setCases(null);
      } catch (cause) {
        if (controller.signal.aborted) return;
        const failure = cause instanceof ApiError ? cause : new ApiError('API_ERROR', 'The request failed.', 500);
        if (failure.status === 401) markExpired(); else setError(failure);
      } finally { if (!controller.signal.aborted) setLoading(false); }
    })();
    return () => controller.abort();
  }, [token, attempt, markExpired]);
  if (loading) return <main className="login-wrap" role="status">Loading workspace…</main>;
  if (error) return <main className="login-wrap"><Card><h1>Workspace unavailable</h1><Notice error>{error.message}</Notice><Button onClick={() => setAttempt(value => value + 1)}>Retry</Button></Card></main>;
  if (!me?.organizations.length) return <main className="login-wrap"><Card><h1>No organization access</h1><p>Your account has no organization membership. Ask an administrator to grant access.</p><Button secondary onClick={() => void logout()}>Sign out</Button></Card></main>;
  const org = me.organizations[0];
  return <Shell orgName={org.name}><Routes>
    <Route path="/" element={<><h1>Dashboard</h1><p className="muted">Signed in as {session?.user.email}. Current organization: {org.name}.</p><div className="grid"><Card><h2>Cases</h2><p>{cases?.total ?? 'Unavailable'}</p><Link to={routes.cases}>View cases</Link></Card><Card><h2>SLA monitoring</h2><p className="muted">Not available yet</p></Card><Card><h2>Investigations</h2><p className="muted">Not available yet</p></Card></div></>} />
    <Route path="/cases" element={<><h1>Cases</h1><p className="muted">Read-only case summary</p>{cases?.items.length ? <ul>{cases.items.map(item => <li key={item.id}>{item.title} — {item.status}</li>)}</ul> : <div className="empty">No cases are available for this organization.</div>}</>} />
    <Route path="/settings" element={<><h1>Settings</h1><Card><h2>Organization</h2><p>{org.name}</p><p>Role: {org.role}</p><p className="muted">Account and membership changes are managed by an administrator.</p></Card></>} />
    <Route path="*" element={<><h1>Page unavailable</h1><Link to={routes.dashboard}>Go to dashboard</Link></>} />
  </Routes></Shell>;
}

export function App() {
  return <ErrorBoundary><Routes>
    <Route path={routes.login} element={<Login />} />
    <Route path="/*" element={<Protected><Workspace /></Protected>} />
  </Routes></ErrorBoundary>;
}
