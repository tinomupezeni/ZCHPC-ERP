import api from './api';
import type { CreateFuelRequisitionData, FuelRequisition } from '@/types/fuel-requisition.types';

export const fuelRequisitionService = {
  async getRequests(): Promise<FuelRequisition[]> {
    const response = await api.get<FuelRequisition[]>('/portal/fuel-requisitions/');
    return response.data;
  },
  async getInbox(): Promise<FuelRequisition[]> {
    const response = await api.get<FuelRequisition[]>('/procurement/fuel-requisitions/inbox/');
    return response.data;
  },
  async approve(id: number): Promise<void> {
    await api.post(`/procurement/fuel-requisitions/${id}/approve/`);
  },
  async reject(id: number, reason: string): Promise<void> {
    await api.post(`/procurement/fuel-requisitions/${id}/reject/`, { reason });
  },
  async createRequest(data: CreateFuelRequisitionData): Promise<FuelRequisition> {
    const response = await api.post<FuelRequisition>('/portal/fuel-requisitions/', data);
    return response.data;
  },
};

export default fuelRequisitionService;
