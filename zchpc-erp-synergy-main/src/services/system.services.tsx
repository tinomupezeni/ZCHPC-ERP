import apiClient from './apiClient';

export interface SystemModule {
  id: number;
  identifier: string;
  name: string;
  description: string;
  is_active: boolean;
  dependencies: string[];
}

export const getModules = async (): Promise<SystemModule[]> => {
  const response = await apiClient.get('/auth/modules/');
  return response.data;
};

export const getActiveModules = async (): Promise<SystemModule[]> => {
  const response = await apiClient.get('/auth/modules/active/');
  return response.data;
};

export const installModule = async (identifier: string): Promise<SystemModule> => {
  const response = await apiClient.post(`/auth/modules/${identifier}/install/`);
  return response.data;
};

export const uninstallModule = async (identifier: string): Promise<SystemModule> => {
  const response = await apiClient.post(`/auth/modules/${identifier}/uninstall/`);
  return response.data;
};
