import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Clock, LogIn, LogOut, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import type { AttendanceStatus } from '@/types/attendance.types';

interface ClockStatusProps {
  status: AttendanceStatus | null;
  isLoading: boolean;
  isClockin: boolean;
  onClock: () => void;
}

export function ClockStatus({
  status,
  isLoading,
  isClockin,
  onClock,
}: ClockStatusProps) {
  const getStatusDisplay = () => {
    if (!status) return { text: 'Loading...', color: 'text-muted-foreground' };

    switch (status.status) {
      case 'clocked_in':
        return { text: 'Clocked In', color: 'text-green-600' };
      case 'clocked_out':
        return { text: 'Clocked Out', color: 'text-blue-600' };
      default:
        return { text: 'Not Clocked In', color: 'text-orange-600' };
    }
  };

  const statusDisplay = getStatusDisplay();
  const canClockOut = status?.status === 'clocked_in';
  const canClockIn = status?.status === 'not_clocked';
  const isDisabled = status?.status === 'clocked_out';

  return (
    <Card className="bg-gradient-to-br from-primary/5 to-primary/10">
      <CardContent className="p-6">
        <div className="flex flex-col items-center text-center space-y-4">
          {/* Clock Icon */}
          <div className="h-20 w-20 rounded-full bg-card flex items-center justify-center shadow-lg">
            <Clock className="h-10 w-10 text-primary" />
          </div>

          {/* Current Time */}
          <div>
            <p className="text-3xl font-bold">
              {format(new Date(), 'HH:mm')}
            </p>
            <p className="text-sm text-muted-foreground">
              {format(new Date(), 'EEEE, MMMM d, yyyy')}
            </p>
          </div>

          {/* Status */}
          <div className={`text-lg font-semibold ${statusDisplay.color}`}>
            {statusDisplay.text}
          </div>

          {/* Clock Times */}
          {status && (status.clock_in || status.clock_out) && (
            <div className="flex gap-6 text-sm">
              {status.clock_in && (
                <div className="flex items-center gap-2">
                  <LogIn className="h-4 w-4 text-green-600" />
                  <span>In: {status.clock_in}</span>
                </div>
              )}
              {status.clock_out && (
                <div className="flex items-center gap-2">
                  <LogOut className="h-4 w-4 text-blue-600" />
                  <span>Out: {status.clock_out}</span>
                </div>
              )}
            </div>
          )}

          {/* Hours Worked */}
          {status?.hours_worked && (
            <p className="text-sm text-muted-foreground">
              Total hours: {status.hours_worked.toFixed(2)}
            </p>
          )}

          {/* Clock Button */}
          <Button
            size="lg"
            className={`w-full max-w-xs ${
              canClockOut
                ? 'bg-blue-600 hover:bg-blue-700'
                : canClockIn
                ? 'bg-green-600 hover:bg-green-700'
                : ''
            }`}
            disabled={isDisabled || isLoading || isClockin}
            onClick={onClock}
          >
            {isClockin ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : canClockOut ? (
              <>
                <LogOut className="mr-2 h-4 w-4" />
                Clock Out
              </>
            ) : canClockIn ? (
              <>
                <LogIn className="mr-2 h-4 w-4" />
                Clock In
              </>
            ) : (
              'Completed for Today'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default ClockStatus;
