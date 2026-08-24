import { NavLink } from 'react-router-dom';
import {
  Home,
  Clock,
  CalendarDays,
  FileText,
  X,
  Users,
  UserPlus,
  DollarSign,
  BookOpen,
  ShoppingCart,
  Package,
  BarChart2,
  Settings,
  Receipt,
  ClipboardList,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useRole, type RoleGroup } from '@/hooks/useRole';

interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  description?: string;
}

const NAV_ITEMS: Record<RoleGroup, NavItem[]> = {
  staff: [
    { path: '/portal', label: 'Dashboard', icon: Home, description: 'Overview & stats' },
    { path: '/portal/attendance', label: 'Attendance', icon: Clock, description: 'Clock in/out' },
    { path: '/portal/leave', label: 'Leave', icon: CalendarDays, description: 'Request time off' },
    { path: '/portal/payslips', label: 'Payslips', icon: FileText, description: 'View earnings' },
  ],
  hr: [
    { path: '/portal', label: 'Dashboard', icon: Home, description: 'HR overview' },
    { path: '/portal/employees', label: 'Employees', icon: Users, description: 'Manage employees' },
    { path: '/portal/leave', label: 'Leave Management', icon: CalendarDays, description: 'Review requests' },
    { path: '/careers', label: 'Recruitment', icon: UserPlus, description: 'Job postings & apps' },
    { path: '/portal/attendance', label: 'Attendance', icon: Clock, description: 'Track records' },
    { path: '/portal/payslips', label: 'My Payslips', icon: FileText, description: 'Your earnings' },
  ],
  manager: [
    { path: '/portal', label: 'Dashboard', icon: Home, description: 'Team overview' },
    { path: '/portal/leave', label: 'Leave Approvals', icon: ClipboardList, description: 'Review team leave' },
    { path: '/portal/attendance', label: 'Team Attendance', icon: Clock, description: 'Department records' },
    { path: '/portal/reports', label: 'Reports', icon: BarChart2, description: 'Team performance' },
    { path: '/portal/payslips', label: 'My Payslips', icon: FileText, description: 'Your earnings' },
  ],
  accountant: [
    { path: '/portal', label: 'Dashboard', icon: Home, description: 'Finance overview' },
    { path: '/portal/payroll', label: 'Payroll', icon: DollarSign, description: 'Process payroll' },
    { path: '/portal/accounts', label: 'Accounts', icon: BookOpen, description: 'Ledgers & accounts' },
    { path: '/portal/expenses', label: 'Expenses', icon: Receipt, description: 'Expense claims' },
    { path: '/portal/leave', label: 'Leave', icon: CalendarDays, description: 'Request time off' },
    { path: '/portal/payslips', label: 'My Payslips', icon: FileText, description: 'Your earnings' },
    { path: '/portal/attendance', label: 'Attendance', icon: Clock, description: 'Clock in/out' },
  ],
  procurement: [
    { path: '/portal', label: 'Dashboard', icon: Home, description: 'Procurement overview' },
    { path: '/portal/procurement', label: 'Purchase Orders', icon: ShoppingCart, description: 'Manage POs' },
    { path: '/portal/inventory', label: 'Inventory', icon: Package, description: 'Stock levels' },
    { path: '/portal/suppliers', label: 'Suppliers', icon: Users, description: 'Vendor records' },
    { path: '/portal/leave', label: 'Leave', icon: CalendarDays, description: 'Request time off' },
    { path: '/portal/payslips', label: 'My Payslips', icon: FileText, description: 'Your earnings' },
    { path: '/portal/attendance', label: 'Attendance', icon: Clock, description: 'Clock in/out' },
  ],
  admin: [
    { path: '/portal', label: 'Dashboard', icon: Home, description: 'System overview' },
    { path: '/portal/employees', label: 'Human Resources', icon: Users, description: 'Employees & HR' },
    { path: '/portal/payroll', label: 'Payroll & Finance', icon: DollarSign, description: 'Payroll & accounts' },
    { path: '/portal/procurement', label: 'Procurement', icon: ShoppingCart, description: 'Orders & suppliers' },
    { path: '/careers', label: 'Recruitment', icon: UserPlus, description: 'Job postings & apps' },
    { path: '/portal/reports', label: 'Reports', icon: BarChart2, description: 'System-wide reports' },
    { path: '/portal/attendance', label: 'Attendance', icon: Clock, description: 'Track records' },
    { path: '/portal/leave', label: 'Leave', icon: CalendarDays, description: 'Manage leave' },
    { path: '/portal/settings', label: 'Settings', icon: Settings, description: 'System config' },
  ],
};

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { roleGroup } = useRole();
  const navItems = NAV_ITEMS[roleGroup] ?? NAV_ITEMS.staff;

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 h-screen w-72 bg-white border-r border-slate-200 z-40 transform transition-transform duration-300 ease-in-out flex flex-col',
          'md:translate-x-0 md:shadow-none',
          isOpen ? 'translate-x-0 shadow-xl' : '-translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-100 flex-shrink-0">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="ZCHPC" className="h-10 w-auto" />
            <div>
              <span className="font-bold text-slate-900">ZCHPC ERP</span>
              <span className="block text-xs text-slate-500">Employee Portal</span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-slate-500 hover:text-slate-700 hover:bg-slate-100"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation - scrollable */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          <p className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Menu
          </p>
          {navItems.map((item) => (
            <NavLink
              key={item.path + item.label}
              to={item.path}
              end={item.path === '/portal'}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/25'
                    : 'text-slate-600 hover:bg-blue-50 hover:text-blue-700'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <div
                    className={cn(
                      'h-9 w-9 rounded-lg flex items-center justify-center flex-shrink-0',
                      isActive ? 'bg-white/20' : 'bg-slate-100'
                    )}
                  >
                    <item.icon
                      className={cn('h-5 w-5', isActive ? 'text-white' : 'text-slate-500')}
                    />
                  </div>
                  <div className="min-w-0">
                    <span className="block truncate">{item.label}</span>
                    {item.description && (
                      <span
                        className={cn(
                          'text-xs block truncate',
                          isActive ? 'text-blue-100' : 'text-slate-400'
                        )}
                      >
                        {item.description}
                      </span>
                    )}
                  </div>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 flex-shrink-0">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4">
            <p className="text-sm font-medium text-slate-700">Need Help?</p>
            <p className="text-xs text-slate-500 mt-1">Contact HR for support</p>
            <a
              href="mailto:hr@zchpc-erp.zw"
              className="inline-block mt-3 text-xs font-medium text-blue-600 hover:text-blue-700"
            >
              hr@zchpc-erp.zw
            </a>
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
