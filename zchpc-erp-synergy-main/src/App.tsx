import { useEffect, useState } from "react";
import { useLocation, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LoginPage from "./pages/LoginPage";
import Dashboard from "./pages/Dashboard";
import SalesPage from "./pages/SalesPage";
import AccountingPage from "./pages/AccountingPage";
import ProcurementPage from "./pages/ProcurementPage";
import HRPage from "./pages/HRPage";
import InventoryPage from "./pages/InventoryPage";
import SettingsPage from "./pages/SettingsPage";
import NotFound from "./pages/NotFound";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import MainLayout from "./components/MainLayout";
import PayrollPage from "./pages/PayrollPage";

const queryClient = new QueryClient();

const App = () => {
  const [openTab, setOpenTab] = useState("");
  const location = useLocation();

  useEffect(() => {
    setOpenTab(location.pathname);
  }, [location.pathname]);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <MainLayout setOpenTab={setOpenTab}>
                    <Dashboard />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales"
              element={
                <ProtectedRoute requiredPermission={["sales", "admin"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <SalesPage />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/accounting/*"
              element={
                <ProtectedRoute requiredPermission={["accountant", "admin"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <AccountingPage openTab={openTab} />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/payroll/*"
              element={
                <ProtectedRoute requiredPermission={["accountant", "hr", "admin"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <PayrollPage openTab={openTab} />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/procurement/*"
              element={
                <ProtectedRoute requiredPermission={["procurement", "admin"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <ProcurementPage />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/*"
              element={
                <ProtectedRoute requiredPermission={["hr", "admin"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <HRPage openTab={openTab} />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/*"
              element={
                <ProtectedRoute requiredPermission={["inventory", "admin"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <InventoryPage />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute requiredPermission={["admin"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <SettingsPage />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
