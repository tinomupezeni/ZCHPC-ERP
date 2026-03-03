import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { ticketService } from '@/services/ticket.service';
import { TicketForm } from '@/components/tickets/TicketForm';
import { TicketsList } from '@/components/tickets/TicketsList';
import { TicketDetail } from '@/components/tickets/TicketDetail';
import type {
  TicketListItem,
  TicketDetail as TicketDetailType,
  TicketSummary,
  TicketCategoryOption,
  TicketPriorityOption,
  TicketStatus,
  TicketCategory,
  TicketPriority,
  CreateTicketData,
} from '@/types/ticket.types';
import {
  MessageSquare,
  Clock,
  CheckCircle,
  AlertTriangle,
  Inbox,
} from 'lucide-react';

function SummaryCard({
  title,
  count,
  icon,
  color,
}: {
  title: string;
  count: number;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{count}</p>
          </div>
          <div className={`p-2 rounded-full ${color}`}>{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export function TicketsPage() {
  const { toast } = useToast();

  // State
  const [tickets, setTickets] = useState<TicketListItem[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<TicketDetailType | null>(null);
  const [summary, setSummary] = useState<TicketSummary | null>(null);
  const [categories, setCategories] = useState<TicketCategoryOption[]>([]);
  const [priorities, setPriorities] = useState<TicketPriorityOption[]>([]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<TicketStatus | ''>('');
  const [categoryFilter, setCategoryFilter] = useState<TicketCategory | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority | ''>('');

  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Fetch tickets
  const fetchTickets = useCallback(async () => {
    try {
      const params: {
        status?: TicketStatus;
        category?: TicketCategory;
        priority?: TicketPriority;
      } = {};

      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (priorityFilter) params.priority = priorityFilter;

      const data = await ticketService.getTickets(params);
      setTickets(data);
    } catch (error) {
      console.error('Error fetching tickets:', error);
      toast({
        title: 'Error',
        description: 'Failed to load tickets',
        variant: 'destructive',
      });
    }
  }, [statusFilter, categoryFilter, priorityFilter, toast]);

  // Fetch summary
  const fetchSummary = async () => {
    try {
      const data = await ticketService.getSummary();
      setSummary(data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  // Fetch categories and priorities
  const fetchOptions = async () => {
    try {
      const [categoriesData, prioritiesData] = await Promise.all([
        ticketService.getCategories(),
        ticketService.getPriorities(),
      ]);
      setCategories(categoriesData);
      setPriorities(prioritiesData);
    } catch (error) {
      console.error('Error fetching options:', error);
    }
  };

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([fetchTickets(), fetchSummary(), fetchOptions()]);
      setIsLoading(false);
    };
    loadData();
  }, []);

  // Reload tickets when filters change
  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  // Create ticket
  const handleCreateTicket = async (data: CreateTicketData) => {
    setIsSubmitting(true);
    try {
      await ticketService.createTicket(data);
      toast({
        title: 'Success',
        description: 'Ticket created successfully',
      });
      await Promise.all([fetchTickets(), fetchSummary()]);
    } catch (error) {
      console.error('Error creating ticket:', error);
      toast({
        title: 'Error',
        description: 'Failed to create ticket',
        variant: 'destructive',
      });
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  // View ticket details
  const handleViewDetails = async (ticket: TicketListItem) => {
    try {
      const detail = await ticketService.getTicket(ticket.id);
      setSelectedTicket(detail);
      setIsDetailOpen(true);
    } catch (error) {
      console.error('Error fetching ticket details:', error);
      toast({
        title: 'Error',
        description: 'Failed to load ticket details',
        variant: 'destructive',
      });
    }
  };

  // Add message
  const handleAddMessage = async (message: string, attachment?: File) => {
    if (!selectedTicket) return;

    setIsSubmitting(true);
    try {
      await ticketService.addMessage(selectedTicket.id, { message, attachment });
      // Refresh ticket details
      const detail = await ticketService.getTicket(selectedTicket.id);
      setSelectedTicket(detail);
      toast({
        title: 'Success',
        description: 'Message sent successfully',
      });
      await fetchTickets();
    } catch (error) {
      console.error('Error adding message:', error);
      toast({
        title: 'Error',
        description: 'Failed to send message',
        variant: 'destructive',
      });
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  // Close ticket
  const handleCloseTicket = async () => {
    if (!selectedTicket) return;

    setIsSubmitting(true);
    try {
      const response = await ticketService.closeTicket(selectedTicket.id);
      setSelectedTicket(response.ticket);
      toast({
        title: 'Success',
        description: 'Ticket closed successfully',
      });
      await Promise.all([fetchTickets(), fetchSummary()]);
    } catch (error) {
      console.error('Error closing ticket:', error);
      toast({
        title: 'Error',
        description: 'Failed to close ticket',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reopen ticket
  const handleReopenTicket = async () => {
    if (!selectedTicket) return;

    setIsSubmitting(true);
    try {
      const response = await ticketService.reopenTicket(selectedTicket.id);
      setSelectedTicket(response.ticket);
      toast({
        title: 'Success',
        description: 'Ticket reopened successfully',
      });
      await Promise.all([fetchTickets(), fetchSummary()]);
    } catch (error) {
      console.error('Error reopening ticket:', error);
      toast({
        title: 'Error',
        description: 'Failed to reopen ticket',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle filter changes
  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value === 'all' ? '' : value as TicketStatus);
  };

  const handleCategoryFilterChange = (value: string) => {
    setCategoryFilter(value === 'all' ? '' : value as TicketCategory);
  };

  const handlePriorityFilterChange = (value: string) => {
    setPriorityFilter(value === 'all' ? '' : value as TicketPriority);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessageSquare className="h-6 w-6" />
          Support Tickets
        </h1>
        <p className="text-muted-foreground">
          Create and manage your support requests
        </p>
      </div>

      {/* Summary Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      ) : summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <SummaryCard
            title="Total"
            count={summary.total_tickets}
            icon={<Inbox className="h-5 w-5 text-gray-600" />}
            color="bg-gray-100"
          />
          <SummaryCard
            title="Open"
            count={summary.open_tickets}
            icon={<MessageSquare className="h-5 w-5 text-blue-600" />}
            color="bg-blue-100"
          />
          <SummaryCard
            title="In Progress"
            count={summary.in_progress_tickets}
            icon={<Clock className="h-5 w-5 text-yellow-600" />}
            color="bg-yellow-100"
          />
          <SummaryCard
            title="Resolved"
            count={summary.resolved_tickets}
            icon={<CheckCircle className="h-5 w-5 text-green-600" />}
            color="bg-green-100"
          />
          <SummaryCard
            title="Closed"
            count={summary.closed_tickets}
            icon={<AlertTriangle className="h-5 w-5 text-gray-600" />}
            color="bg-gray-100"
          />
        </div>
      )}

      {/* Create Ticket Form */}
      <TicketForm
        categories={categories}
        priorities={priorities}
        onSubmit={handleCreateTicket}
        isSubmitting={isSubmitting}
      />

      {/* Tickets List */}
      <TicketsList
        tickets={tickets}
        isLoading={isLoading}
        statusFilter={statusFilter}
        categoryFilter={categoryFilter}
        priorityFilter={priorityFilter}
        onStatusFilterChange={handleStatusFilterChange}
        onCategoryFilterChange={handleCategoryFilterChange}
        onPriorityFilterChange={handlePriorityFilterChange}
        onViewDetails={handleViewDetails}
        onRefresh={fetchTickets}
      />

      {/* Ticket Detail Modal */}
      <TicketDetail
        ticket={selectedTicket}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onAddMessage={handleAddMessage}
        onCloseTicket={handleCloseTicket}
        onReopenTicket={handleReopenTicket}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}

export default TicketsPage;
