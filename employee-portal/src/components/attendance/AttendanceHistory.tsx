import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CalendarCheck, CalendarX, Clock } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import type { AttendanceRecord } from '@/types/attendance.types';

interface AttendanceHistoryProps {
  records: AttendanceRecord[];
  isLoading: boolean;
}

export function AttendanceHistory({
  records,
  isLoading,
}: AttendanceHistoryProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Attendance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-muted rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (records.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Attendance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-4">
            No attendance records found
          </p>
        </CardContent>
      </Card>
    );
  }

  const getStatusIcon = (record: AttendanceRecord) => {
    if (record.clock_in && record.clock_out) {
      return <CalendarCheck className="h-5 w-5 text-green-600" />;
    }
    if (record.clock_in) {
      return <Clock className="h-5 w-5 text-orange-600" />;
    }
    return <CalendarX className="h-5 w-5 text-red-600" />;
  };

  const getStatusText = (record: AttendanceRecord) => {
    if (record.clock_in && record.clock_out) {
      return 'Complete';
    }
    if (record.clock_in) {
      return 'In Progress';
    }
    return 'Absent';
  };

  const calculateHours = (record: AttendanceRecord): string | null => {
    if (!record.clock_in || !record.clock_out) return null;

    const clockIn = parseISO(`2000-01-01T${record.clock_in}`);
    const clockOut = parseISO(`2000-01-01T${record.clock_out}`);
    const hours = (clockOut.getTime() - clockIn.getTime()) / (1000 * 60 * 60);
    return hours.toFixed(2);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Recent Attendance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {records.map((record) => {
            const hours = calculateHours(record);
            return (
              <div
                key={record.id}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  {getStatusIcon(record)}
                  <div>
                    <p className="font-medium">
                      {format(parseISO(record.date), 'EEE, MMM d')}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {record.clock_in || '--:--'} - {record.clock_out || '--:--'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{getStatusText(record)}</p>
                  {hours && (
                    <p className="text-xs text-muted-foreground">{hours} hrs</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default AttendanceHistory;
