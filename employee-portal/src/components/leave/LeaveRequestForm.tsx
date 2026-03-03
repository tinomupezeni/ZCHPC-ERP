import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { CalendarPlus, Loader2 } from 'lucide-react';
import { format, differenceInDays } from 'date-fns';
import type { LeaveType, LeaveBalance, CreateLeaveRequestData } from '@/types/leave.types';

interface LeaveRequestFormProps {
  leaveTypes: LeaveType[];
  balances: LeaveBalance[];
  onSubmit: (data: CreateLeaveRequestData) => Promise<void>;
  isSubmitting: boolean;
}

export function LeaveRequestForm({
  leaveTypes,
  balances,
  onSubmit,
  isSubmitting,
}: LeaveRequestFormProps) {
  const [leaveType, setLeaveType] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const today = format(new Date(), 'yyyy-MM-dd');

  const selectedBalance = balances.find(
    (b) => b.leave_type === parseInt(leaveType)
  );

  const calculateDays = (): number => {
    if (!startDate || !endDate) return 0;
    const start = new Date(startDate);
    const end = new Date(endDate);
    return differenceInDays(end, start) + 1;
  };

  const numberOfDays = calculateDays();

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!leaveType) {
      newErrors.leaveType = 'Please select a leave type';
    }

    if (!startDate) {
      newErrors.startDate = 'Please select a start date';
    }

    if (!endDate) {
      newErrors.endDate = 'Please select an end date';
    }

    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      newErrors.endDate = 'End date must be after start date';
    }

    if (selectedBalance && numberOfDays > selectedBalance.days_remaining) {
      newErrors.leaveType = `Insufficient balance. You have ${selectedBalance.days_remaining} days remaining.`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    await onSubmit({
      leave_type: parseInt(leaveType),
      start_date: startDate,
      end_date: endDate,
      reason: reason || undefined,
    });

    // Reset form on success
    setLeaveType('');
    setStartDate('');
    setEndDate('');
    setReason('');
    setErrors({});
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <CalendarPlus className="h-5 w-5" />
          Request Leave
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Leave Type */}
          <div className="space-y-2">
            <Label htmlFor="leaveType">Leave Type</Label>
            <Select value={leaveType} onValueChange={setLeaveType}>
              <SelectTrigger id="leaveType">
                <SelectValue placeholder="Select leave type" />
              </SelectTrigger>
              <SelectContent>
                {leaveTypes.map((type) => {
                  const balance = balances.find(
                    (b) => b.leave_type === type.id
                  );
                  return (
                    <SelectItem key={type.id} value={type.id.toString()}>
                      {type.name}
                      {balance && (
                        <span className="text-muted-foreground ml-2">
                          ({balance.days_remaining} days left)
                        </span>
                      )}
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
            {errors.leaveType && (
              <p className="text-sm text-destructive">{errors.leaveType}</p>
            )}
            {selectedBalance && (
              <p className="text-xs text-muted-foreground">
                Balance: {selectedBalance.days_remaining} / {selectedBalance.days_allowed} days
              </p>
            )}
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="startDate">Start Date</Label>
              <Input
                id="startDate"
                type="date"
                min={today}
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
              {errors.startDate && (
                <p className="text-sm text-destructive">{errors.startDate}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="endDate">End Date</Label>
              <Input
                id="endDate"
                type="date"
                min={startDate || today}
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
              {errors.endDate && (
                <p className="text-sm text-destructive">{errors.endDate}</p>
              )}
            </div>
          </div>

          {/* Days Summary */}
          {numberOfDays > 0 && (
            <div className="p-3 bg-muted/50 rounded-lg text-center">
              <p className="text-lg font-semibold">{numberOfDays} day{numberOfDays !== 1 ? 's' : ''}</p>
              <p className="text-xs text-muted-foreground">
                {startDate && format(new Date(startDate), 'MMM d, yyyy')} -{' '}
                {endDate && format(new Date(endDate), 'MMM d, yyyy')}
              </p>
            </div>
          )}

          {/* Reason */}
          <div className="space-y-2">
            <Label htmlFor="reason">Reason (Optional)</Label>
            <Textarea
              id="reason"
              placeholder="Enter reason for leave..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
            />
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={isSubmitting || !leaveType || !startDate || !endDate}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Request'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default LeaveRequestForm;
