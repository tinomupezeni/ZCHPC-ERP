// This type is for your Audit Log
export interface AuditLog {
  id: number;
  user: string | null;
  username_attempted: string;
  event_type: string;
  timestamp: string;
  ip_address: string;
}

// This is the main type for your dashboard
export interface DashboardData {
  metrics: {
    total_employees: number;
    total_attendees: number;
  };
  charts: {
    employee_distribution: {
      department: string;
      employees: number 
    }[];
    payroll_distribution: {
      employee__department: string;
      total_usd: string;
      total_zig: string;
    }[];
  };
  lists: {
    tasks_due: {
      id: number;
      text: string;
      done: boolean;
      module: string;
      due: string;
    }[];
    recent_activities: AuditLog[];
  };
}

