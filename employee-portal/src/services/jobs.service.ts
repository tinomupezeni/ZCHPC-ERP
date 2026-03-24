import axios from 'axios';
import type {
  Job,
  JobsListResponse,
  JobApplicationFormData,
  ApplicationCheckResponse,
  ApplicationSubmitResponse,
  ApplicationStatusResponse,
} from '@/types/jobs.types';

const API_URL = import.meta.env.VITE_API_URL || '';

// Create axios instance without auth for public endpoints
const publicApi = axios.create({
  baseURL: `${API_URL}/portal/public`,
});

export const jobsService = {
  /**
   * Get all open jobs
   */
  async getJobs(): Promise<Job[] | JobsListResponse> {
    const response = await publicApi.get<Job[] | JobsListResponse>('/jobs/');
    return response.data;
  },

  /**
   * Get a specific job by ID
   */
  async getJob(id: number): Promise<Job> {
    const response = await publicApi.get<Job>(`/jobs/${id}/`);
    return response.data;
  },

  /**
   * Check if a candidate has already applied for a job
   */
  async checkApplication(
    idNumber: string,
    jobId: number
  ): Promise<ApplicationCheckResponse> {
    const response = await publicApi.post<ApplicationCheckResponse>(
      '/jobs/check-application/',
      {
        id_number: idNumber,
        job_id: jobId,
      }
    );
    return response.data;
  },

  /**
   * Submit a job application
   */
  async submitApplication(
    data: JobApplicationFormData
  ): Promise<ApplicationSubmitResponse> {
    const formData = new FormData();

    formData.append('job_id', data.job_id.toString());
    formData.append('id_number', data.id_number);
    formData.append('first_name', data.first_name);
    formData.append('last_name', data.last_name);
    formData.append('email', data.email);
    formData.append('phone', data.phone);
    formData.append('address', data.address);
    formData.append('date_of_birth', data.date_of_birth);
    formData.append('qualifications', data.qualifications);
    formData.append('experience', data.experience);
    formData.append('cover_letter', data.cover_letter);

    if (data.resume) {
      formData.append('resume', data.resume);
    }

    const response = await publicApi.post<ApplicationSubmitResponse>(
      '/jobs/apply/',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Check application status by ID number
   */
  async getApplicationStatus(
    idNumber: string
  ): Promise<ApplicationStatusResponse> {
    const response = await publicApi.post<ApplicationStatusResponse>(
      '/applications/status/',
      {
        id_number: idNumber,
      }
    );
    return response.data;
  },
};

export default jobsService;
