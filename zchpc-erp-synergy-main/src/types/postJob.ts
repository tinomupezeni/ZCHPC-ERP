export type JobListing = {
  id?: number;
  title: string;
  department_id: string | number;
  position_id: string | number;
  status: string;
  postedDate: string;
  description: string;
  qualifications: string[];
  applicationProcess: string;
  location: string;
  salaryRange?: string;  // Legacy field
  // Multi-currency salary fields
  salaryUsdMin?: number | string | null;
  salaryUsdMax?: number | string | null;
  salaryZigMin?: number | string | null;
  salaryZigMax?: number | string | null;
  contactEmail: string;
  responsibilities: string[];
  notes?: string;
  department?: any; // To handle nested data from backend
  reportsTo: string;       // e.g., "ZCHPC Director"
  competencies: string[];  // Array for the Competencies list
  note?: string;           // Made optional with ?
  isInternal: boolean;     // New: Internal staff only flag
};

export interface PostJobModalProps {
  isOpen: boolean;
  job: JobListing | null;
  onClose: () => void;
  onSave: (updated: JobListing) => void;
}

export interface Option {
  id: number;
  name?: string;
  title?: string;
  department_id?: string | number; // For positions that belong to departments
}