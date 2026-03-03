import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CalendarCheck, CalendarX, Clock, Calendar } from 'lucide-react';
import type { AttendanceSummary } from '@/types/attendance.types';

interface AttendanceSummaryCardProps {
  summary: AttendanceSummary | null;
  isLoading: boolean;
}

export function AttendanceSummaryCard({
  summary,
  isLoading,
}: AttendanceSummaryCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Monthly Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-muted rounded w-3/4"></div>
            <div className="h-4 bg-muted rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Monthly Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const monthName = new Date(summary.year, summary.month - 1).toLocaleString(
    'default',
    { month: 'long' }
  );

  const stats = [
    {
      label: 'Days Present',
      value: summary.days_present,
      icon: CalendarCheck,
      color: 'text-green-600',
    },
    {
      label: 'Days Absent',
      value: summary.days_absent,
      icon: CalendarX,
      color: 'text-red-600',
    },
    {
      label: 'Days on Leave',
      value: summary.days_on_leave,
      icon: Calendar,
      color: 'text-blue-600',
    },
    {
      label: 'Hours Worked',
      value: Number(summary.total_hours_worked || 0).toFixed(1),
      icon: Clock,
      color: 'text-primary',
    },
  ];

  const attendanceRate = summary.total_working_days > 0
    ? ((summary.days_present / summary.total_working_days) * 100).toFixed(1)
    : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Monthly Summary</span>
          <span className="text-sm font-normal text-muted-foreground">
            {monthName} {summary.year}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Attendance Rate */}
        <div className="text-center p-4 bg-primary/5 rounded-lg">
          <p className="text-3xl font-bold text-primary">{attendanceRate}%</p>
          <p className="text-sm text-muted-foreground">Attendance Rate</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg"
            >
              <stat.icon className={`h-5 w-5 ${stat.color}`} />
              <div>
                <p className="text-lg font-semibold">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Working Days */}
        <div className="text-center text-sm text-muted-foreground">
          Total working days: {summary.total_working_days}
        </div>
      </CardContent>
    </Card>
  );
}

export default AttendanceSummaryCard;
