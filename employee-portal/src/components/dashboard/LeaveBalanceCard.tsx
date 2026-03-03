import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { LeaveBalance } from '@/types/dashboard.types';

interface LeaveBalanceCardProps {
  balances: LeaveBalance[];
}

export function LeaveBalanceCard({ balances }: LeaveBalanceCardProps) {
  if (balances.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Leave Balances</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-4">
            No leave balances available
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Leave Balances</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {balances.map((balance) => {
          const usagePercent = balance.total_days > 0
            ? ((balance.used_days + balance.pending_days) / balance.total_days) * 100
            : 0;

          return (
            <div key={balance.leave_type_id} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{balance.leave_type}</span>
                <span className="text-muted-foreground">
                  {balance.available_days} / {balance.total_days} days
                </span>
              </div>
              <div className="h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${Math.min(100 - usagePercent, 100)}%` }}
                />
              </div>
              {balance.pending_days > 0 && (
                <p className="text-xs text-orange-600">
                  {balance.pending_days} day(s) pending approval
                </p>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export default LeaveBalanceCard;
