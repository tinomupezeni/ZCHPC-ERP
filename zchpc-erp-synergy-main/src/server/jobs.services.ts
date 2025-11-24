import { apiClient } from "./apiClient";

// --- Types ---

export interface JobListing {
  id?: number;
  title: string;
  
  // Department: Read as string, Write as ID
  department?: string; 
  department_id?: number | string; 
  
  status: "Open" | "Closed" | "Draft" | "Pending";
  location: string;
  
  // Detailed Fields
  description: string;
  responsibilities: string[]; // Handled as JSON list by backend
  qualifications: string[];   // Handled as JSON list by backend
  notes?: string;

  // Mapped Fields (Backend Serializer maps these camelCase keys to snake_case columns)
  postedDate: string;       // Maps to posted_date
  salaryRange: string;      // Maps to salary_range
  contactEmail: string;     // Maps to contact_email
  applicationProcess: string; // Maps to application_process
  
  // Read Only
  applicants?: number;
  created_at?: string;
}

export interface JobApplication {
  id?: number;
  job: number; // Job ID
  candidate_name: string; // You might need to expand this based on your Candidate model
  status: "Pending" | "Shortlisted" | "Interview" | "Offered" | "Hired" | "Rejected";
  applied_on: string;
}

// --- Job Services ---

/**
 * Fetch all job listings.
 * Can filter by status: getJobs('Open')
 */
export const getJobs = async (statusFilter?: string) => {
  let url = "/hr/jobs/";
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
  const response = await apiClient.get<JobListing>(`/hr/jobs/${id}/`);
  console.log(response);
  
  return response.data;
};

/**
 * Create a new job posting
 */
export const createJob = async (data: JobListing) => {
  const response = await apiClient.post<JobListing>("/hr/jobs/", data);
  return response.data;
};

/**
 * Update an existing job (Partial update supported)
 */
export const updateJob = async (id: number | string, data: Partial<JobListing>) => {
  const response = await apiClient.patch<JobListing>(`/hr/jobs/${id}/`, data);
  return response.data;
};

/**
 * Delete a job posting
 */
export const deleteJob = async (id: number | string) => {
  await apiClient.delete(`/hr/jobs/${id}/`);
};

// --- Application Services ---

export const getApplications = async (jobId?: number) => {
  let url = "/hr/applications/";
  if (jobId) {
    url += `?job=${jobId}`;
  }
  const response = await apiClient.get<JobApplication[]>(url);
  return response.data;
};

export const updateApplicationStatus = async (id: number, status: string) => {
  const response = await apiClient.patch(`/hr/applications/${id}/`, { status });
  return response.data;
};