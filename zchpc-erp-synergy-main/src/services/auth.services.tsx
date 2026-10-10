
import { MeAccess, User } from '../types/index';
import apiClient from './apiClient';

export const login = async (email: string, password: string): Promise<User> => {
  const response = await apiClient.post('/auth/token/', { email, password });
  const { access, refresh, user } = response.data;

  if (access && refresh) {
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
  }
  return user;
};

// New "Me" endpoint logic
export const getProfile = async (): Promise<User | null> => {
  try {
    // Note: Since your router is DefaultRouter and registered 'users', 
    // you might need a custom action in Django for /api/auth/users/me/
    const response = await apiClient.get('/auth/users/me/'); 
    return response.data;
  } catch (error) {
    return null;
  }
};

// Throws on failure: the caller tells 403 PASSWORD_CHANGE_REQUIRED apart.
export const getMyAccess = async (): Promise<MeAccess> => {
  const response = await apiClient.get('/auth/users/me/access/');
  return response.data;
};

// Logout: the server blacklists the refresh token if it is the caller's and
// always answers 200. Goes through apiClient so an expired access token is
// refreshed first.
export const revokeRefreshToken = async (): Promise<void> => {
  const refresh = localStorage.getItem('refreshToken');
  if (!refresh) return;
  await apiClient.post('/auth/logout/', { refresh });
};

export const clearTokens = () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
};

export const addUser = (payload) => {
  return apiClient.post("/auth/users/", payload);
};

export const getUsers = () => {
    return apiClient.get("/auth/users/")
}

