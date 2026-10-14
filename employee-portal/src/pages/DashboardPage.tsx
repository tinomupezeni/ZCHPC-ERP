import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRole } from '@/hooks/useRole';
import { dashboardService } from '@/services/dashboard.service';
import type { DashboardSummary } from '@/types/dashboard.types';
import {
  Sun,
  Sunset,
  Moon,
  Briefcase,
  Shield,
  Users,
  DollarSign,
  ShoppingCart,
} from 'lucide-react';
import { format } from 'date-fns';

// Role-specific dashboard components
import { StaffDashboard } from '@/components/dashboard/role/StaffDashboard';
import { HRDashboard } from '@/components/dashboard/role/HRDashboard';
import { ManagerDashboard } from '@/components/dashboard/role/ManagerDashboard';
import { AccountantDashboard } from '@/components/dashboard/role/AccountantDashboard';
import { ProcurementDashboard } from '@/components/dashboard/role/ProcurementDashboard';
import { AdminDashboard } from '@/components/dashboard/role/AdminDashboard';

const ROLE_BANNER: Record<string, { gradient: string; icon: React.ElementType; badge: string; subtitle: string }> = {
  admin: {
    gradient: 'from-slate-800 via-slate-900 to-indigo-900',
    icon: Shield,
    badge: 'System Administrator',
    subtitle: 'Full system access — manage all modules and configurations.',
  },
  hr: {
    gradient: 'from-blue-700 via-blue-800 to-indigo-800',
    icon: Users,
    badge: 'Human Resources',
    subtitle: 'Manage employees, leave requests, and recruitment.',
  },
  manager: {
    gradient: 'from-indigo-600 via-indigo-700 to-purple-700',
    icon: Briefcase,
    badge: 'Department Manager',
    subtitle: 'View team attendance, approve leave, and monitor performance.',
  },
  accountant: {
    gradient: 'from-emerald-700 via-emerald-800 to-teal-800',
    icon: DollarSign,
    badge: 'Accountant',
    subtitle: 'Process payroll, manage accounts, and review expense claims.',
  },
  procurement: {
    gradient: 'from-amber-700 via-amber-800 to-orange-800',
    icon: ShoppingCart,
    badge: 'Procurement Officer',
    subtitle: 'Manage purchase orders, suppliers, and inventory.',
  },
  staff: {
    gradient: 'from-blue-600 via-blue-700 to-indigo-700',
    icon: Briefcase,
    badge: '',
    subtitle: "Welcome back to your employee portal. Here's an overview of your account.",
  },
};

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return { text: 'Good morning', icon: Sun, color: 'text-amber-400' };
  if (hour < 18) return { text: 'Good afternoon', icon: Sunset, color: 'text-orange-400' };
  return { text: 'Good evening', icon: Moon, color: 'text-indigo-300' };
}

export function DashboardPage() {
  const { employee } = useAuth();
  const { roleGroup } = useRole();

  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    dashboardService.getDashboard().then(setDashboardData).catch(() => {
      // Dashboard data is optional; page still renders with fallbacks
    });
  }, []);

  const greeting = getGreeting();
  const GreetingIcon = greeting.icon;
  const banner = ROLE_BANNER[roleGroup] ?? ROLE_BANNER.staff;
  const BannerIcon = banner.icon;

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div
        className={`relative overflow-hidden bg-gradient-to-r ${banner.gradient} rounded-2xl p-6 md:p-8 text-white shadow-xl`}
      >
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2 pointer-events-none" />

        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <GreetingIcon className={`h-5 w-5 ${greeting.color}`} />
                <span className="text-white/70 text-sm font-medium">
                  {format(new Date(), 'EEEE, MMMM d, yyyy')}
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold">
                {greeting.text}, {employee?.first_name}!
              </h1>
              <p className="text-white/80 mt-2 max-w-lg text-sm">{banner.subtitle}</p>
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

          {/* Badges */}
          <div className="flex flex-wrap gap-3 mt-5">
            {banner.badge && (
              <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur rounded-lg px-3 py-1.5">
                <BannerIcon className="h-4 w-4 text-white/80" />
                <span className="text-sm font-medium">{banner.badge}</span>
              </div>
            )}
            {employee?.position_title && (
              <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur rounded-lg px-3 py-1.5">
                <Briefcase className="h-4 w-4 text-white/70" />
                <span className="text-sm">{employee.position_title}</span>
              </div>
            )}
            {employee?.department_name && (
              <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur rounded-lg px-3 py-1.5">
                <span className="text-sm text-white/80">{employee.department_name}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Role-specific dashboard content */}
      {roleGroup === 'admin' && <AdminDashboard data={dashboardData} />}
      {roleGroup === 'hr' && <HRDashboard data={dashboardData} />}
      {roleGroup === 'manager' && <ManagerDashboard data={dashboardData} />}
      {roleGroup === 'accountant' && <AccountantDashboard data={dashboardData} />}
      {roleGroup === 'procurement' && <ProcurementDashboard data={dashboardData} />}
      {roleGroup === 'staff' && <StaffDashboard data={dashboardData} />}
    </div>
  );
}

export default DashboardPage;
