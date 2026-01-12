import apiClient  from './apiClient';
import { DashboardData } from '../types/admin'; // Import the new type
import { toast } from 'sonner';

/**
 * Fetches the aggregated data for the admin dashboard.
 */
export const getAdminDashboardData = async (): Promise<DashboardData> => {
  try {
    // 1. Use the correct URL and return type
    const response = await apiClient.get<DashboardData>('/admin/dashboard/');
    
    // 2. Return the whole data object
    console.log(response);
    
    return response.data;

  } catch (error: any) {
    console.error("Failed to fetch dashboard data:", error);
    toast.error("Failed to Load Dashboard", {
      description: error.message || "Could not retrieve data from the server.",
    });
    // Re-throw the error so the component can handle loading/error states
    throw error;
  }
};