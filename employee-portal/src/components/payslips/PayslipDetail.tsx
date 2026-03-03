import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  Download,
  User,
  Building,
  Briefcase,
  Calendar,
  CheckCircle,
  Clock,
} from 'lucide-react';
import type { PayslipDetail as PayslipDetailType, PayslipStatus } from '@/types/payslip.types';

interface PayslipDetailProps {
  payslip: PayslipDetailType;
  onBack: () => void;
  onDownload: () => void;
  isDownloading?: boolean;
}

export function PayslipDetail({
  payslip,
  onBack,
  onDownload,
  isDownloading,
}: PayslipDetailProps) {
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
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Payslips
        </Button>
        <Button onClick={onDownload} disabled={isDownloading}>
          <Download className="h-4 w-4 mr-2" />
          Download
        </Button>
      </div>

      {/* Employee Info */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <CardTitle className="text-lg">Payslip - {payslip.period_display}</CardTitle>
            {getStatusBadge(payslip.status)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-muted-foreground">Employee</p>
                <p className="font-medium">{payslip.employee_name}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-muted-foreground">Position</p>
                <p className="font-medium">{payslip.position}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Building className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-muted-foreground">Department</p>
                <p className="font-medium">{payslip.department}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-muted-foreground">Period</p>
                <p className="font-medium">{payslip.period_display}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Earnings */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-green-700">Earnings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b">
              <span>Base Salary</span>
              <div className="text-right">
                <p className="font-medium">{formatCurrency(payslip.earnings.base_salary.usd, 'USD')}</p>
                {payslip.earnings.base_salary.zig > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {formatCurrency(payslip.earnings.base_salary.zig, 'ZiG')}
                  </p>
                )}
              </div>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>Allowances</span>
              <div className="text-right">
                <p className="font-medium">{formatCurrency(payslip.earnings.allowances.usd, 'USD')}</p>
                {payslip.earnings.allowances.zig > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {formatCurrency(payslip.earnings.allowances.zig, 'ZiG')}
                  </p>
                )}
              </div>
            </div>
            <div className="flex justify-between items-center py-2 bg-green-50 px-2 rounded">
              <span className="font-semibold text-green-700">Gross Salary</span>
              <div className="text-right">
                <p className="font-bold text-green-700">
                  {formatCurrency(payslip.earnings.gross.usd, 'USD')}
                </p>
                {payslip.earnings.gross.zig > 0 && (
                  <p className="text-xs text-green-600">
                    {formatCurrency(payslip.earnings.gross.zig, 'ZiG')}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Deductions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-red-700">Deductions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b">
              <span>PAYE (Tax)</span>
              <div className="text-right">
                <p className="font-medium">{formatCurrency(payslip.deductions.paye.usd, 'USD')}</p>
                {payslip.deductions.paye.zig > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {formatCurrency(payslip.deductions.paye.zig, 'ZiG')}
                  </p>
                )}
              </div>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>AIDS Levy</span>
              <div className="text-right">
                <p className="font-medium">{formatCurrency(payslip.deductions.aids_levy.usd, 'USD')}</p>
                {payslip.deductions.aids_levy.zig > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {formatCurrency(payslip.deductions.aids_levy.zig, 'ZiG')}
                  </p>
                )}
              </div>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>NSSA (Employee)</span>
              <div className="text-right">
                <p className="font-medium">{formatCurrency(payslip.deductions.nssa_employee.usd, 'USD')}</p>
                {payslip.deductions.nssa_employee.zig > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {formatCurrency(payslip.deductions.nssa_employee.zig, 'ZiG')}
                  </p>
                )}
              </div>
            </div>
            {payslip.deductions.other_deductions.usd > 0 && (
              <div className="flex justify-between items-center py-2 border-b">
                <span>Other Deductions</span>
                <div className="text-right">
                  <p className="font-medium">{formatCurrency(payslip.deductions.other_deductions.usd, 'USD')}</p>
                </div>
              </div>
            )}
            <div className="flex justify-between items-center py-2 bg-red-50 px-2 rounded">
              <span className="font-semibold text-red-700">Total Deductions</span>
              <div className="text-right">
                <p className="font-bold text-red-700">
                  {formatCurrency(payslip.deductions.total.usd, 'USD')}
                </p>
                {payslip.deductions.total.zig > 0 && (
                  <p className="text-xs text-red-600">
                    {formatCurrency(payslip.deductions.total.zig, 'ZiG')}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Net Pay Summary */}
      <Card className="bg-gradient-to-r from-primary/5 to-primary/10">
        <CardContent className="p-6">
          <div className="text-center space-y-2">
            <p className="text-muted-foreground">Net Salary</p>
            <p className="text-4xl font-bold text-primary">
              {formatCurrency(payslip.summary.net_salary.usd, 'USD')}
            </p>
            {payslip.summary.net_salary.zig > 0 && (
              <p className="text-lg text-muted-foreground">
                {formatCurrency(payslip.summary.net_salary.zig, 'ZiG')}
              </p>
            )}
            {payslip.exchange_rate > 0 && (
              <p className="text-xs text-muted-foreground">
                Exchange Rate: 1 USD = {payslip.exchange_rate} ZiG
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Notes */}
      {payslip.notes && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{payslip.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default PayslipDetail;
