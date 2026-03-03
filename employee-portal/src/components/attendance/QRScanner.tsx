import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { QrCode, Camera, X, Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { Html5QrcodeScanner, Html5QrcodeScanType } from 'html5-qrcode';
import { attendanceService } from '@/services/attendance.service';
import { toast } from 'sonner';

interface QRScannerProps {
  onSuccess: () => void;
  disabled?: boolean;
}

type ScanStatus = 'idle' | 'scanning' | 'processing' | 'success' | 'error';

export function QRScanner({ onSuccess, disabled }: QRScannerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [status, setStatus] = useState<ScanStatus>('idle');
  const [message, setMessage] = useState('');
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);
  const scannerContainerId = 'qr-reader';

  useEffect(() => {
    if (isOpen && status === 'scanning') {
      // Small delay to ensure the container is mounted
      const timer = setTimeout(() => {
        try {
          scannerRef.current = new Html5QrcodeScanner(
            scannerContainerId,
            {
              fps: 10,
              qrbox: { width: 250, height: 250 },
              aspectRatio: 1,
              supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
              rememberLastUsedCamera: true,
            },
            false
          );

          scannerRef.current.render(
            async (decodedText) => {
              // Stop scanning immediately
              if (scannerRef.current) {
                await scannerRef.current.clear();
                scannerRef.current = null;
              }
              handleScan(decodedText);
            },
            (errorMessage) => {
              // Ignore scan errors - they happen constantly when no QR is in view
              console.debug('QR scan error:', errorMessage);
            }
          );
        } catch {
          setStatus('error');
          setMessage('Failed to initialize camera');
        }
      }, 100);

      return () => {
        clearTimeout(timer);
        if (scannerRef.current) {
          scannerRef.current.clear().catch(console.error);
          scannerRef.current = null;
        }
      };
    }
  }, [isOpen, status]);

  const handleScan = async (token: string) => {
    setStatus('processing');
    setMessage('Verifying QR code...');

    try {
      const response = await attendanceService.qrClockIn(token);
      setStatus('success');
      setMessage(response.message);
      toast.success(response.message);

      // Close after 2 seconds and trigger refresh
      setTimeout(() => {
        setIsOpen(false);
        setStatus('idle');
        onSuccess();
      }, 2000);
    } catch (error) {
      setStatus('error');
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to clock in. Please try again.';
      setMessage(errorMessage);
      toast.error(errorMessage);

      // Allow retry after 3 seconds
      setTimeout(() => {
        setStatus('scanning');
        setMessage('');
      }, 3000);
    }
  };

  const handleOpen = () => {
    setIsOpen(true);
    setStatus('scanning');
    setMessage('');
  };

  const handleClose = () => {
    if (scannerRef.current) {
      scannerRef.current.clear().catch(console.error);
      scannerRef.current = null;
    }
    setIsOpen(false);
    setStatus('idle');
    setMessage('');
  };

  return (
    <>
      <Card className="border-dashed border-2 border-blue-200 bg-blue-50/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2 text-blue-700">
            <QrCode className="h-5 w-5" />
            QR Code Clock In
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Scan the QR code displayed at the office to clock in securely.
          </p>
          <Button
            onClick={handleOpen}
            disabled={disabled}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            <Camera className="mr-2 h-4 w-4" />
            Scan QR Code
          </Button>
        </CardContent>
      </Card>

      <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5 text-blue-600" />
              Scan Attendance QR Code
            </DialogTitle>
            <DialogDescription>
              Point your camera at the QR code displayed at the office
            </DialogDescription>
          </DialogHeader>

          <div className="relative min-h-[320px] flex items-center justify-center bg-slate-100 rounded-lg overflow-hidden">
            {status === 'scanning' && (
              <div id={scannerContainerId} className="w-full" />
            )}

            {status === 'processing' && (
              <div className="text-center p-8">
                <Loader2 className="h-16 w-16 text-blue-600 animate-spin mx-auto mb-4" />
                <p className="text-lg font-medium text-slate-700">{message}</p>
              </div>
            )}

            {status === 'success' && (
              <div className="text-center p-8">
                <div className="h-20 w-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="h-12 w-12 text-green-600" />
                </div>
                <p className="text-lg font-medium text-green-700">{message}</p>
              </div>
            )}

            {status === 'error' && (
              <div className="text-center p-8">
                <div className="h-20 w-20 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                  <XCircle className="h-12 w-12 text-red-600" />
                </div>
                <p className="text-lg font-medium text-red-700">{message}</p>
                <p className="text-sm text-muted-foreground mt-2">Retrying in a moment...</p>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertCircle className="h-4 w-4" />
              <span>QR codes rotate every 30 seconds</span>
            </div>
            <Button variant="outline" onClick={handleClose}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default QRScanner;
