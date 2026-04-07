import { Link } from 'react-router-dom';
import {
  Users,
  CalendarDays,
  Clock,
  TrendingUp,
  ClipboardList,
  BarChart2,
  ArrowRight,
  UserCheck,
  Bell,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import type { DashboardSummary } from '@/types/dashboard.types';

interface ManagerDashboardProps {
  data: DashboardSummary | null;
}

export function ManagerDashboard({ data }: ManagerDashboardProps) {
  const { employee } = useAuth();

  const managerStats = [
    {
      label: 'Leave Requests',
      value: data?.pending_leave_requests ?? 0,
      unit: 'pending approval',
      icon: CalendarDays,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
      urgent: (data?.pending_leave_requests ?? 0) > 0,
    },
    {
      label: 'My Leave Balance',
      value: data?.leave_balances?.[0]?.available_days ?? employee?.leave_days_entitled ?? 0,
      unit: 'days remaining',
      icon: Clock,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      urgent: false,
    },
    {
      label: 'My Attendance',
      value: data?.attendance_this_month ?? 0,
      unit: 'days this month',
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-50',
      urgent: false,
    },
    {
      label: 'Notifications',
      value: data?.unread_notifications ?? 0,
      unit: 'unread',
      icon: Bell,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      urgent: false,
    },
  ];

  const quickActions = [
    {
      icon: ClipboardList,
      label: 'Approve Leave',
      description: 'Review team leave requests',
      gradient: 'from-orange-500 to-orange-600',
      shadow: 'shadow-orange-500/25',
      href: '/portal/leave',
      badge: data?.pending_leave_requests ? `${data.pending_leave_requests} pending` : null,
    },
    {
      icon: Users,
      label: 'Team Attendance',
      description: 'View department attendance',
      gradient: 'from-blue-500 to-blue-600',
      shadow: 'shadow-blue-500/25',
      href: '/portal/attendance',
    },
    {
      icon: BarChart2,
      label: 'Team Reports',
      description: 'Performance and activity reports',
      gradient: 'from-indigo-500 to-indigo-600',
      shadow: 'shadow-indigo-500/25',
      href: '/portal/reports',
    },
    {
      icon: UserCheck,
      label: 'My Attendance',
      description: 'Your personal attendance record',
      gradient: 'from-emerald-500 to-emerald-600',
      shadow: 'shadow-emerald-500/25',
      href: '/portal/attendance',
    },
    {
      icon: CalendarDays,
      label: 'Request Leave',
      description: 'Submit your own leave request',
      gradient: 'from-cyan-500 to-cyan-600',
      shadow: 'shadow-cyan-500/25',
      href: '/portal/leave',
    },
    {
      icon: Clock,
      label: 'My Payslips',
      description: 'View your earnings',
      gradient: 'from-purple-500 to-purple-600',
      shadow: 'shadow-purple-500/25',
      href: '/portal/payslips',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Department badge */}
      {employee?.department_name && (
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-slate-500" />
          <span className="text-sm text-slate-600 font-medium">
            Managing: <span className="text-slate-900">{employee.department_name}</span>
          </span>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {managerStats.map((stat) => (
          <Card
            key={stat.label}
            className={`border shadow-sm hover:shadow-md transition-shadow ${
              stat.urgent ? 'border-orange-200 bg-orange-50/30' : 'border-slate-200'
            }`}
          >
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-xs font-medium text-slate-500">{stat.label}</p>
                  <div className="flex items-baseline gap-1 mt-2">
                    <span className={`text-2xl font-bold ${stat.color}`}>{stat.value}</span>
                  </div>
                  <span className="text-xs text-slate-400">{stat.unit}</span>
                </div>
                <div className={`h-10 w-10 rounded-xl ${stat.bg} flex items-center justify-center flex-shrink-0`}>
                  <stat.icon className={`h-5 w-5 ${stat.color}`} />
                </div>
              </div>
              {stat.urgent && (
                <Badge variant="destructive" className="mt-2 text-xs">
                  Action required
                </Badge>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Management Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <Link key={action.label} to={action.href}>
              <Card className="cursor-pointer border-slate-200 shadow-sm hover:shadow-lg transition-all duration-200 hover:-translate-y-1 group h-full">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div
                      className={`h-11 w-11 rounded-xl bg-gradient-to-br ${action.gradient} flex items-center justify-center shadow-lg ${action.shadow} group-hover:scale-110 transition-transform`}
                    >
                      <action.icon className="h-5 w-5 text-white" />
                    </div>
                    {action.badge && (
                      <Badge className="bg-orange-100 text-orange-700 border-0 text-xs">
                        {action.badge}
                      </Badge>
                    )}
                  </div>
                  <h3 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                    {action.label}
                  </h3>
                  <p className="text-sm text-slate-500 mt-1">{action.description}</p>
                  <div className="flex items-center gap-1 text-blue-600 text-sm font-medium mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    Open <ArrowRight className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Upcoming Events */}
      {data?.upcoming_events && data.upcoming_events.length > 0 && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <CalendarDays className="h-5 w-5 text-blue-600" />
              Upcoming Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.upcoming_events.slice(0, 3).map((event, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50">
                  <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <CalendarDays className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">{event.title}</p>
                    <p className="text-xs text-slate-500">{event.start_date}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
