import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Receipt } from 'lucide-react';
import { ExpenseCard } from './ExpenseCard';
import type { ExpenseClaimListItem, ExpenseStatus } from '@/types/expense.types';

interface ExpensesListProps {
  expenses: ExpenseClaimListItem[];
  isLoading: boolean;
  statusFilter: ExpenseStatus | 'all';
  onStatusFilter: (status: ExpenseStatus | 'all') => void;
  onSubmit: (id: number) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  submittingId?: number | null;
  deletingId?: number | null;
}

export function ExpensesList({
  expenses,
  isLoading,
  statusFilter,
  onStatusFilter,
  onSubmit,
  onDelete,
  submittingId,
  deletingId,
}: ExpensesListProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">My Expense Claims</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-muted rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-lg flex items-center gap-2">
            <Receipt className="h-5 w-5" />
            My Expense Claims
          </CardTitle>
          <Select
            value={statusFilter}
            onValueChange={(value) => onStatusFilter(value as ExpenseStatus | 'all')}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="Draft">Draft</SelectItem>
              <SelectItem value="Submitted">Submitted</SelectItem>
              <SelectItem value="Under Review">Under Review</SelectItem>
              <SelectItem value="Approved">Approved</SelectItem>
              <SelectItem value="Rejected">Rejected</SelectItem>
              <SelectItem value="Paid">Paid</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {expenses.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Receipt className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No expense claims found</p>
            <p className="text-sm">Create a new claim to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {expenses.map((expense) => (
              <ExpenseCard
                key={expense.id}
                expense={expense}
                onSubmit={onSubmit}
                onDelete={onDelete}
                isSubmitting={submittingId === expense.id}
                isDeleting={deletingId === expense.id}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default ExpensesList;
