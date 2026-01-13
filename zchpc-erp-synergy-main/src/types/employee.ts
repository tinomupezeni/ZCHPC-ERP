import { LucideIcon } from "lucide-react";

export interface Employee {
  id: string;
  first_name: string;
  surname: string;
  email: string;
  phone: string;
  position: string;
  position_id?: number;
  department: string;
  department_id?: number;
  is_active: boolean;
  date_joined: string;
  leave_days_entitled?: number;
  deductions?: Array<{ name: string; amount: number }>;
  [key: string]: any; // For other dynamic fields
}

export interface DropdownOption {
  id: string | number;
  name?: string;
  title?: string;
  label?: string;
  value?: string | number;
}

export interface FieldProps {
  icon?: LucideIcon;
  label: string;
  name: string;
  type?: string;
  options?: DropdownOption[] | null;
}