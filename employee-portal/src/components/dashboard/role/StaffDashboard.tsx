import { Link } from 'react-router-dom';
import {
  CalendarDays,
  Clock,
  FileText,
  TrendingUp,
  Briefcase,
  ArrowRight,
  Bell,
  CheckCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import type { DashboardSummary } from '@/types/dashboard.types';

interface StaffDashboardProps {
  data: DashboardSummary | null;
}

export function StaffDashboard({ data }: StaffDashboardProps) {
  const { employee } = useAuth();

  const stats = [
    {
      label: 'Leave Balance',
      value: data?.leave_balances?.[0]?.available_days ?? employee?.leave_days_entitled ?? 0,
      unit: 'days',
      icon: CalendarDays,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: 'Days Present',
      value: data?.attendance_this_month ?? 0,
      unit: 'this month',
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      label: 'Pending Requests',
      value: data?.pending_leave_requests ?? 0,
      unit: 'requests',
      icon: Clock,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
    },
  ];

  const quickActions = [
    {
      icon: Clock,
      label: 'Clock In',
      description: 'Record your attendance',
      gradient: 'from-green-500 to-emerald-600',
      shadow: 'shadow-green-500/25',
      href: '/portal/attendance',
    },
    {
      icon: CalendarDays,
      label: 'Request Leave',
      description: 'Submit leave application',
      gradient: 'from-blue-500 to-blue-600',
      shadow: 'shadow-blue-500/25',
      href: '/portal/leave',
    },
    {
      icon: FileText,
      label: 'View Payslip',
      description: 'Access your payslips',
      gradient: 'from-purple-500 to-purple-600',
      shadow: 'shadow-purple-500/25',
      href: '/portal/payslips',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                  <div className="flex items-baseline gap-2 mt-2">
                    <span className={`text-3xl font-bold ${stat.color}`}>{stat.value}</span>
                    <span className="text-sm text-slate-400">{stat.unit}</span>
                  </div>
                </div>
                <div className={`h-12 w-12 rounded-xl ${stat.bg} flex items-center justify-center`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <Link key={action.label} to={action.href}>
              <Card className="cursor-pointer border-slate-200 shadow-sm hover:shadow-lg transition-all duration-200 hover:-translate-y-1 group">
                <CardContent className="p-5">
                  <div
                    className={`h-12 w-12 rounded-xl bg-gradient-to-br ${action.gradient} flex items-center justify-center mb-4 shadow-lg ${action.shadow} group-hover:scale-110 transition-transform`}
                  >
                    <action.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                    {action.label}
                  </h3>
                  <p className="text-sm text-slate-500 mt-1">{action.description}</p>
                  <div className="flex items-center gap-1 text-blue-600 text-sm font-medium mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    Get started <ArrowRight className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Activity & Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 p-3 rounded-xl bg-slate-50">
              <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-700">No recent activity</p>
                <p className="text-xs text-slate-500">Your activities will appear here</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Bell className="h-5 w-5 text-blue-600" />
              Notifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 p-3 rounded-xl bg-blue-50">
              <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                <Bell className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-700">Welcome to the Portal!</p>
                <p className="text-xs text-slate-500">Explore your dashboard and features</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Career Link */}
      <Card className="border-slate-200 bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-lg">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-white/10 flex items-center justify-center">
                <Briefcase className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold">Explore Career Opportunities</h3>
                <p className="text-sm text-slate-300">Check out open positions at ZCHPC</p>
              </div>
            </div>
            <Link to="/careers">
              <button className="inline-flex items-center gap-2 bg-white text-slate-900 hover:bg-slate-100 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                View Jobs <ArrowRight className="h-4 w-4" />
              </button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
