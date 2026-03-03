import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  MessageSquare,
  Clock,
  User,
  Paperclip,
  Send,
  Loader2,
  X,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  RefreshCcw,
  Download,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import type { TicketDetail as TicketDetailType, TicketMessage } from '@/types/ticket.types';

interface TicketDetailProps {
  ticket: TicketDetailType | null;
  isOpen: boolean;
  onClose: () => void;
  onAddMessage: (message: string, attachment?: File) => Promise<void>;
  onCloseTicket: () => Promise<void>;
  onReopenTicket: () => Promise<void>;
  isSubmitting: boolean;
}

const statusConfig: Record<
  string,
  { color: string; icon: React.ReactNode; bgColor: string }
> = {
  Open: {
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    icon: <HelpCircle className="h-4 w-4" />,
  },
  'In Progress': {
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    icon: <Loader2 className="h-4 w-4" />,
  },
  Waiting: {
    color: 'text-purple-700',
    bgColor: 'bg-purple-100',
    icon: <Clock className="h-4 w-4" />,
  },
  Resolved: {
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    icon: <CheckCircle className="h-4 w-4" />,
  },
  Closed: {
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    icon: <CheckCircle className="h-4 w-4" />,
  },
};

const priorityConfig: Record<string, string> = {
  Low: 'bg-gray-100 text-gray-700',
  Medium: 'bg-blue-100 text-blue-700',
  High: 'bg-orange-100 text-orange-700',
  Urgent: 'bg-red-100 text-red-700',
};

function MessageBubble({
  message,
  isOwn,
}: {
  message: TicketMessage;
  isOwn: boolean;
}) {
  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg p-3 ${
          isOwn
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        }`}
      >
        <div className="flex items-center gap-2 mb-1">
          <User className="h-3 w-3" />
          <span className="text-xs font-medium">{message.sender_name}</span>
          <span className="text-xs opacity-70">
            {formatDistanceToNow(new Date(message.created_at), {
              addSuffix: true,
            })}
          </span>
        </div>
        <p className="text-sm whitespace-pre-wrap">{message.message}</p>
        {message.attachment && (
          <a
            href={message.attachment}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex items-center gap-1 mt-2 text-xs ${
              isOwn ? 'text-primary-foreground/80 hover:text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Download className="h-3 w-3" />
            View Attachment
          </a>
        )}
      </div>
    </div>
  );
}

export function TicketDetail({
  ticket,
  isOpen,
  onClose,
  onAddMessage,
  onCloseTicket,
  onReopenTicket,
  isSubmitting,
}: TicketDetailProps) {
  const [newMessage, setNewMessage] = useState('');
  const [attachment, setAttachment] = useState<File | null>(null);

  if (!ticket) return null;

  const status = statusConfig[ticket.status] || statusConfig.Open;
  const priorityClass = priorityConfig[ticket.priority] || priorityConfig.Medium;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    await onAddMessage(newMessage.trim(), attachment || undefined);
    setNewMessage('');
    setAttachment(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachment(file);
    }
  };

  const canAddMessage = ticket.status !== 'Closed';

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Ticket #{ticket.ticket_number}
              </DialogTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {ticket.subject}
              </p>
            </div>
          </div>
        </DialogHeader>

        {/* Ticket Info */}
        <Card className="flex-shrink-0">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-2 items-center">
              <Badge variant="outline" className={`${status.bgColor} ${status.color} flex items-center gap-1`}>
                {status.icon}
                {ticket.status}
              </Badge>
              <Badge variant="outline" className={priorityClass}>
                {ticket.priority === 'Urgent' && (
                  <AlertCircle className="h-3 w-3 mr-1" />
                )}
                {ticket.priority}
              </Badge>
              <Badge variant="outline">{ticket.category}</Badge>
              {ticket.assigned_to_name && (
                <Badge variant="outline" className="bg-blue-50">
                  <User className="h-3 w-3 mr-1" />
                  {ticket.assigned_to_name}
                </Badge>
              )}
            </div>

            <Separator className="my-3" />

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Created:</span>
                <p>{format(new Date(ticket.created_at), 'MMM d, yyyy h:mm a')}</p>
              </div>
              {ticket.resolved_at && (
                <div>
                  <span className="text-muted-foreground">Resolved:</span>
                  <p>{format(new Date(ticket.resolved_at), 'MMM d, yyyy h:mm a')}</p>
                </div>
              )}
              {ticket.closed_at && (
                <div>
                  <span className="text-muted-foreground">Closed:</span>
                  <p>{format(new Date(ticket.closed_at), 'MMM d, yyyy h:mm a')}</p>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-4">
              {ticket.can_close && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onCloseTicket}
                  disabled={isSubmitting}
                >
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Close Ticket
                </Button>
              )}
              {ticket.can_reopen && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onReopenTicket}
                  disabled={isSubmitting}
                >
                  <RefreshCcw className="h-4 w-4 mr-1" />
                  Reopen Ticket
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Messages */}
        <div className="flex-1 min-h-0">
          <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Conversation ({ticket.messages.length})
          </h4>
          <ScrollArea className="h-[250px] pr-4">
            <div className="space-y-4">
              {ticket.messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isOwn={message.is_own_message}
                />
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* New Message Form */}
        {canAddMessage ? (
          <form onSubmit={handleSubmit} className="flex-shrink-0 space-y-3 pt-4 border-t">
            <div className="space-y-2">
              <Label htmlFor="message">Add Reply</Label>
              <Textarea
                id="message"
                placeholder="Type your message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                rows={3}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Input
                  id="attachment"
                  type="file"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => document.getElementById('attachment')?.click()}
                >
                  <Paperclip className="h-4 w-4 mr-1" />
                  Attach
                </Button>
                {attachment && (
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <Paperclip className="h-3 w-3" />
                    {attachment.name}
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-5 w-5 p-0"
                      onClick={() => setAttachment(null)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                )}
              </div>

              <Button
                type="submit"
                size="sm"
                disabled={!newMessage.trim() || isSubmitting}
              >
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                ) : (
                  <Send className="h-4 w-4 mr-1" />
                )}
                Send
              </Button>
            </div>
          </form>
        ) : (
          <div className="flex-shrink-0 pt-4 border-t text-center text-sm text-muted-foreground">
            This ticket is closed. Reopen it to add new messages.
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default TicketDetail;
