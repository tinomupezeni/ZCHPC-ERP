import api from './api';
import type { DashboardSummary } from '@/types/dashboard.types';

export const dashboardService = {
  /**
   * Get dashboard summary data
   */
  async getDashboard(): Promise<DashboardSummary> {
    const response = await api.get<DashboardSummary>('/portal/dashboard/');
    return response.data;
  },
};

export default dashboardService;
