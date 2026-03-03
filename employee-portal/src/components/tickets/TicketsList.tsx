import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { MessageSquare, Filter, RefreshCw } from 'lucide-react';
import { TicketCard } from './TicketCard';
import type {
  TicketListItem,
  TicketStatus,
  TicketCategory,
  TicketPriority,
} from '@/types/ticket.types';

interface TicketsListProps {
  tickets: TicketListItem[];
  isLoading: boolean;
  statusFilter: TicketStatus | '';
  categoryFilter: TicketCategory | '';
  priorityFilter: TicketPriority | '';
  onStatusFilterChange: (value: TicketStatus | '') => void;
  onCategoryFilterChange: (value: TicketCategory | '') => void;
  onPriorityFilterChange: (value: TicketPriority | '') => void;
  onViewDetails: (ticket: TicketListItem) => void;
  onRefresh: () => void;
}

const statusOptions: { value: TicketStatus | ''; label: string }[] = [
  { value: '', label: 'All Status' },
  { value: 'Open', label: 'Open' },
  { value: 'In Progress', label: 'In Progress' },
  { value: 'Waiting', label: 'Waiting' },
  { value: 'Resolved', label: 'Resolved' },
  { value: 'Closed', label: 'Closed' },
];

const categoryOptions: { value: TicketCategory | ''; label: string }[] = [
  { value: '', label: 'All Categories' },
  { value: 'IT', label: 'IT Support' },
  { value: 'HR', label: 'Human Resources' },
  { value: 'Facilities', label: 'Facilities' },
  { value: 'Finance', label: 'Finance' },
  { value: 'Other', label: 'Other' },
];

const priorityOptions: { value: TicketPriority | ''; label: string }[] = [
  { value: '', label: 'All Priorities' },
  { value: 'Low', label: 'Low' },
  { value: 'Medium', label: 'Medium' },
  { value: 'High', label: 'High' },
  { value: 'Urgent', label: 'Urgent' },
];

export function TicketsList({
  tickets,
  isLoading,
  statusFilter,
  categoryFilter,
  priorityFilter,
  onStatusFilterChange,
  onCategoryFilterChange,
  onPriorityFilterChange,
  onViewDetails,
  onRefresh,
}: TicketsListProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            My Tickets
          </CardTitle>
          <Button variant="outline" size="sm" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2 mt-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
          </div>
          <Select
            value={statusFilter}
            onValueChange={(v) => onStatusFilterChange(v as TicketStatus | '')}
          >
            <SelectTrigger className="w-[140px] h-8">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {statusOptions.map((opt) => (
                <SelectItem key={opt.value || 'all'} value={opt.value || 'all'}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={categoryFilter}
            onValueChange={(v) => onCategoryFilterChange(v as TicketCategory | '')}
          >
            <SelectTrigger className="w-[140px] h-8">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              {categoryOptions.map((opt) => (
                <SelectItem key={opt.value || 'all'} value={opt.value || 'all'}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={priorityFilter}
            onValueChange={(v) => onPriorityFilterChange(v as TicketPriority | '')}
          >
            <SelectTrigger className="w-[140px] h-8">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              {priorityOptions.map((opt) => (
                <SelectItem key={opt.value || 'all'} value={opt.value || 'all'}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        ) : tickets.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No tickets found</p>
            <p className="text-sm">
              {statusFilter || categoryFilter || priorityFilter
                ? 'Try adjusting your filters'
                : 'Create your first support ticket above'}
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {tickets.map((ticket) => (
              <TicketCard
                key={ticket.id}
                ticket={ticket}
                onViewDetails={onViewDetails}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TicketsList;
