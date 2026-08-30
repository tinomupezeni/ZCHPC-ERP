import { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Briefcase,
  LogIn,
  FileSearch,
  User,
  Lock,
  Loader2,
  AlertCircle,
  Building2,
  ChevronRight,
  Menu,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { path: '/careers', label: 'View Jobs', icon: Briefcase, description: 'Browse open positions' },
  { path: '/careers/status', label: 'Application Status', icon: FileSearch, description: 'Track your application' },
];

export function PublicLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [ecNumber, setEcNumber] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await login({
        ec_number: ecNumber.trim().toUpperCase(),
        password,
      });
      navigate('/portal', { replace: true });
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Login failed. Please check your credentials.';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      {/* Top Header Bar */}
      <header className="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <img src="/logo.png" alt="ZCHPC" className="h-10 w-auto" />
              <div>
                <span className="font-bold text-lg tracking-tight">ZCHPC ERP</span>
                <span className="hidden sm:inline text-blue-200 ml-2 text-sm">Career Portal</span>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'text-blue-100 hover:bg-white/10 hover:text-white'
                    )
                  }
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              ))}
              <div className="w-px h-6 bg-blue-400/50 mx-2" />
              <Button
                onClick={() => setShowLogin(!showLogin)}
                variant="ghost"
                className="text-white hover:bg-white/20 hover:text-white gap-2"
              >
                <LogIn className="h-4 w-4" />
                Employee Login
              </Button>
            </nav>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-blue-500/30 bg-blue-700/50 backdrop-blur">
            <div className="px-4 py-3 space-y-2">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all',
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'text-blue-100 hover:bg-white/10'
                    )
                  }
                >
                  <item.icon className="h-5 w-5" />
                  <div>
                    <div>{item.label}</div>
                    <div className="text-xs text-blue-200">{item.description}</div>
                  </div>
                </NavLink>
              ))}
              <button
                onClick={() => {
                  setShowLogin(!showLogin);
                  setMobileMenuOpen(false);
                }}
                className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-blue-100 hover:bg-white/10 w-full"
              >
                <LogIn className="h-5 w-5" />
                <div>
                  <div>Employee Login</div>
                  <div className="text-xs text-blue-200">Access your portal</div>
                </div>
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Login Panel (Slide down) */}
      {showLogin && (
        <div className="bg-gradient-to-r from-slate-800 via-slate-900 to-slate-800 border-b border-slate-700 shadow-xl">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="max-w-md mx-auto">
              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold text-white">Employee Portal Login</h3>
                <p className="text-sm text-slate-400">Sign in with your EC number</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-4">
                {error && (
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/20 text-red-300 text-sm border border-red-500/30">
                    <AlertCircle className="h-4 w-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="ec-number" className="text-slate-300 text-sm">
                      EC Number
                    </Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                      <Input
                        id="ec-number"
                        type="text"
                        placeholder="EMP0001"
                        value={ecNumber}
                        onChange={(e) => setEcNumber(e.target.value)}
                        className="pl-10 bg-slate-800 border-slate-600 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500"
                        autoComplete="username"
                        required
                        disabled={isSubmitting}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-slate-300 text-sm">
                      Password
                    </Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                      <Input
                        id="password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="pl-10 bg-slate-800 border-slate-600 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500"
                        autoComplete="current-password"
                        required
                        disabled={isSubmitting}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <a href="#" className="text-sm text-blue-400 hover:text-blue-300 hover:underline">
                    Forgot password?
                  </a>
                  <Button
                    type="submit"
                    disabled={isSubmitting || !ecNumber || !password}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Signing in...
                      </>
                    ) : (
                      <>
                        Sign In
                        <ChevronRight className="ml-1 h-4 w-4" />
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section (only on main careers page) */}
      {location.pathname === '/careers' && (
        <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
            <div className="max-w-3xl">
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
                Build Your Career With Us
              </h1>
              <p className="text-lg md:text-xl text-blue-100 mb-6">
                Join Zimbabwe Centre for High Performance Computing and be part of a team
                driving innovation and excellence in technology.
              </p>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur rounded-lg px-4 py-2">
                  <Briefcase className="h-5 w-5 text-blue-200" />
                  <span className="text-sm font-medium">Competitive Salaries</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur rounded-lg px-4 py-2">
                  <Building2 className="h-5 w-5 text-blue-200" />
                  <span className="text-sm font-medium">Growth Opportunities</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur rounded-lg px-4 py-2">
                  <User className="h-5 w-5 text-blue-200" />
                  <span className="text-sm font-medium">Great Team Culture</span>
                </div>
              </div>
            </div>
          </div>
          {/* Wave decoration */}
          <svg className="w-full h-8 md:h-12" viewBox="0 0 1440 48" fill="none" preserveAspectRatio="none">
            <path
              d="M0 48h1440V0c-158 36-411 48-720 48S158 36 0 0v48z"
              fill="currentColor"
              className="text-slate-50"
            />
          </svg>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <img src="/logo.png" alt="ZCHPC" className="h-10 w-auto" />
                <span className="font-bold text-white">ZCHPC ERP</span>
              </div>
              <p className="text-sm">
                Zimbabwe Centre for High Performance Computing - Advancing technology and innovation.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-3">Quick Links</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <NavLink to="/careers" className="hover:text-white transition-colors">
                    View Jobs
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/careers/status" className="hover:text-white transition-colors">
                    Application Status
                  </NavLink>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-3">Contact HR</h4>
              <ul className="space-y-2 text-sm">
                <li>Email: hr@zchpc-erp.zw</li>
                <li>Phone: +263 242 123 456</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 mt-8 pt-6 text-center text-sm">
            <p>&copy; {new Date().getFullYear()} Zimbabwe Centre for High Performance Computing. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default PublicLayout;
