import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FileText, Download, Eye, CheckCircle, Clock } from 'lucide-react';
import type { PayslipListItem, PayslipStatus } from '@/types/payslip.types';

interface PayslipCardProps {
  payslip: PayslipListItem;
  onView: (id: number) => void;
  onDownload: (id: number) => void;
  isDownloading?: boolean;
}

export function PayslipCard({
  payslip,
  onView,
  onDownload,
  isDownloading,
}: PayslipCardProps) {
  const getStatusBadge = (status: PayslipStatus) => {
    switch (status) {
      case 'Paid':
        return (
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <CheckCircle className="h-3 w-3 mr-1" />
            Paid
          </Badge>
        );
      case 'Processed':
        return (
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            <Clock className="h-3 w-3 mr-1" />
            Processed
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatCurrency = (amount: number, currency: 'USD' | 'ZiG') => {
    if (currency === 'USD') {
      return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `ZiG ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            {/* Icon */}
            <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <FileText className="h-6 w-6 text-primary" />
            </div>

            {/* Details */}
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-semibold">{payslip.period_display}</h3>
                {getStatusBadge(payslip.status)}
              </div>

              <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
                <div>
                  <span className="text-muted-foreground">Gross: </span>
                  <span className="font-medium">
                    {formatCurrency(payslip.base_salary_usd, 'USD')}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Net: </span>
                  <span className="font-medium text-green-600">
                    {formatCurrency(payslip.net_salary_usd, 'USD')}
                  </span>
                </div>
              </div>

              {payslip.net_salary_zig > 0 && (
                <p className="text-xs text-muted-foreground">
                  ZiG Net: {formatCurrency(payslip.net_salary_zig, 'ZiG')}
                </p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2 flex-shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onView(payslip.id)}
            >
              <Eye className="h-4 w-4 mr-1" />
              View
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDownload(payslip.id)}
              disabled={isDownloading}
            >
              <Download className="h-4 w-4 mr-1" />
              Download
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default PayslipCard;
