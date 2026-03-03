import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/layout';
import { Card, CardContent } from '@/components/ui/card';
import { PayslipsList, PayslipDetail } from '@/components/payslips';
import { payslipService } from '@/services/payslip.service';
import { DollarSign, TrendingDown, Wallet } from 'lucide-react';
import type {
  PayslipListItem,
  PayslipDetail as PayslipDetailType,
  PayslipYearSummary,
} from '@/types/payslip.types';

export function PayslipsPage() {
  const [payslips, setPayslips] = useState<PayslipListItem[]>([]);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [yearSummary, setYearSummary] = useState<PayslipYearSummary | null>(null);
  const [selectedPayslip, setSelectedPayslip] = useState<PayslipDetailType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  useEffect(() => {
    loadPayslips();
  }, [selectedYear]);

  const loadPayslips = async () => {
    setIsLoading(true);
    try {
      const [payslipsData, summaryData] = await Promise.all([
        payslipService.getPayslips(selectedYear),
        payslipService.getYearSummary(selectedYear),
      ]);

      setPayslips(payslipsData.payslips);
      setAvailableYears(payslipsData.available_years);
      setYearSummary(summaryData);

      // Update selected year if not in available years
      if (payslipsData.available_years.length > 0 && !payslipsData.available_years.includes(selectedYear)) {
        setSelectedYear(payslipsData.available_years[0]);
      }
    } catch (error) {
      console.error('Failed to load payslips:', error);
      toast.error('Failed to load payslips');
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewPayslip = async (id: number) => {
    setIsLoadingDetail(true);
    try {
      const detail = await payslipService.getPayslip(id);
      setSelectedPayslip(detail);
    } catch (error) {
      console.error('Failed to load payslip details:', error);
      toast.error('Failed to load payslip details');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleDownload = async (id: number) => {
    setDownloadingId(id);
    try {
      await payslipService.downloadPayslip(id);
      toast.success('Payslip downloaded successfully');
    } catch (error) {
      console.error('Failed to download payslip:', error);
      toast.error('Failed to download payslip');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleBack = () => {
    setSelectedPayslip(null);
  };

  const formatCurrency = (amount: number, currency: 'USD' | 'ZiG') => {
    if (currency === 'USD') {
      return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `ZiG ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // Show detail view if a payslip is selected
  if (selectedPayslip) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Payslip Details"
          description={`Viewing payslip for ${selectedPayslip.period_display}`}
        />
        <PayslipDetail
          payslip={selectedPayslip}
          onBack={handleBack}
          onDownload={() => handleDownload(selectedPayslip.id)}
          isDownloading={downloadingId === selectedPayslip.id}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payslips"
        description="View and download your payslips"
      />

      {/* Year Summary Cards */}
      {yearSummary && yearSummary.payslip_count > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-green-100 flex items-center justify-center">
                  <DollarSign className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Gross ({selectedYear})</p>
                  <p className="text-lg font-semibold text-green-600">
                    {formatCurrency(yearSummary.total_gross_usd, 'USD')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-red-100 flex items-center justify-center">
                  <TrendingDown className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Deductions ({selectedYear})</p>
                  <p className="text-lg font-semibold text-red-600">
                    {formatCurrency(yearSummary.total_deductions_usd, 'USD')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Wallet className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Net ({selectedYear})</p>
                  <p className="text-lg font-semibold text-primary">
                    {formatCurrency(yearSummary.total_net_usd, 'USD')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Payslips List */}
      <PayslipsList
        payslips={payslips}
        availableYears={availableYears}
        selectedYear={selectedYear}
        onYearChange={setSelectedYear}
        onView={handleViewPayslip}
        onDownload={handleDownload}
        downloadingId={downloadingId}
        isLoading={isLoading || isLoadingDetail}
      />
    </div>
  );
}

export default PayslipsPage;
