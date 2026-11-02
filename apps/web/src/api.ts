import { publicConfig } from './config';

export type Role = 'ADMIN' | 'OPERATOR' | 'REVIEWER';
export interface Organization { id: string; name: string; role: Role }
export interface Me { user_id: string; organizations: Organization[] }
export interface CaseSummary { id: string; organization_id: string; title: string; status: 'NEW'; updated_at: string }
export interface Cases { items: CaseSummary[]; total: number }
export interface ApiErrorBody { error: { code: string; message: string; request_id: string; details: Record<string, string> } }

export class ApiError extends Error {
  constructor(public code: string, message: string, public status: number) { super(message); }
}

async function get<T>(path: string, token: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${publicConfig().apiBase}/api/v1${path}`, {
      headers: { Authorization: `Bearer ${token}` }, signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError('NETWORK_UNAVAILABLE', 'The API is unreachable. Try again shortly.', 0);
  }
  if (!response.ok) {
    let body: ApiErrorBody | undefined;
    try { body = await response.json() as ApiErrorBody; } catch { /* Provider body is untrusted. */ }
    const code = body?.error?.code || 'API_ERROR';
    const message = response.status === 401 ? 'Your session has expired. Sign in again.' :
      response.status === 403 ? 'You do not have access to this resource.' :
      response.status === 404 ? 'This resource is unavailable.' :
      response.status === 503 ? 'The service is temporarily unavailable.' : 'The request failed.';
    throw new ApiError(code, message, response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  me: (token: string, signal?: AbortSignal) => get<Me>('/me', token, signal),
  organization: (id: string, token: string, signal?: AbortSignal) => get<Organization>(`/organizations/${encodeURIComponent(id)}/context`, token, signal),
  cases: (id: string, token: string, signal?: AbortSignal) => get<Cases>(`/cases?organization_id=${encodeURIComponent(id)}`, token, signal),
};
