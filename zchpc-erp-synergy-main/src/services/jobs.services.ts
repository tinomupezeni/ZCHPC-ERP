import { JobListing } from "@/types/postJob";
import apiClient from "./apiClient";

// Type definitions for applications
interface Candidate {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  resume: string | null;
  notes: string | null;
}

interface JobApplication {
  id: number;
  job: number;
  job_title: string;
  candidate: Candidate;
  applied_on: string;
  status: string;
}


export const getJobs = async (statusFilter?: string) => {
  let url = "/recruitment/jobs/";
  if (statusFilter && statusFilter !== "All") {
    url += `?status=${statusFilter}`;
  }
  const response = await apiClient.get<JobListing[]>(url);
  return response.data;
};

/**
 * Get a single job details
 */
export const getJob = async (id: number | string) => {
  const response = await apiClient.get<JobListing>(`/recruitment/jobs/${id}/`);
  return response.data;
};

/**
 * Create a new job posting
 */
export const createJob = async (data: JobListing) => {
  const response = await apiClient.post<JobListing>("/recruitment/jobs/", data);
  return response.data;
};

/**
 * Update an existing job (Partial update supported)
 */
export const updateJob = async (id: number | string, data: Partial<JobListing>) => {
  const response = await apiClient.patch<JobListing>(`/recruitment/jobs/${id}/`, data);
  return response.data;
};

/**
 * Delete a job posting
 */
export const deleteJob = async (id: number | string) => {
  await apiClient.delete(`/recruitment/jobs/${id}/`);
};

// --- Application Services ---

export const getApplications = async (jobId?: number) => {
  if (jobId) {
    // Get applications for a specific job
    const response = await apiClient.get<JobApplication[]>(`/recruitment/jobs/${jobId}/applications/`);
    return response.data;
  }
  // For all applications, we need a different approach - the backend doesn't have a general applications list
  return [];
};

export const updateApplicationStatus = async (id: number, status: string) => {
  const response = await apiClient.patch(`/recruitment/applications/${id}/status/`, { status });
  return response.data;
};