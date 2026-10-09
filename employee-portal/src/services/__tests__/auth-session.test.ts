import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import axios, { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios';
import api, { getAccessToken, getRefreshToken, setTokens } from '../api';
import { authService } from '../auth.service';

// B3: the portal refreshes at the identity SimpleJWT endpoint (the old
// /portal/auth/refresh/ route never existed), and logout always clears the
// stored tokens.

const REFRESH_URL = '/api/v2/auth/token/refresh/';

const ok = (config: InternalAxiosRequestConfig, data: unknown) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config,
});

const unauthorized = (config: InternalAxiosRequestConfig) =>
  new AxiosError('Unauthorized', 'ERR_BAD_REQUEST', config, null, {
    data: {},
    status: 401,
    statusText: 'Unauthorized',
    headers: {},
    config,
  });

let originalAdapter: typeof api.defaults.adapter;

beforeEach(() => {
  originalAdapter = api.defaults.adapter;
  localStorage.clear();
});

afterEach(() => {
  api.defaults.adapter = originalAdapter;
  vi.restoreAllMocks();
});

describe('portal token refresh', () => {
  it('refreshes an expired access token at /api/v2/auth/token/refresh/ and retries', async () => {
    setTokens('expired-access', 'refresh-1');
    const seen: Array<string | undefined> = [];
    const adapter: AxiosAdapter = async (config) => {
      const auth = String(config.headers?.Authorization ?? '');
      seen.push(auth);
      if (auth === 'Bearer expired-access') throw unauthorized(config);
      return ok(config, { name: 'me' });
    };
    api.defaults.adapter = adapter;
    const refreshPost = vi.spyOn(axios, 'post').mockResolvedValue({ data: { access: 'fresh-access' } });

    const response = await api.get('/portal/auth/me/');

    expect(refreshPost).toHaveBeenCalledTimes(1);
    expect(refreshPost).toHaveBeenCalledWith(REFRESH_URL, { refresh: 'refresh-1' });
    expect(response.data).toEqual({ name: 'me' });
    expect(seen).toEqual(['Bearer expired-access', 'Bearer fresh-access']);
    expect(getAccessToken()).toBe('fresh-access');
    expect(getRefreshToken()).toBe('refresh-1');
  });

  it('authService.refreshToken posts to the identity refresh endpoint', async () => {
    setTokens('access-1', 'refresh-1');
    const urls: Array<string | undefined> = [];
    api.defaults.adapter = async (config) => {
      urls.push(`${config.baseURL ?? ''}|${config.url ?? ''}`);
      return ok(config, { access: 'access-2' });
    };

    const access = await authService.refreshToken();

    expect(access).toBe('access-2');
    expect(urls).toEqual(['/api/v2/|auth/token/refresh/']);
  });
});

describe('portal logout', () => {
  it('sends the refresh token to the portal logout endpoint and clears both tokens', async () => {
    setTokens('access-1', 'refresh-1');
    const calls: Array<{ url?: string; data?: unknown }> = [];
    api.defaults.adapter = async (config) => {
      calls.push({ url: config.url, data: config.data });
      return ok(config, { message: 'Logged out successfully' });
    };

    await authService.logout();

    expect(calls).toEqual([{ url: '/portal/auth/logout/', data: JSON.stringify({ refresh: 'refresh-1' }) }]);
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it('clears both tokens even when the logout request fails', async () => {
    setTokens('access-1', 'refresh-1');
    api.defaults.adapter = async (config) => {
      throw new AxiosError('Network Error', 'ERR_NETWORK', config);
    };

    await expect(authService.logout()).rejects.toBeInstanceOf(AxiosError);

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
});
