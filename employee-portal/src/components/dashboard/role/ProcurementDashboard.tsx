import { Link } from 'react-router-dom';
import {
  ShoppingCart,
  Package,
  Clock,
  TrendingUp,
  ClipboardList,
  Truck,
  ArrowRight,
  CalendarDays,
  FileText,
  Bell,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import type { DashboardSummary } from '@/types/dashboard.types';

interface ProcurementDashboardProps {
  data: DashboardSummary | null;
}

export function ProcurementDashboard({ data }: ProcurementDashboardProps) {
  const { employee } = useAuth();

  const procurementStats = [
    {
      label: 'Open Tickets',
      value: data?.open_tickets ?? 0,
      unit: 'active',
      icon: ClipboardList,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
      urgent: (data?.open_tickets ?? 0) > 0,
    },
    {
      label: 'My Leave Balance',
      value: data?.leave_balances?.[0]?.available_days ?? employee?.leave_days_entitled ?? 0,
      unit: 'days remaining',
      icon: CalendarDays,
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
      urgent: (data?.unread_notifications ?? 0) > 0,
    },
  ];

  const quickActions = [
    {
      icon: ShoppingCart,
      label: 'Purchase Orders',
      description: 'Create and manage purchase orders',
      gradient: 'from-blue-500 to-blue-600',
      shadow: 'shadow-blue-500/25',
      href: '/portal/procurement',
      badge: null,
    },
    {
      icon: Package,
      label: 'Inventory',
      description: 'Track stock and inventory levels',
      gradient: 'from-amber-500 to-amber-600',
      shadow: 'shadow-amber-500/25',
      href: '/portal/inventory',
      badge: null,
    },
    {
      icon: Truck,
      label: 'Suppliers',
      description: 'Manage vendor and supplier records',
      gradient: 'from-emerald-500 to-emerald-600',
      shadow: 'shadow-emerald-500/25',
      href: '/portal/suppliers',
      badge: null,
    },
    {
      icon: ClipboardList,
      label: 'Requisitions',
      description: 'View pending purchase requisitions',
      gradient: 'from-orange-500 to-orange-600',
      shadow: 'shadow-orange-500/25',
      href: '/portal/requisitions',
      badge: null,
    },
    {
      icon: FileText,
      label: 'My Payslips',
      description: 'View your personal payslips',
      gradient: 'from-purple-500 to-purple-600',
      shadow: 'shadow-purple-500/25',
      href: '/portal/payslips',
      badge: null,
    },
    {
      icon: Clock,
      label: 'Attendance & Leave',
      description: 'Manage your time and leave',
      gradient: 'from-cyan-500 to-cyan-600',
      shadow: 'shadow-cyan-500/25',
      href: '/portal/attendance',
      badge: null,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Procurement Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {procurementStats.map((stat) => (
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

      {/* Quick Actions */}
      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Procurement Actions</h2>
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

      {/* Procurement summary banner */}
      <Card className="border-amber-200 bg-gradient-to-r from-amber-600 to-orange-700 text-white shadow-lg">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0">
              <Package className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold">Procurement Module</h3>
              <p className="text-sm text-amber-100 mt-1">
                Manage purchase orders, suppliers, and inventory through the procurement portal.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
