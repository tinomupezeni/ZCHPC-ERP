/**
 * The backend origin this app calls (4a).
 *
 * - VITE_API_URL set: that origin, in every mode.
 * - Vite dev server (import.meta.env.DEV) with no VITE_API_URL: the local
 *   backend, http://localhost:8000 - never production.
 * - Production build with no VITE_API_URL: vite.config.ts's __API_URL__
 *   default (production), unchanged; build-desktop.sh relies on it. DEV is
 *   false in a build, so the localhost branch is dropped from the bundle
 *   (deploy/staging/deploy.sh refuses a bundle containing localhost:8000).
 * - No __API_URL__ at all (vitest, which has no define): same origin.
 */
export function resolveApiOrigin(): string {
  if (typeof __API_URL__ === 'undefined') return '';
  if (import.meta.env.DEV && !import.meta.env.VITE_API_URL) return 'http://localhost:8000';
  return __API_URL__;
}
