import { useState, useEffect, useCallback } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { attendanceService } from '@/services/attendance.service';
import type { QRTokenResponse } from '@/services/attendance.service';
import { format } from 'date-fns';
import { RefreshCw, Clock, Shield } from 'lucide-react';

export function QRDisplayPage() {
  const [token, setToken] = useState<QRTokenResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [timeRemaining, setTimeRemaining] = useState(30);

  const fetchToken = useCallback(async () => {
    try {
      const data = await attendanceService.getQRToken();
      setToken(data);
      setTimeRemaining(data.time_remaining);
      setError(null);
    } catch {
      setError('Failed to load QR code. Please check your connection.');
    }
  }, []);

  // Fetch token on mount and when it expires
  useEffect(() => {
    fetchToken();

    // Refresh token every 25 seconds (before the 30 second expiry)
    const tokenInterval = setInterval(fetchToken, 25000);

    return () => clearInterval(tokenInterval);
  }, [fetchToken]);

  // Update current time every second
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
      setTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timeInterval);
  }, []);

  // Progress percentage for the circular indicator
  const progressPercent = (timeRemaining / 30) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex flex-col">
      {/* Header */}
      <header className="px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <img src="/logo.png" alt="ZCHPC" className="h-14 w-auto" />
          <div>
            <h1 className="text-2xl font-bold text-white">ZCHPC</h1>
            <p className="text-blue-200 text-sm">Attendance Check-In</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-green-500/20 px-4 py-2 rounded-full border border-green-400/30">
          <Shield className="h-5 w-5 text-green-400" />
          <span className="text-green-300 font-medium">Secure QR</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-8 pb-8">
        <div className="text-center">
          {/* Current Time Display */}
          <div className="mb-8">
            <div className="text-7xl font-bold text-white tracking-tight">
              {format(currentTime, 'HH:mm:ss')}
            </div>
            <div className="text-xl text-blue-200 mt-2">
              {format(currentTime, 'EEEE, MMMM d, yyyy')}
            </div>
          </div>

          {/* QR Code Container */}
          <div className="relative inline-block">
            {/* Circular progress indicator */}
            <svg
              className="absolute -inset-4 w-[calc(100%+2rem)] h-[calc(100%+2rem)]"
              viewBox="0 0 100 100"
            >
              <circle
                cx="50"
                cy="50"
                r="48"
                fill="none"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="2"
              />
              <circle
                cx="50"
                cy="50"
                r="48"
                fill="none"
                stroke={timeRemaining > 10 ? '#22c55e' : timeRemaining > 5 ? '#eab308' : '#ef4444'}
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray={`${progressPercent * 3.02} 302`}
                transform="rotate(-90 50 50)"
                className="transition-all duration-1000"
              />
            </svg>

            {/* QR Code */}
            <div className="bg-white p-6 rounded-2xl shadow-2xl relative">
              {error ? (
                <div className="w-64 h-64 flex items-center justify-center">
                  <div className="text-center text-red-500">
                    <RefreshCw className="h-12 w-12 mx-auto mb-2 animate-spin" />
                    <p>{error}</p>
                  </div>
                </div>
              ) : token ? (
                <QRCodeSVG
                  value={token.token}
                  size={256}
                  level="H"
                  includeMargin={false}
                />
              ) : (
                <div className="w-64 h-64 flex items-center justify-center">
                  <RefreshCw className="h-12 w-12 text-blue-500 animate-spin" />
                </div>
              )}
            </div>
          </div>

          {/* Timer Display */}
          <div className="mt-8 flex items-center justify-center gap-3">
            <Clock className={`h-6 w-6 ${timeRemaining > 10 ? 'text-green-400' : timeRemaining > 5 ? 'text-yellow-400' : 'text-red-400'}`} />
            <span className={`text-2xl font-bold ${timeRemaining > 10 ? 'text-green-400' : timeRemaining > 5 ? 'text-yellow-400' : 'text-red-400'}`}>
              Refreshes in {timeRemaining}s
            </span>
          </div>

          {/* Instructions */}
          <div className="mt-8 max-w-md mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-3">How to Clock In</h3>
              <ol className="text-blue-100 text-left space-y-2">
                <li className="flex items-start gap-3">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold shrink-0">1</span>
                  <span>Open the ZCHPC Employee Portal on your phone</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold shrink-0">2</span>
                  <span>Go to Attendance and tap "Scan QR Code"</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold shrink-0">3</span>
                  <span>Point your camera at this QR code</span>
                </li>
              </ol>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-8 py-4 text-center text-blue-300/50 text-sm">
        QR code rotates every 30 seconds for security &bull; © {new Date().getFullYear()} ZCHPC
      </footer>
    </div>
  );
}

export default QRDisplayPage;
