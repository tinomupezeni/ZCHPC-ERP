import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
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
import { useEffect, useState } from "react";
import PayrollPage from "./pages/PayrollPage";

const queryClient = new QueryClient();

const App = () => {
  const [openTab, setOpenTab] = useState("");

  // Set openTab based on the initial URL hash when the component mounts
  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      setOpenTab(hash); // Set the initial hash
    }

    // Define the hashchange handler to update openTab whenever the hash changes
    const handleHashChange = () => {
      const newHash = window.location.hash;
      setOpenTab(newHash); // Update openTab whenever the hash changes
    };

    // Listen for changes in the hash
    window.addEventListener("hashchange", handleHashChange);

    // Cleanup the event listener on unmount
    return () => {
      window.removeEventListener("hashchange", handleHashChange);
    };
  }, []); // The empty dependency array ensures this effect runs once on mount

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              {/* Public route - redirect to dashboard if authenticated */}
              <Route path="/" element={<Navigate to="/login" replace />} />
              <Route path="/login" element={<LoginPage />} />

              {/* Protected routes inside MainLayout */}
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
                  <ProtectedRoute requiredPermission="sales">
                    <MainLayout setOpenTab={setOpenTab}>
                      <SalesPage />
                    </MainLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/accounting"
                element={
                  <ProtectedRoute requiredPermission="accounting">
                    <MainLayout setOpenTab={setOpenTab}>
                      <AccountingPage openTab={openTab} />
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/payroll"
                element={
                  <ProtectedRoute requiredPermission="accounting">
                    <MainLayout setOpenTab={setOpenTab}>
                      <PayrollPage openTab={openTab} />
                    </MainLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/procurement"
                element={
                  <ProtectedRoute requiredPermission="procurement">
                    <MainLayout setOpenTab={setOpenTab}>
                      <ProcurementPage />
                    </MainLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/hr"
                element={
                  <ProtectedRoute requiredPermission="hr">
                    <MainLayout setOpenTab={setOpenTab}>
                      <HRPage openTab={openTab} />
                    </MainLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/inventory"
                element={
                  <ProtectedRoute requiredPermission="inventory">
                    <MainLayout setOpenTab={setOpenTab}>
                      <InventoryPage />
                    </MainLayout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/settings"
                element={
                  <ProtectedRoute requiredPermission="admin">
                    <MainLayout setOpenTab={setOpenTab}>
                      <SettingsPage />
                    </MainLayout>
                  </ProtectedRoute>
                }
              />

              {/* Catch-all route */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
