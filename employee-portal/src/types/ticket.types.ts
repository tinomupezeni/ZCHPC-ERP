export type TicketCategory = 'IT' | 'HR' | 'Facilities' | 'Finance' | 'Other';

export type TicketPriority = 'Low' | 'Medium' | 'High' | 'Urgent';

export type TicketStatus = 'Open' | 'In Progress' | 'Waiting' | 'Resolved' | 'Closed';

export interface TicketMessage {
  id: number;
  message: string;
  attachment: string | null;
  sender_name: string;
  is_own_message: boolean;
  created_at: string;
}

export interface TicketListItem {
  id: number;
  ticket_number: string;
  category: TicketCategory;
  priority: TicketPriority;
  subject: string;
  status: TicketStatus;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
  can_close: boolean;
  can_reopen: boolean;
}

export interface TicketDetail {
  id: number;
  ticket_number: string;
  category: TicketCategory;
  priority: TicketPriority;
  subject: string;
  description: string;
  status: TicketStatus;
  assigned_to_name: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  closed_at: string | null;
  messages: TicketMessage[];
  can_close: boolean;
  can_reopen: boolean;
}

export interface CreateTicketData {
  category: TicketCategory;
  priority: TicketPriority;
  subject: string;
  description: string;
}

export interface CreateTicketMessageData {
  message: string;
  attachment?: File;
}

export interface TicketSummary {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
}

export interface TicketCategoryOption {
  value: TicketCategory;
  label: string;
}

export interface TicketPriorityOption {
  value: TicketPriority;
  label: string;
}
