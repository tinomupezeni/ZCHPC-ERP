import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import {
  CalendarDays,
  Clock,
  FileText,
  TrendingUp,
  Briefcase,
  ArrowRight,
  Sun,
  Sunset,
  Moon,
  Bell,
  CheckCircle,
} from 'lucide-react';
import { format } from 'date-fns';

export function DashboardPage() {
  const { employee } = useAuth();

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return { text: 'Good morning', icon: Sun, color: 'text-amber-500' };
    if (hour < 18) return { text: 'Good afternoon', icon: Sunset, color: 'text-orange-500' };
    return { text: 'Good evening', icon: Moon, color: 'text-indigo-500' };
  };

  const greeting = getGreeting();
  const GreetingIcon = greeting.icon;

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

  const stats = [
    {
      label: 'Leave Balance',
      value: employee?.leave_days_entitled || 0,
      unit: 'days',
      icon: CalendarDays,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: 'Days Present',
      value: 22,
      unit: 'this month',
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      label: 'Pending Requests',
      value: 0,
      unit: 'requests',
      icon: Clock,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 rounded-2xl p-6 md:p-8 text-white shadow-xl">
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />

        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <GreetingIcon className={`h-6 w-6 ${greeting.color}`} />
                <span className="text-blue-200 text-sm font-medium">
                  {format(new Date(), 'EEEE, MMMM d, yyyy')}
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold">
                {greeting.text}, {employee?.first_name}!
              </h1>
              <p className="text-blue-100 mt-2 max-w-lg">
                Welcome back to your employee portal. Here's an overview of your account.
              </p>
            </div>
            <div className="flex-shrink-0">
              <div className="h-20 w-20 md:h-24 md:w-24 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
                <span className="text-3xl md:text-4xl font-bold">
                  {employee?.first_name?.charAt(0)}
                  {employee?.surname?.charAt(0)}
                </span>
              </div>
            </div>
          </div>

          {/* Position badge */}
          <div className="flex flex-wrap gap-3 mt-6">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur rounded-lg px-4 py-2">
              <Briefcase className="h-4 w-4 text-blue-200" />
              <span className="text-sm font-medium">
                {employee?.position_title || 'Employee'}
              </span>
            </div>
            {employee?.department_name && (
              <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur rounded-lg px-4 py-2">
                <span className="text-sm text-blue-200">
                  {employee.department_name}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

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
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Quick Actions</h2>
        </div>
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
                    Get started
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Activity & Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-3 rounded-xl bg-slate-50">
                <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-700">No recent activity</p>
                  <p className="text-xs text-slate-500">Your activities will appear here</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Bell className="h-5 w-5 text-blue-600" />
              Notifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-3 rounded-xl bg-blue-50">
                <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <Bell className="h-5 w-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-700">Welcome to the Portal!</p>
                  <p className="text-xs text-slate-500">Explore your dashboard and features</p>
                </div>
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
              <Button className="bg-white text-slate-900 hover:bg-slate-100 gap-2">
                View Jobs
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default DashboardPage;
