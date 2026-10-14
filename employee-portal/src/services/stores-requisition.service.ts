import api from './api';
import type { CreateStoresRequisitionData, StoresRequisition } from '@/types/stores-requisition.types';

export const storesRequisitionService = {
  async getRequests(): Promise<StoresRequisition[]> {
    const response = await api.get<StoresRequisition[]>('/portal/stores-requisitions/');
    return response.data;
  },
  async getInbox(): Promise<StoresRequisition[]> {
    const response = await api.get<StoresRequisition[]>('/procurement/stores-requisitions/inbox/');
    return response.data;
  },
  async approve(id: number): Promise<void> {
    await api.post(`/procurement/stores-requisitions/${id}/approve/`);
  },
  async reject(id: number, reason: string): Promise<void> {
    await api.post(`/procurement/stores-requisitions/${id}/reject/`, { reason });
  },
  async createRequest(data: CreateStoresRequisitionData): Promise<StoresRequisition> {
    const response = await api.post<StoresRequisition>('/portal/stores-requisitions/', data);
    return response.data;
  },
};

export default storesRequisitionService;
