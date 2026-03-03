import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { MainLayout, PublicLayout } from '@/components/layout';
import { DashboardPage } from '@/pages/DashboardPage';
import { AttendancePage } from '@/pages/AttendancePage';
import { LeavePage } from '@/pages/LeavePage';
import { PayslipsPage } from '@/pages/PayslipsPage';
import { JobsListPage } from '@/pages/JobsListPage';
import { JobDetailPage } from '@/pages/JobDetailPage';
import { JobApplicationPage } from '@/pages/JobApplicationPage';
import { ApplicationStatusPage } from '@/pages/ApplicationStatusPage';
import { QRDisplayPage } from '@/pages/QRDisplayPage';
import { Toaster } from 'sonner';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* QR Display for office - standalone page without layout */}
          <Route path="/attendance/qr-display" element={<QRDisplayPage />} />

          {/* Public careers routes - default landing page */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Navigate to="/careers" replace />} />
            <Route path="/careers" element={<JobsListPage />} />
            <Route path="/careers/status" element={<ApplicationStatusPage />} />
            <Route path="/careers/:id" element={<JobDetailPage />} />
            <Route path="/careers/:id/apply" element={<JobApplicationPage />} />
          </Route>

          {/* Login page - redirect to careers (login is now in PublicLayout) */}
          <Route path="/login" element={<Navigate to="/careers" replace />} />

          {/* Protected routes with layout */}
          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/portal" element={<DashboardPage />} />
            <Route path="/portal/attendance" element={<AttendancePage />} />
            <Route path="/portal/leave" element={<LeavePage />} />
            <Route path="/portal/payslips" element={<PayslipsPage />} />
          </Route>

          {/* Catch all - redirect to careers */}
          <Route path="*" element={<Navigate to="/careers" replace />} />
        </Routes>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
