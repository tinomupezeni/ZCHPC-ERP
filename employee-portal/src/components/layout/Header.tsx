import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Bell, Menu, User, LogOut, Settings, ChevronDown, Briefcase } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { employee, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 text-white sticky top-0 z-20 shadow-lg">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left side - Menu button (mobile) and logo */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-white hover:bg-white/20"
            onClick={onMenuClick}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <Link to="/portal" className="flex items-center gap-2">
            <img src="/logo.png" alt="ZCHPC" className="h-9 w-auto" />
            <div className="hidden sm:block">
              <span className="font-bold text-lg tracking-tight">ZCHPC</span>
              <span className="text-blue-200 ml-2 text-sm">Portal</span>
            </div>
          </Link>
        </div>

        {/* Right side - Notifications and user menu */}
        <div className="flex items-center gap-2">
          {/* Quick link to careers */}
          <Link to="/careers">
            <Button
              variant="ghost"
              size="sm"
              className="hidden sm:flex items-center gap-2 text-blue-100 hover:text-white hover:bg-white/20"
            >
              <Briefcase className="h-4 w-4" />
              <span className="text-sm">Careers</span>
            </Button>
          </Link>

          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className="relative text-white hover:bg-white/20"
          >
            <Bell className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-2 w-2 bg-red-400 rounded-full ring-2 ring-blue-700" />
          </Button>

          {/* User menu */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              className="flex items-center gap-2 text-white hover:bg-white/20 pl-2 pr-3"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              <div className="h-8 w-8 rounded-full bg-white/20 flex items-center justify-center">
                <User className="h-4 w-4" />
              </div>
              <span className="hidden sm:block text-sm font-medium">
                {employee?.first_name}
              </span>
              <ChevronDown className="h-4 w-4 text-blue-200" />
            </Button>

            {/* Dropdown menu */}
            {showUserMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowUserMenu(false)}
                />
                <div className="absolute right-0 top-full mt-2 w-64 rounded-xl bg-white border border-slate-200 shadow-xl z-20 overflow-hidden">
                  {/* User info header */}
                  <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-4 text-white">
                    <div className="flex items-center gap-3">
                      <div className="h-12 w-12 rounded-full bg-white/20 flex items-center justify-center">
                        <User className="h-6 w-6" />
                      </div>
                      <div>
                        <p className="font-semibold">{employee?.full_name}</p>
                        <p className="text-sm text-blue-200">{employee?.employee_id}</p>
                      </div>
                    </div>
                  </div>
                  {/* Menu items */}
                  <div className="p-2">
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition-colors">
                      <User className="h-4 w-4" />
                      My Profile
                    </button>
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition-colors">
                      <Settings className="h-4 w-4" />
                      Settings
                    </button>
                    <div className="border-t border-slate-100 my-2" />
                    <button
                      className="w-full flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg text-red-600 hover:bg-red-50 transition-colors"
                      onClick={() => {
                        setShowUserMenu(false);
                        logout();
                      }}
                    >
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
