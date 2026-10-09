import { useEffect, useState } from "react";
import { useLocation, Routes, Route, Navigate } from "react-router-dom";
// import { Toaster } from "@/components/ui/toaster";
import { Toaster } from "sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LoginPage from "./pages/LoginPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";
import Dashboard from "./pages/Dashboard";
import SalesPage from "./pages/SalesPage";
import AccountingPage from "./pages/AccountingPage";
import ProcurementPage from "./components/Procurement/ProcurementPage";
import HRPage from "./pages/HRPage";
import InventoryPage from "./pages/InventoryPage";
import SettingsPage from "./pages/SettingsPage";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./components/ProtectedRoute";
import { MainLayout } from "./layout/MainLayout";
import PayrollPage from "./pages/PayrollPage";
import ModulesPage from "./pages/ModulesPage";

const queryClient = new QueryClient();

const App = () => {
  const [openTab, setOpenTab] = useState("");
  const location = useLocation();

  useEffect(() => {
    setOpenTab(location.pathname);
  }, [location.pathname]);

  return (
    <QueryClientProvider client={queryClient}>
      <>
        <TooltipProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<LoginPage />} />
            {/* REM-07: replacing a temporary password (no role/permission gate) */}
            <Route path="/change-password" element={<ChangePasswordPage />} />
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
                <ProtectedRoute requiredPermission={["sales"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <SalesPage />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/accounting/*"
              element={
                <ProtectedRoute requiredPermission={["accounts"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <AccountingPage openTab={openTab} />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/payroll/*"
              element={
                <ProtectedRoute
                  requiredPermission={["payroll"]}
                >
                  <MainLayout setOpenTab={setOpenTab}>
                    <PayrollPage openTab={openTab} />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/procurement/*"
              element={
                <ProtectedRoute requiredPermission={["procurement"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <ProcurementPage openTab={openTab} />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/*"
              element={
                <ProtectedRoute requiredPermission={["hr"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <HRPage openTab={openTab} />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/*"
              element={
                <ProtectedRoute requiredPermission={["inventory"]}>
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
            <Route
              path="/modules"
              element={
                <ProtectedRoute requiredPermission={["admin"]}>
                  <MainLayout setOpenTab={setOpenTab}>
                    <ModulesPage />
                  </MainLayout>
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </TooltipProvider>
      </>
      <Toaster position="top-right" richColors closeButton />
    </QueryClientProvider>
  );
};

export default App;
