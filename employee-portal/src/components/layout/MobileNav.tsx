import { NavLink } from 'react-router-dom';
import {
  Home,
  Clock,
  CalendarDays,
  FileText,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
}

const navItems: NavItem[] = [
  { path: '/portal', label: 'Home', icon: Home },
  { path: '/portal/attendance', label: 'Clock', icon: Clock },
  { path: '/portal/leave', label: 'Leave', icon: CalendarDays },
  { path: '/portal/payslips', label: 'Pay', icon: FileText },
];

export function MobileNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 md:hidden z-20 safe-area-pb shadow-lg">
      <div className="flex items-center justify-around">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/portal'}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center gap-1 py-3 px-4 text-xs font-medium transition-all min-w-[64px]',
                isActive
                  ? 'text-blue-600'
                  : 'text-slate-500 hover:text-slate-700'
              )
            }
          >
            {({ isActive }) => (
              <>
                <div
                  className={cn(
                    'h-8 w-8 rounded-xl flex items-center justify-center transition-all',
                    isActive
                      ? 'bg-blue-600 shadow-lg shadow-blue-600/25'
                      : 'bg-transparent'
                  )}
                >
                  <item.icon
                    className={cn(
                      'h-5 w-5 transition-colors',
                      isActive ? 'text-white' : 'text-slate-500'
                    )}
                  />
                </div>
                <span
                  className={cn(
                    'transition-colors',
                    isActive ? 'text-blue-600 font-semibold' : 'text-slate-500'
                  )}
                >
                  {item.label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}

export default MobileNav;
