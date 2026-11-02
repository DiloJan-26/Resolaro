export function publicConfig() {
  const url = import.meta.env.VITE_SUPABASE_URL;
  const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;
  const apiBase = import.meta.env.VITE_API_BASE_URL;
  if (!url || !key?.startsWith('sb_publishable_') || !apiBase || !url.startsWith('https://') || !apiBase.startsWith('https://')) {
    throw new Error('Public application configuration is incomplete');
  }
  return { url, key, apiBase: apiBase.replace(/\/$/, '') };
}
