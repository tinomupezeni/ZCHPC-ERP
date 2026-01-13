import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import {
  BarChart3,
  Eye,
  EyeOff,
  Lock,
  Mail,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { useLogin } from "@/hooks/useLogin";

const LoginPage = () => {
  const {
    email,
    setEmail,
    password,
    setPassword,
    viewPassword,
    setViewPassword,
    isSubmitting,
    handleLogin,
  } = useLogin();

  return (
    <div className="min-h-screen w-full flex overflow-hidden bg-[#0a0a0b]">
      {/* Left Side: Brand & Visuals (The "outstanding" part) */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-blue-600 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-blue-700 to-indigo-950 z-10 opacity-90" />

        {/* Abstract "Neural Network" background effect */}
        <div className="absolute inset-0 z-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]" />

        <div className="relative z-20 w-full flex flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-2">
            <div className="bg-white/10 backdrop-blur-md p-2 rounded-lg border border-white/20">
              <Zap className="h-8 w-8 text-blue-300" />
            </div>
            <span className="text-2xl font-bold tracking-tighter">ZCHPC</span>
          </div>

          <div className="space-y-6">
            <h2 className="text-5xl font-extrabold leading-tight tracking-tight">
              Enterprise Resource <br />
              <span className="text-blue-300">Intelligent Management.</span>
            </h2>
            <p className="text-lg text-blue-100/80 max-w-md leading-relaxed">
              Securely access Zimbabwe's premier high-performance computing ERP
              infrastructure. Unified data for HR, Payroll, and Operations.
            </p>
            <div className="flex gap-4 pt-4">
              <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-full border border-white/10">
                <ShieldCheck className="h-4 w-4 text-green-400" />
                <span className="text-sm">Bank-grade Security</span>
              </div>
              <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-full border border-white/10">
                <BarChart3 className="h-4 w-4 text-blue-300" />
                <span className="text-sm">Real-time Analytics</span>
              </div>
            </div>
          </div>

          <div className="text-sm text-blue-200/50">
            © 2025 ZCHPC. All rights reserved.
          </div>
        </div>
      </div>

      {/* Right Side: Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-background relative">
        {/* Subtle glow effect behind the card */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-500/10 rounded-full blur-[120px]" />

        <div className="w-full max-w-sm space-y-8 relative z-10">
          <div className="text-center lg:text-left">
            <h1 className="text-3xl font-bold text-foreground tracking-tight">
              Welcome Back
            </h1>
            <p className="text-muted-foreground mt-2">
              Enter your corporate credentials to continue
            </p>
          </div>

          <Card className="border-border/50 bg-card/50 backdrop-blur-xl shadow-2xl">
            <form onSubmit={handleLogin}>
              <CardContent className="pt-6 space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email">Work Email</Label>
                  <div className="relative group">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="admin@zchpc.com"
                      className="pl-10 h-12 bg-background/50"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password">Password</Label>
                    <a
                      href="#"
                      className="text-xs text-primary hover:underline"
                    >
                      Forgot password?
                    </a>
                  </div>
                  <div className="relative group">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                    <Input
                      id="password"
                      type={viewPassword ? "text" : "password"}
                      placeholder="••••••••"
                      className="pl-10 h-12 bg-background/50"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setViewPassword(!viewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary"
                    >
                      {viewPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full h-12 text-md font-semibold bg-blue-600 hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <span className="flex items-center gap-2">
                      <Zap className="h-4 w-4 animate-pulse text-blue-200" />{" "}
                      Authenticating...
                    </span>
                  ) : (
                    "Sign In to ERP"
                  )}
                </Button>
              </CardContent>
            </form>
          </Card>

          <p className="text-center text-sm text-muted-foreground">
            Problems logging in?{" "}
            <span className="text-primary cursor-pointer font-medium hover:underline">
              Contact IT Support
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
