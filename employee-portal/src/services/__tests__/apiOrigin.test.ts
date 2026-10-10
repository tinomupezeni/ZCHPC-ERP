import { afterEach, describe, expect, it, vi } from 'vitest';
import { resolveApiOrigin } from '../apiOrigin';

// 4a: localhost only on the Vite dev server; a build keeps the production default.
describe('resolveApiOrigin', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('uses VITE_API_URL when it is set, also on the dev server', () => {
    vi.stubGlobal('__API_URL__', 'https://staging.example');
    vi.stubEnv('DEV', true);
    vi.stubEnv('VITE_API_URL', 'https://staging.example');
    expect(resolveApiOrigin()).toBe('https://staging.example');
  });

  it('falls back to localhost on the dev server when VITE_API_URL is unset', () => {
    vi.stubGlobal('__API_URL__', 'https://zchpcerp.zchpc.ac.zw');
    vi.stubEnv('DEV', true);
    vi.stubEnv('VITE_API_URL', '');
    expect(resolveApiOrigin()).toBe('http://localhost:8000');
  });

  it('keeps the production default in a build when VITE_API_URL is unset', () => {
    vi.stubGlobal('__API_URL__', 'https://zchpcerp.zchpc.ac.zw');
    vi.stubEnv('DEV', false);
    vi.stubEnv('VITE_API_URL', '');
    expect(resolveApiOrigin()).toBe('https://zchpcerp.zchpc.ac.zw');
  });

  it('is same-origin when __API_URL__ is not defined (vitest)', () => {
    expect(resolveApiOrigin()).toBe('');
  });
});
