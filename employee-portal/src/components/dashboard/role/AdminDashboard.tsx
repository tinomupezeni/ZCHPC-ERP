import { Link } from 'react-router-dom';
import {
  Users,
  DollarSign,
  ShoppingCart,
  Settings,
  BarChart2,
  UserPlus,
  Clock,
  CalendarDays,
  FileText,
  ArrowRight,
  Shield,
  TrendingUp,
  Bell,
  Receipt,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import type { DashboardSummary } from '@/types/dashboard.types';

interface AdminDashboardProps {
  data: DashboardSummary | null;
}

export function AdminDashboard({ data }: AdminDashboardProps) {
  const { employee } = useAuth();

  const systemStats = [
    {
      label: 'Pending Leave Requests',
      value: data?.pending_leave_requests ?? 0,
      unit: 'system-wide',
      icon: CalendarDays,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
      urgent: (data?.pending_leave_requests ?? 0) > 0,
    },
    {
      label: 'Expense Claims',
      value: data?.pending_expense_claims ?? 0,
      unit: 'pending',
      icon: Receipt,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
      urgent: (data?.pending_expense_claims ?? 0) > 0,
    },
    {
      label: 'Open Tickets',
      value: data?.open_tickets ?? 0,
      unit: 'active',
      icon: FileText,
      color: 'text-red-600',
      bg: 'bg-red-50',
      urgent: (data?.open_tickets ?? 0) > 0,
    },
    {
      label: 'Notifications',
      value: data?.unread_notifications ?? 0,
      unit: 'unread',
      icon: Bell,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      urgent: (data?.unread_notifications ?? 0) > 0,
    },
  ];

  const modules = [
    {
      icon: Users,
      label: 'Human Resources',
      description: 'Employees, positions, departments',
      gradient: 'from-blue-500 to-blue-600',
      shadow: 'shadow-blue-500/25',
      href: '/portal/employees',
    },
    {
      icon: DollarSign,
      label: 'Payroll & Finance',
      description: 'Payroll processing, accounts',
      gradient: 'from-emerald-500 to-emerald-600',
      shadow: 'shadow-emerald-500/25',
      href: '/portal/payroll',
    },
    {
      icon: ShoppingCart,
      label: 'Procurement',
      description: 'Purchase orders, suppliers',
      gradient: 'from-amber-500 to-amber-600',
      shadow: 'shadow-amber-500/25',
      href: '/portal/procurement',
    },
    {
      icon: UserPlus,
      label: 'Recruitment',
      description: 'Job postings, applications',
      gradient: 'from-cyan-500 to-cyan-600',
      shadow: 'shadow-cyan-500/25',
      href: '/careers',
    },
    {
      icon: BarChart2,
      label: 'Reports & Analytics',
      description: 'System-wide reports',
      gradient: 'from-indigo-500 to-indigo-600',
      shadow: 'shadow-indigo-500/25',
      href: '/portal/reports',
    },
    {
      icon: Settings,
      label: 'System Settings',
      description: 'Roles, permissions, config',
      gradient: 'from-slate-600 to-slate-700',
      shadow: 'shadow-slate-500/25',
      href: '/portal/settings',
    },
  ];

  const personalActions = [
    {
      icon: Clock,
      label: 'My Attendance',
      href: '/portal/attendance',
    },
    {
      icon: CalendarDays,
      label: 'Request Leave',
      href: '/portal/leave',
    },
    {
      icon: FileText,
      label: 'My Payslips',
      href: '/portal/payslips',
    },
  ];

  return (
    <div className="space-y-6">
      {/* System Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {systemStats.map((stat) => (
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
                  Needs attention
                </Badge>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* System Modules */}
      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">System Modules</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {modules.map((mod) => (
            <Link key={mod.label} to={mod.href}>
              <Card className="cursor-pointer border-slate-200 shadow-sm hover:shadow-lg transition-all duration-200 hover:-translate-y-1 group h-full">
                <CardContent className="p-5">
                  <div
                    className={`h-11 w-11 rounded-xl bg-gradient-to-br ${mod.gradient} flex items-center justify-center shadow-lg ${mod.shadow} group-hover:scale-110 transition-transform mb-3`}
                  >
                    <mod.icon className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                    {mod.label}
                  </h3>
                  <p className="text-sm text-slate-500 mt-1">{mod.description}</p>
                  <div className="flex items-center gap-1 text-blue-600 text-sm font-medium mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    Open module <ArrowRight className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Personal Actions + Upcoming Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Personal quick actions */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-600" />
              My Personal Portal
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {personalActions.map((action) => (
              <Link key={action.label} to={action.href}>
                <div className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 transition-colors group">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-lg bg-slate-100 group-hover:bg-blue-50 flex items-center justify-center transition-colors">
                      <action.icon className="h-4 w-4 text-slate-500 group-hover:text-blue-600 transition-colors" />
                    </div>
                    <span className="text-sm font-medium text-slate-700 group-hover:text-blue-700 transition-colors">
                      {action.label}
                    </span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>

        {/* Upcoming Events */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <CalendarDays className="h-5 w-5 text-blue-600" />
              Upcoming Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data?.upcoming_events && data.upcoming_events.length > 0 ? (
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
            ) : (
              <p className="text-sm text-slate-500 py-3">No upcoming events</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Admin banner */}
      <Card className="border-slate-700 bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-lg">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-white/10 flex items-center justify-center flex-shrink-0">
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold">Administrator Access</h3>
              <p className="text-sm text-slate-300 mt-1">
                You have full system access. Use admin tools responsibly and in accordance with data protection policies.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
