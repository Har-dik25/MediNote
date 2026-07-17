# MediMate — Frontend

A production-structured React (Vite) frontend for the MediMate clinical documentation copilot. Ships as a multi-page app: sign-in, patient list, encounter workspace (SOAP note generation + clinical tools), note history, and settings.

This package is **frontend-only by design** — it talks to a backend over a documented HTTP contract (see below) but ships with a full in-memory mock adapter so you can run and demo the entire app before the backend exists.

## Quick start

```bash
npm install
cp .env.example .env
npm run dev
```

Open the printed local URL. With the default `.env` (`VITE_USE_MOCKS=true`), there's no seeded account or seeded patients — click **Create an account** on the sign-in screen and fill in your name, email, password, and clinic details. That becomes your profile (editable later in Settings). Patients are the same: add them yourself from the Patients page — nothing is pre-populated, same as a real deployment would be for a new clinic.

The mock adapter keeps accounts/patients/notes in memory only — a page refresh during dev keeps your session (via `/auth/me`), but restarting the dev server clears everything, since there's no real database yet.

## Project layout

```
src/
  api/
    client.js     Real API client — fetch with timeout, retry, typed errors, cookie auth
    mock.js       In-memory mock adapter — same method signatures as client.js
    index.js      Picks real vs mock based on VITE_USE_MOCKS
  context/
    AuthContext.jsx    Session state, checks /auth/me on load
    ToastContext.jsx   Global toast notifications
  components/
    Layout.jsx           Header, nav, sign-out
    ProtectedRoute.jsx   Redirects to /login if not authenticated
    Banner.jsx           Info/danger alert banner
  pages/
    LoginPage.jsx
    EncounterPage.jsx    Main SOAP-note workspace (audio/text intake, clinical tools)
    PatientListPage.jsx
    NoteHistoryPage.jsx
    SettingsPage.jsx
    NotFoundPage.jsx
```

## Wiring up the real backend

1. Set `VITE_USE_MOCKS=false`.
2. Set `VITE_API_BASE_URL` to your API's origin (or leave as `/api` and configure a rewrite — see Deployment below).
3. Implement the endpoints listed at the top of `src/api/client.js`. Auth is cookie-based: your `/auth/login` response should set an `httpOnly`, `Secure`, `SameSite=Lax` (or `Strict`) session cookie; the frontend never touches a token directly. This is deliberate — token storage in `localStorage`/`sessionStorage` is readable by any script that gets injected into the page (e.g. via a compromised dependency), which is an unacceptable risk for a clinical app carrying PHI.
4. Your API must send CORS headers allowing the frontend's origin with `Access-Control-Allow-Credentials: true` if it's on a different domain than the frontend (see hosting note below).

## Deployment (Vercel/Netlify frontend + separate API host)

Since you're hosting the frontend on Vercel/Netlify and the API elsewhere:

- **Same-domain cookies are easiest.** Put the API behind a subdomain of your main domain (e.g. `api.medimate.com` alongside `app.medimate.com`) and set the session cookie's `Domain` to the parent domain, or proxy `/api/*` through Vercel to your API host using `vercel.json` rewrites (`vercel.json` already rewrites SPA routes — add an API rewrite here if you go this route: `{ "source": "/api/(.*)", "destination": "https://your-api-host/$1" }`).
- **Cross-domain cookies (no proxy)** require `SameSite=None; Secure` on the session cookie, and the browser must allow third-party cookies — increasingly restricted, so avoid this if you can.
- `vercel.json` in this repo already sets `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and a restrictive `Permissions-Policy`. Add a `Content-Security-Policy` header once you know your exact script/style/API origins.

## Security notes specific to this app

- No `localStorage`/`sessionStorage` is used anywhere — session state lives only in React memory for the current page load and is re-established via `/auth/me` on refresh.
- Every user-supplied string (drug names, guideline queries, transcript text) is rendered via React's default text interpolation (no `dangerouslySetInnerHTML`), so there's no XSS path through clinical free-text.
- The audio upload path validates file type and a 25MB size cap client-side; **the backend must re-validate both**, since client-side checks are a UX convenience, not a security boundary.
- A persistent "AI-generated draft, must be clinician-reviewed" banner shows on every generated note — keep this even if you redesign the UI; it's a liability and safety control, not decoration.

## What's intentionally not in this package

There is no backend here. `src/api/mock.js` is a stand-in so the UI is fully clickable and demoable. When you're ready, I can build the FastAPI + RAG (ChromaDB) + Whisper + Llama 3 (Groq) service that implements the contract in `src/api/client.js`.
