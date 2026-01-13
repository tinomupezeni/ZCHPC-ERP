export interface Deduction {
  id: string | number;
  name: string;
}

export interface EmployeeFormState {
  firstname: string;
  surname: string;
  nationalId: string;
  dob: string;
  gender: string;
  maritalStatus: string;
  email: string;
  phone: string;
  bankName: string;
  accountNumber: string;
  payFrequency: string;
  employeeType: string;
  leaveDays: number;
  pensionScheme: string;
  position: string;
  department: string;
  usd_salary: string;
  zig_salary: string;
  contractFrom: string;
  contractTo: string;
  emergencyContactName: string;
  emergencyContactPhone: string;
  emergencyContactRelationship: string;
  selectedDeductions: Deduction[];
}

export interface Department {
  id: string | number;
  name: string;
}

export interface Position {
  id: string | number;
  title: string;
}