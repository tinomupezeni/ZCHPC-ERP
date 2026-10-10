import api from './api';
import type {
  PayslipsResponse,
  PayslipDetail,
  PayslipYearSummary,
} from '@/types/payslip.types';

export const payslipService = {
  /**
   * Get list of payslips
   */
  async getPayslips(year?: number): Promise<PayslipsResponse> {
    const response = await api.get<PayslipsResponse>('/portal/payslips/', {
      params: year ? { year } : undefined,
    });
    return response.data;
  },

  /**
   * Get payslip details
   */
  async getPayslip(id: number): Promise<PayslipDetail> {
    const response = await api.get<PayslipDetail>(`/portal/payslips/${id}/`);
    return response.data;
  },

  /**
   * Get yearly summary
   */
  async getYearSummary(year?: number): Promise<PayslipYearSummary> {
    const response = await api.get<PayslipYearSummary>('/portal/payslips/summary/', {
      params: year ? { year } : undefined,
    });
    return response.data;
  },
};

export default payslipService;
