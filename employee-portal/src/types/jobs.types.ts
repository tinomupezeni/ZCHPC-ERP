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

export interface ApplicationCheckResponse {
  has_applied: boolean;
  candidate_exists: boolean;
  candidate_name?: string;
}

export interface ApplicationSubmitResponse {
  detail: string;
  application_id: number;
  job_title: string;
  candidate_name: string;
}

export interface ApplicationStatus {
  id: number;
  job_title: string;
  job_department: string | null;
  applied_on: string;
  status: 'Pending' | 'Shortlisted' | 'Interview' | 'Offered' | 'Hired' | 'Rejected';
}

export interface ApplicationStatusResponse {
  candidate_name: string;
  applications: ApplicationStatus[];
  total: number;
}
