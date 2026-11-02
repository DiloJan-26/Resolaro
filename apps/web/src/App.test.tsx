import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';
import { AuthProvider } from './auth';
import { App } from './App';

const fake = vi.hoisted(() => ({
  session: null as null | { access_token: string; user: { email: string } },
  signIn: vi.fn(), signOut: vi.fn(),
}));
vi.mock('./supabase', () => ({ getSupabase: () => ({ auth: {
  getSession: async () => ({ data: { session: fake.session }, error: null }),
  onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
  signInWithPassword: fake.signIn, signOut: fake.signOut,
} }) }));
vi.mock('./config', () => ({ publicConfig: () => ({ apiBase: 'https://api.example.test' }) }));

function show(path = '/') { return render(<MemoryRouter initialEntries={[path]}><AuthProvider><App /></AuthProvider></MemoryRouter>); }

beforeEach(() => {
  fake.session = null;
  fake.signIn.mockReset().mockResolvedValue({ error: { message: 'bad' } });
  fake.signOut.mockReset().mockResolvedValue({ error: null });
  vi.stubGlobal('fetch', vi.fn());
});

test('signed out user sees labeled login and safe error', async () => {
  show('/login');
  const email = await screen.findByLabelText('Email');
  fireEvent.change(email, { target: { value: 'demo@example.test' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Sign in failed');
});

test('authenticated user sees navigation and empty cases', async () => {
  fake.session = { access_token: 'test-token', user: { email: 'demo@example.test' } };
  vi.mocked(fetch).mockImplementation(async (input) => ({ ok: true, json: async () =>
    String(input).endsWith('/me') ? { user_id: 'u', organizations: [{ id: 'o', name: 'Demo', role: 'OPERATOR' }] } : { items: [], total: 0 },
  }) as Response);
  show('/');
  expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('link', { name: 'Cases' }));
  expect(screen.getByText('No cases are available for this organization.')).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument();
});

test('no membership has clear permission state', async () => {
  fake.session = { access_token: 'test-token', user: { email: 'demo@example.test' } };
  vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({ user_id: 'u', organizations: [] }) } as Response);
  show();
  expect(await screen.findByRole('heading', { name: 'No organization access' })).toBeInTheDocument();
});

test('API failure is recoverable without leaking provider detail', async () => {
  fake.session = { access_token: 'test-token', user: { email: 'demo@example.test' } };
  vi.mocked(fetch).mockResolvedValue({ ok: false, status: 503, json: async () => ({ error: { code: 'DATABASE_UNAVAILABLE', message: 'private detail' } }) } as Response);
  show();
  expect(await screen.findByRole('alert')).toHaveTextContent('temporarily unavailable');
  expect(screen.queryByText('private detail')).not.toBeInTheDocument();
  await waitFor(() => expect(screen.getByRole('button', { name: 'Retry' })).toBeEnabled());
});
