import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Receipt,
  Send,
  Trash2,
  CheckCircle,
  Clock,
  XCircle,
  AlertCircle,
  DollarSign,
  Loader2,
  FileText,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import type { ExpenseClaimListItem, ExpenseStatus } from '@/types/expense.types';

interface ExpenseCardProps {
  expense: ExpenseClaimListItem;
  onSubmit?: (id: number) => Promise<void>;
  onDelete?: (id: number) => Promise<void>;
  isSubmitting?: boolean;
  isDeleting?: boolean;
}

export function ExpenseCard({
  expense,
  onSubmit,
  onDelete,
  isSubmitting,
  isDeleting,
}: ExpenseCardProps) {
  const getStatusBadge = (status: ExpenseStatus) => {
    switch (status) {
      case 'Draft':
        return (
          <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
            <FileText className="h-3 w-3 mr-1" />
            Draft
          </Badge>
        );
      case 'Submitted':
        return (
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            <Clock className="h-3 w-3 mr-1" />
            Submitted
          </Badge>
        );
      case 'Under Review':
        return (
          <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
            <AlertCircle className="h-3 w-3 mr-1" />
            Under Review
          </Badge>
        );
      case 'Approved':
        return (
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <CheckCircle className="h-3 w-3 mr-1" />
            Approved
          </Badge>
        );
      case 'Rejected':
        return (
          <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
            <XCircle className="h-3 w-3 mr-1" />
            Rejected
          </Badge>
        );
      case 'Paid':
        return (
          <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
            <DollarSign className="h-3 w-3 mr-1" />
            Paid
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
    if (currency === 'USD') {
      return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `ZiG ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            {/* Icon */}
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Receipt className="h-5 w-5 text-primary" />
            </div>

            {/* Details */}
            <div className="space-y-1 flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-semibold truncate">{expense.title}</h3>
                {getStatusBadge(expense.status)}
              </div>

              <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                <span>{expense.category_name}</span>
                <span>{format(parseISO(expense.date_incurred), 'MMM d, yyyy')}</span>
                {expense.has_receipt && (
                  <span className="flex items-center gap-1">
                    <FileText className="h-3 w-3" />
                    Receipt
                  </span>
                )}
              </div>

              <p className="text-lg font-semibold text-primary">
                {formatCurrency(expense.amount, expense.currency)}
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2 flex-shrink-0">
            {expense.can_submit && onSubmit && (
              <Button
                size="sm"
                onClick={() => onSubmit(expense.id)}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-1" />
                    Submit
                  </>
                )}
              </Button>
            )}
            {expense.can_cancel && onDelete && (
              <Button
                variant="ghost"
                size="sm"
                className="text-destructive hover:text-destructive hover:bg-destructive/10"
                onClick={() => onDelete(expense.id)}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ExpenseCard;
