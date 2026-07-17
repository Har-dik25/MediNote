// Production API client.
//
// Auth model: the backend sets an httpOnly session cookie on login, so the
// browser never has to hold a token in JS-accessible storage (no
// localStorage/sessionStorage — those are readable by any injected script
// and are the wrong place for a session credential in a clinical app).
// Every request goes out with credentials: 'include'.
//
// Backend contract (mirrors the FastAPI service this is meant to sit in front of):
//   POST   /auth/signup              { name, email, password, clinicName, specialty, phone, region } -> { user }
//   POST   /auth/login              { email, password }        -> { user }
//   POST   /auth/logout             {}                          -> {}
//   GET    /auth/me                                              -> { user } | 401
//   PATCH  /auth/profile            { name?, clinicName?, specialty?, phone?, region? } -> { user }
//   GET    /patients?query=&page=                                -> { items, total, page, pageSize }
//   POST   /patients                { name, mrn, dob?, phone? } -> { patient }
//   GET    /notes?status=&query=&page=                           -> { items, total, page, pageSize }
//   POST   /transcribe              multipart { audio }         -> { transcript }
//   POST   /notes/generate          { transcript, patientId? }  -> { noteId, soap, icd10, tests, safetyFlag, safetyReason }
//   PATCH  /notes/:id               { soap }                     -> { ok }
//   POST   /notes/:id/approve       {}                           -> { ok, approvedAt }
//   POST   /tools/drug-interaction  { drugA, drugB }             -> { severity, message }
//   POST   /tools/guidelines        { query }                    -> { summary, source? }
//   POST   /tools/drug-lookup       { query }                    -> { summary, drugClass? }
//   GET    /settings                                              -> { settings }
//   PATCH  /settings                { settings }                 -> { settings }

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const REQUEST_TIMEOUT_MS = 20000;
const MAX_RETRIES = 1;

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function rawFetch(path, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response;
  try {
    response = await fetch(API_BASE_URL + path, {
      credentials: 'include',
      ...options,
      signal: controller.signal
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new ApiError(0, 'The request timed out. Check your connection and try again.');
    }
    throw new ApiError(0, 'Could not reach the server. Check your connection and try again.');
  }
  clearTimeout(timeoutId);

  let body = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try { body = await response.json(); } catch { body = null; }
  }

  if (!response.ok) {
    const detail = (body && (body.detail || body.message)) || `Request failed (${response.status})`;
    throw new ApiError(response.status, detail);
  }
  return body;
}

export async function apiFetch(path, options = {}, retries = MAX_RETRIES) {
  try {
    return await rawFetch(path, options);
  } catch (err) {
    // Only retry idempotent-safe network/timeout failures, never a server decision.
    const isRetryable = err instanceof ApiError && err.status === 0 && (!options.method || options.method === 'GET');
    if (retries > 0 && isRetryable) {
      return apiFetch(path, options, retries - 1);
    }
    throw err;
  }
}

function json(body) {
  return { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
}

export const realApi = {
  signup: (payload) => apiFetch('/auth/signup', { method: 'POST', ...json(payload) }),
  login: (email, password) => apiFetch('/auth/login', { method: 'POST', ...json({ email, password }) }),
  logout: () => apiFetch('/auth/logout', { method: 'POST' }),
  me: () => apiFetch('/auth/me'),
  updateProfile: (fields) => apiFetch('/auth/profile', { method: 'PATCH', ...json(fields) }),

  listPatients: (params) => apiFetch(`/patients?${new URLSearchParams(params)}`),
  getPatient: (id) => apiFetch(`/patients/${encodeURIComponent(id)}`),
  createPatient: (payload) => apiFetch('/patients', { method: 'POST', ...json(payload) }),
  listNotes: (params) => apiFetch(`/notes?${new URLSearchParams(params)}`),

  transcribeAudio: (file) => {
    const form = new FormData();
    form.append('audio', file);
    return apiFetch('/transcribe', { method: 'POST', body: form });
  },
  generateNote: (transcript, patientId) => apiFetch('/notes/generate', { method: 'POST', ...json({ transcript, patientId }) }),
  saveNote: (noteId, soap) => apiFetch(`/notes/${encodeURIComponent(noteId)}`, { method: 'PATCH', ...json({ soap }) }),
  approveNote: (noteId) => apiFetch(`/notes/${encodeURIComponent(noteId)}/approve`, { method: 'POST' }),

  checkDrugInteraction: (drugA, drugB) => apiFetch('/tools/drug-interaction', { method: 'POST', ...json({ drugA, drugB }) }),
  searchGuideline: (query) => apiFetch('/tools/guidelines', { method: 'POST', ...json({ query }) }),
  lookupDrug: (query) => apiFetch('/tools/drug-lookup', { method: 'POST', ...json({ query }) }),

  getSettings: () => apiFetch('/settings'),
  updateSettings: (settings) => apiFetch('/settings', { method: 'PATCH', ...json({ settings }) })
};
