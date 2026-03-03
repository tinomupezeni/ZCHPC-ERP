import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  MessageSquare,
  Clock,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  Loader2,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { TicketListItem } from '@/types/ticket.types';

interface TicketCardProps {
  ticket: TicketListItem;
  onViewDetails: (ticket: TicketListItem) => void;
}

const statusConfig: Record<
  string,
  { color: string; icon: React.ReactNode }
> = {
  Open: {
    color: 'bg-blue-100 text-blue-800',
    icon: <HelpCircle className="h-3 w-3" />,
  },
  'In Progress': {
    color: 'bg-yellow-100 text-yellow-800',
    icon: <Loader2 className="h-3 w-3" />,
  },
  Waiting: {
    color: 'bg-purple-100 text-purple-800',
    icon: <Clock className="h-3 w-3" />,
  },
  Resolved: {
    color: 'bg-green-100 text-green-800',
    icon: <CheckCircle className="h-3 w-3" />,
  },
  Closed: {
    color: 'bg-gray-100 text-gray-800',
    icon: <CheckCircle className="h-3 w-3" />,
  },
};

const priorityConfig: Record<string, string> = {
  Low: 'bg-gray-100 text-gray-700',
  Medium: 'bg-blue-100 text-blue-700',
  High: 'bg-orange-100 text-orange-700',
  Urgent: 'bg-red-100 text-red-700',
};

const categoryConfig: Record<string, string> = {
  IT: 'bg-indigo-100 text-indigo-700',
  HR: 'bg-pink-100 text-pink-700',
  Facilities: 'bg-teal-100 text-teal-700',
  Finance: 'bg-emerald-100 text-emerald-700',
  Other: 'bg-gray-100 text-gray-700',
};

export function TicketCard({ ticket, onViewDetails }: TicketCardProps) {
  const status = statusConfig[ticket.status] || statusConfig.Open;
  const priorityClass = priorityConfig[ticket.priority] || priorityConfig.Medium;
  const categoryClass = categoryConfig[ticket.category] || categoryConfig.Other;

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => onViewDetails(ticket)}
    >
      <CardContent className="p-4">
        {/* Header with ticket number and status */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground font-mono">
              #{ticket.ticket_number}
            </span>
            <Badge variant="outline" className={categoryClass}>
              {ticket.category}
            </Badge>
          </div>
          <Badge variant="outline" className={`${status.color} flex items-center gap-1`}>
            {status.icon}
            {ticket.status}
          </Badge>
        </div>

        {/* Subject */}
        <h3 className="font-medium text-sm mb-2 line-clamp-2">{ticket.subject}</h3>

        {/* Meta info */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-3">
            <Badge variant="outline" className={priorityClass}>
              {ticket.priority === 'Urgent' && (
                <AlertCircle className="h-3 w-3 mr-1" />
              )}
              {ticket.priority}
            </Badge>
            <span className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              {ticket.message_count}
            </span>
          </div>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}
          </span>
        </div>

        {/* Last activity */}
        {ticket.last_message_at && (
          <p className="text-xs text-muted-foreground mt-2">
            Last reply{' '}
            {formatDistanceToNow(new Date(ticket.last_message_at), {
              addSuffix: true,
            })}
          </p>
        )}

        {/* View button */}
        <Button
          variant="ghost"
          size="sm"
          className="w-full mt-3 justify-between"
          onClick={(e) => {
            e.stopPropagation();
            onViewDetails(ticket);
          }}
        >
          View Details
          <ChevronRight className="h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );
}

export default TicketCard;
