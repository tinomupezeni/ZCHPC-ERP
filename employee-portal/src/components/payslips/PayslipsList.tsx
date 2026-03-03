import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FileText } from 'lucide-react';
import { PayslipCard } from './PayslipCard';
import type { PayslipListItem } from '@/types/payslip.types';

interface PayslipsListProps {
  payslips: PayslipListItem[];
  availableYears: number[];
  selectedYear: number;
  onYearChange: (year: number) => void;
  onView: (id: number) => void;
  onDownload: (id: number) => void;
  downloadingId?: number | null;
  isLoading: boolean;
}

export function PayslipsList({
  payslips,
  availableYears,
  selectedYear,
  onYearChange,
  onView,
  onDownload,
  downloadingId,
  isLoading,
}: PayslipsListProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Payslips</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-muted rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Payslips
          </CardTitle>
          {availableYears.length > 0 && (
            <Select
              value={selectedYear.toString()}
              onValueChange={(value) => onYearChange(parseInt(value))}
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Select year" />
              </SelectTrigger>
              <SelectContent>
                {availableYears.map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {payslips.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No payslips found for {selectedYear}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {payslips.map((payslip) => (
              <PayslipCard
                key={payslip.id}
                payslip={payslip}
                onView={onView}
                onDownload={onDownload}
                isDownloading={downloadingId === payslip.id}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default PayslipsList;
