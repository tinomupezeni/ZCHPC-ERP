import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/layout';
import { ClockStatus } from '@/components/attendance/ClockStatus';
import { AttendanceSummaryCard } from '@/components/attendance/AttendanceSummaryCard';
import { AttendanceHistory } from '@/components/attendance/AttendanceHistory';
import { QRScanner } from '@/components/attendance/QRScanner';
import { attendanceService } from '@/services/attendance.service';
import type {
  AttendanceStatus,
  AttendanceSummary,
  AttendanceRecord,
} from '@/types/attendance.types';

export function AttendancePage() {
  const [status, setStatus] = useState<AttendanceStatus | null>(null);
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [history, setHistory] = useState<AttendanceRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isClockin, setIsClockin] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statusData, summaryData, historyData] = await Promise.all([
        attendanceService.getStatus(),
        attendanceService.getSummary(),
        attendanceService.getHistory({ page_size: 10 }),
      ]);
      setStatus(statusData);
      setSummary(summaryData);
      setHistory(historyData.records);
    } catch (error) {
      console.error('Failed to load attendance data:', error);
      toast.error('Failed to load attendance data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClock = async () => {
    setIsClockin(true);
    try {
      const response = await attendanceService.clock();
      toast.success(response.message);

      // Refresh status and history
      const [newStatus, newHistory] = await Promise.all([
        attendanceService.getStatus(),
        attendanceService.getHistory({ page_size: 10 }),
      ]);
      setStatus(newStatus);
      setHistory(newHistory.records);
    } catch (error) {
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to clock in/out';
      toast.error(errorMessage);
    } finally {
      setIsClockin(false);
    }
  };

  const handleQRSuccess = async () => {
    // Refresh data after successful QR clock in
    try {
      const [newStatus, newHistory] = await Promise.all([
        attendanceService.getStatus(),
        attendanceService.getHistory({ page_size: 10 }),
      ]);
      setStatus(newStatus);
      setHistory(newHistory.records);
    } catch (error) {
      console.error('Failed to refresh data:', error);
    }
  };

  // Determine if QR scan should be disabled
  const isQRDisabled = status?.status === 'clocked_out';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        description="Track your daily attendance and view history"
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Clock In/Out Section */}
        <div className="lg:col-span-1">
          <ClockStatus
            status={status}
            isLoading={isLoading}
            isClockin={isClockin}
            onClock={handleClock}
          />
        </div>

        {/* QR Scanner Section */}
        <div className="lg:col-span-1">
          <QRScanner onSuccess={handleQRSuccess} disabled={isQRDisabled} />
        </div>

        {/* Summary Section */}
        <div className="lg:col-span-1">
          <AttendanceSummaryCard summary={summary} isLoading={isLoading} />
        </div>

        {/* History Section */}
        <div className="lg:col-span-1">
          <AttendanceHistory records={history} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}

export default AttendancePage;
