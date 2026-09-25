export interface Job {
  id: number;
  title: string;
  department: string | null;
  location: string;
  employment_type: string;
  description: string;
  requirements: string;
  responsibilities?: string;
  salary_min: number | null;
  salary_max: number | null;
  closing_date: string | null;
  posted_date: string;
  is_internal: boolean;
  application_count?: number;
}

export interface JobsListResponse {
  jobs: Job[];
  total: number;
}

export interface JobApplicationFormData {
  job_id: number;
  id_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address: string;
  date_of_birth: string;
  qualifications: string;
  experience: string;
  cover_letter: string;
  resume?: File;
}

// The public careers API discloses nothing about the applicant's identity:
// check-application answers only has_applied, and neither the submission
// receipt nor the status lookup carries a name or email.
export interface ApplicationCheckResponse {
  has_applied: boolean;
}

export interface ApplicationReceipt {
  id: number;
  job_id: number;
  job_title: string;
  status: ApplicationStatus['status'];
  applied_at: string;
  updated_at: string;
}

export interface ApplicationSubmitResponse {
  success: boolean;
  message: string;
  application: ApplicationReceipt;
}

export interface ApplicationStatus {
  job_id: number;
  job_title: string;
  applied_at: string;
  status: 'Pending' | 'Shortlisted' | 'Interview' | 'Offered' | 'Hired' | 'Rejected';
}

// An unknown ID number returns an empty list, exactly like an ID with no
// applications.
export type ApplicationStatusResponse = ApplicationStatus[];
