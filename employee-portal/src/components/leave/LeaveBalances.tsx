import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { CalendarDays } from 'lucide-react';
import type { LeaveBalance } from '@/types/leave.types';

interface LeaveBalancesProps {
  balances: LeaveBalance[];
  summary: {
    total_allowed: number;
    total_used: number;
    total_remaining: number;
  } | null;
  isLoading: boolean;
}

export function LeaveBalances({
  balances,
  summary,
  isLoading,
}: LeaveBalancesProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Leave Balances</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="animate-pulse space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <div className="h-4 bg-muted rounded w-1/3"></div>
                  <div className="h-2 bg-muted rounded"></div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (balances.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Leave Balances</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-4">
            No leave balances found
          </p>
        </CardContent>
      </Card>
    );
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-red-500';
    if (percentage >= 50) return 'bg-orange-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      {summary && (
        <Card className="bg-gradient-to-br from-primary/5 to-primary/10">
          <CardContent className="p-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-primary">
                  {summary.total_allowed}
                </p>
                <p className="text-xs text-muted-foreground">Total Days</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-orange-600">
                  {summary.total_used}
                </p>
                <p className="text-xs text-muted-foreground">Days Used</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600">
                  {summary.total_remaining}
                </p>
                <p className="text-xs text-muted-foreground">Days Left</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Individual Balance Cards */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <CalendarDays className="h-5 w-5" />
            Leave Balances
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {balances.map((balance) => (
            <div key={balance.id} className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-medium">{balance.leave_type_name}</span>
                <span className="text-sm text-muted-foreground">
                  {balance.days_remaining} / {balance.days_allowed} days
                </span>
              </div>
              <div className="relative">
                <Progress
                  value={balance.percentage_used}
                  className="h-2"
                />
                <div
                  className={`absolute inset-0 h-2 rounded-full ${getProgressColor(
                    balance.percentage_used
                  )}`}
                  style={{ width: `${balance.percentage_used}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{balance.days_used} days used</span>
                <span>{balance.percentage_used}% utilized</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default LeaveBalances;
