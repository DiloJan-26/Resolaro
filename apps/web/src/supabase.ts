import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { publicConfig } from './config';

let client: SupabaseClient | undefined;
export function getSupabase(): SupabaseClient {
  if (!client) {
    const { url, key } = publicConfig();
    client = createClient(url, key, { auth: { persistSession: true, autoRefreshToken: true } });
  }
  return client;
}
