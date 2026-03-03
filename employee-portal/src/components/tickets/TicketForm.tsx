import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { MessageSquarePlus, Loader2 } from 'lucide-react';
import type {
  CreateTicketData,
  TicketCategoryOption,
  TicketPriorityOption,
  TicketCategory,
  TicketPriority,
} from '@/types/ticket.types';

interface TicketFormProps {
  categories: TicketCategoryOption[];
  priorities: TicketPriorityOption[];
  onSubmit: (data: CreateTicketData) => Promise<void>;
  isSubmitting: boolean;
}

export function TicketForm({
  categories,
  priorities,
  onSubmit,
  isSubmitting,
}: TicketFormProps) {
  const [category, setCategory] = useState<string>('');
  const [priority, setPriority] = useState<string>('Medium');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!category) {
      newErrors.category = 'Please select a category';
    }

    if (!priority) {
      newErrors.priority = 'Please select a priority';
    }

    if (!subject.trim()) {
      newErrors.subject = 'Subject is required';
    } else if (subject.length < 5) {
      newErrors.subject = 'Subject must be at least 5 characters';
    }

    if (!description.trim()) {
      newErrors.description = 'Description is required';
    } else if (description.length < 20) {
      newErrors.description = 'Please provide more details (at least 20 characters)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    await onSubmit({
      category: category as TicketCategory,
      priority: priority as TicketPriority,
      subject: subject.trim(),
      description: description.trim(),
    });

    // Reset form
    setCategory('');
    setPriority('Medium');
    setSubject('');
    setDescription('');
    setErrors({});
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <MessageSquarePlus className="h-5 w-5" />
          Create Support Ticket
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Category and Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger id="category">
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.category && (
                <p className="text-sm text-destructive">{errors.category}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger id="priority">
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  {priorities.map((pri) => (
                    <SelectItem key={pri.value} value={pri.value}>
                      {pri.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.priority && (
                <p className="text-sm text-destructive">{errors.priority}</p>
              )}
            </div>
          </div>

          {/* Subject */}
          <div className="space-y-2">
            <Label htmlFor="subject">Subject</Label>
            <Input
              id="subject"
              placeholder="Brief summary of your issue"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
            {errors.subject && (
              <p className="text-sm text-destructive">{errors.subject}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Please describe your issue in detail. Include any relevant information that might help us resolve it faster."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
            />
            {errors.description && (
              <p className="text-sm text-destructive">{errors.description}</p>
            )}
            <p className="text-xs text-muted-foreground">
              {description.length} characters
            </p>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating Ticket...
              </>
            ) : (
              'Create Ticket'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default TicketForm;
