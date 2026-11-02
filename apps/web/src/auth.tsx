import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';
import type { Session } from '@supabase/supabase-js';
import { getSupabase } from './supabase';

interface AuthState { session: Session | null; loading: boolean; expired: boolean; logout: () => Promise<void>; markExpired: () => void }
const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [expired, setExpired] = useState(false);
  useEffect(() => {
    let active = true;
    const supabase = getSupabase();
    void supabase.auth.getSession().then(({ data, error }) => {
      if (active) { setSession(error ? null : data.session); setLoading(false); }
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, current) => {
      if (active) { setSession(current); setLoading(false); if (current) setExpired(false); }
    });
    return () => { active = false; subscription.unsubscribe(); };
  }, []);
  const value = useMemo<AuthState>(() => ({
    session, loading, expired,
    logout: async () => { await getSupabase().auth.signOut(); setSession(null); setExpired(false); },
    markExpired: () => setExpired(true),
  }), [session, loading, expired]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error('AuthProvider is missing');
  return value;
}
