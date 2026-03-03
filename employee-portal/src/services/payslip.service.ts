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

  /**
   * Download payslip as file
   */
  async downloadPayslip(id: number): Promise<void> {
    const response = await api.get(`/portal/payslips/${id}/download/`, {
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    // Extract filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'payslip.txt';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }

    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default payslipService;
