import api from './api';
import type { CreateFuelRequisitionData, FuelRequisition } from '@/types/fuel-requisition.types';

export const fuelRequisitionService = {
  async getRequests(): Promise<FuelRequisition[]> {
    const response = await api.get<FuelRequisition[]>('/portal/fuel-requisitions/');
    return response.data;
  },
  async createRequest(data: CreateFuelRequisitionData): Promise<FuelRequisition> {
    const response = await api.post<FuelRequisition>('/portal/fuel-requisitions/', data);
    return response.data;
  },
};

export default fuelRequisitionService;
