import api from './api';
import type { CreateStoresRequisitionData, StoresRequisition } from '@/types/stores-requisition.types';

export const storesRequisitionService = {
  async getRequests(): Promise<StoresRequisition[]> {
    const response = await api.get<StoresRequisition[]>('/portal/stores-requisitions/');
    return response.data;
  },
  async createRequest(data: CreateStoresRequisitionData): Promise<StoresRequisition> {
    const response = await api.post<StoresRequisition>('/portal/stores-requisitions/', data);
    return response.data;
  },
};

export default storesRequisitionService;
