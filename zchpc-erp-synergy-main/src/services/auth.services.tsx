
import { User } from '../types/index';
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

