import api from './api';
import type {
  TicketListItem,
  TicketDetail,
  CreateTicketData,
  CreateTicketMessageData,
  TicketMessage,
  TicketSummary,
  TicketCategoryOption,
  TicketPriorityOption,
  TicketStatus,
  TicketCategory,
  TicketPriority,
} from '@/types/ticket.types';

export const ticketService = {
  /**
   * Get list of tickets
   */
  async getTickets(params?: {
    status?: TicketStatus;
    category?: TicketCategory;
    priority?: TicketPriority;
  }): Promise<TicketListItem[]> {
    const response = await api.get<TicketListItem[]>('/portal/tickets/', {
      params,
    });
    return response.data;
  },

  /**
   * Get ticket details
   */
  async getTicket(id: number): Promise<TicketDetail> {
    const response = await api.get<TicketDetail>(`/portal/tickets/${id}/`);
    return response.data;
  },

  /**
   * Create a new ticket
   */
  async createTicket(data: CreateTicketData): Promise<TicketDetail> {
    const response = await api.post<TicketDetail>('/portal/tickets/', data);
    return response.data;
  },

  /**
   * Add a message to a ticket
   */
  async addMessage(
    ticketId: number,
    data: CreateTicketMessageData
  ): Promise<TicketMessage> {
    const formData = new FormData();
    formData.append('message', data.message);
    if (data.attachment) {
      formData.append('attachment', data.attachment);
    }

    const response = await api.post<TicketMessage>(
      `/portal/tickets/${ticketId}/message/`,
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
   * Close a ticket
   */
  async closeTicket(id: number): Promise<{ detail: string; ticket: TicketDetail }> {
    const response = await api.post<{ detail: string; ticket: TicketDetail }>(
      `/portal/tickets/${id}/close/`
    );
    return response.data;
  },

  /**
   * Reopen a ticket
   */
  async reopenTicket(id: number): Promise<{ detail: string; ticket: TicketDetail }> {
    const response = await api.post<{ detail: string; ticket: TicketDetail }>(
      `/portal/tickets/${id}/reopen/`
    );
    return response.data;
  },

  /**
   * Get ticket summary
   */
  async getSummary(): Promise<TicketSummary> {
    const response = await api.get<TicketSummary>('/portal/tickets/summary/');
    return response.data;
  },

  /**
   * Get available categories
   */
  async getCategories(): Promise<TicketCategoryOption[]> {
    const response = await api.get<TicketCategoryOption[]>('/portal/tickets/categories/');
    return response.data;
  },

  /**
   * Get available priorities
   */
  async getPriorities(): Promise<TicketPriorityOption[]> {
    const response = await api.get<TicketPriorityOption[]>('/portal/tickets/priorities/');
    return response.data;
  },
};

export default ticketService;
