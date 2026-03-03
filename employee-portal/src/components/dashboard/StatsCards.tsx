import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  CalendarDays,
  Clock,
  FileText,
  TrendingUp,
} from 'lucide-react';

interface StatsCardsProps {
  totalLeaveBalance: number;
  attendanceThisMonth: number;
  pendingLeaveRequests: number;
  todayStatus: 'clocked_in' | 'clocked_out' | 'not_clocked';
}

export function StatsCards({
  totalLeaveBalance,
  attendanceThisMonth,
  pendingLeaveRequests,
  todayStatus,
}: StatsCardsProps) {
  const getStatusText = () => {
    switch (todayStatus) {
      case 'clocked_in':
        return { text: 'Clocked In', color: 'text-green-600' };
      case 'clocked_out':
        return { text: 'Clocked Out', color: 'text-blue-600' };
      default:
        return { text: 'Not Clocked', color: 'text-orange-600' };
    }
  };

  const status = getStatusText();

  const stats = [
    {
      title: 'Leave Balance',
      value: totalLeaveBalance,
      subtitle: 'Days available',
      icon: CalendarDays,
      color: 'text-primary',
    },
    {
      title: "Today's Status",
      value: status.text,
      subtitle: 'Attendance',
      icon: Clock,
      color: status.color,
      isText: true,
    },
    {
      title: 'This Month',
      value: attendanceThisMonth,
      subtitle: 'Days present',
      icon: TrendingUp,
      color: 'text-green-600',
    },
    {
      title: 'Pending Requests',
      value: pendingLeaveRequests,
      subtitle: 'Leave requests',
      icon: FileText,
      color: pendingLeaveRequests > 0 ? 'text-orange-600' : 'text-muted-foreground',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <Card key={stat.title}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-xl font-bold ${stat.color}`}>
              {stat.isText ? stat.value : stat.value}
            </div>
            <p className="text-xs text-muted-foreground mt-1 truncate">
              {stat.subtitle}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default StatsCards;
