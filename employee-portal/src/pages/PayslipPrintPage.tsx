import { useEffect, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { Loader2, Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { availabilityFor } from '@/components/layout/navAvailability';
import { NotAvailablePage } from '@/pages/NotAvailablePage';
import { payslipService } from '@/services/payslip.service';
import type { CurrencyAmount, PayslipDetail } from '@/types/payslip.types';

/**
 * PY-3: a printable payslip, replacing the old download (its endpoint never
 * existed). A standalone route like the purchase-requisition print form, so
 * it reuses that form's print styles (pr-print-*). Outside MainLayout, so it
 * applies the evaluation's availability list itself. Tax figures are
 * indicative (A-9) and the page says so.
 */
function money(value: number): string {
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function Row({ label, amount }: { label: string; amount: CurrencyAmount }) {
  return (
    <tr>
      <td>{label}</td>
      <td className="pr-print-num">{money(amount.usd)}</td>
      <td className="pr-print-num">{money(amount.zig)}</td>
    </tr>
  );
}

export function PayslipPrintPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const available = !availabilityFor(location.pathname);
  const [payslip, setPayslip] = useState<PayslipDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!id || !available) return;
    let cancelled = false;
    payslipService
      .getPayslip(Number(id))
      .then((result) => {
        if (!cancelled) setPayslip(result);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id, available]);

  if (!available) return <NotAvailablePage />;

  if (isLoading) {
    return (
      <div className="pr-print-status">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (failed || !payslip) {
    return (
      <div className="pr-print-status">
        <p>Payslip not found.</p>
      </div>
    );
  }

  const { earnings, deductions, summary } = payslip;

  return (
    <div className="pr-print-page">
      <div className="pr-print-actions">
        <Button type="button" onClick={() => window.print()}>
          <Printer className="mr-2 h-4 w-4" />
          Print
        </Button>
      </div>
      <div className="pr-print-paper">
        <div className="pr-print-letterhead">
          <div className="pr-print-header">
            <span />
            <h1>PAYSLIP - {payslip.period_display.toUpperCase()}</h1>
            <span />
          </div>
        </div>

        <div className="pr-print-row">
          <div>
            <span className="pr-print-label">Name:</span>
            <span className="pr-print-fill">{payslip.employee_name}</span>
          </div>
          <div>
            <span className="pr-print-label">EC number:</span>
            <span className="pr-print-fill">{payslip.employee_id}</span>
          </div>
          <div>
            <span className="pr-print-label">Department:</span>
            <span className="pr-print-fill">{payslip.department}</span>
          </div>
          <div>
            <span className="pr-print-label">Position:</span>
            <span className="pr-print-fill">{payslip.position}</span>
          </div>
          <div>
            <span className="pr-print-label">Status:</span>
            <span className="pr-print-fill">{payslip.status}</span>
          </div>
          <div>
            <span className="pr-print-label">Exchange rate (ZiG per USD):</span>
            <span className="pr-print-fill">{payslip.exchange_rate}</span>
          </div>
        </div>

        <h2>Earnings</h2>
        <table className="pr-print-table">
          <thead>
            <tr>
              <th>Item</th>
              <th className="pr-print-num">USD</th>
              <th className="pr-print-num">ZiG</th>
            </tr>
          </thead>
          <tbody>
            <Row label="Basic salary" amount={earnings.base_salary} />
            <Row label="Allowances" amount={earnings.allowances} />
            <Row label="Gross pay" amount={earnings.gross} />
          </tbody>
        </table>

        <h2>Deductions</h2>
        <table className="pr-print-table">
          <thead>
            <tr>
              <th>Item</th>
              <th className="pr-print-num">USD</th>
              <th className="pr-print-num">ZiG</th>
            </tr>
          </thead>
          <tbody>
            <Row label="PAYE" amount={deductions.paye} />
            <Row label="AIDS levy" amount={deductions.aids_levy} />
            <Row label="NSSA (employee)" amount={deductions.nssa_employee} />
            <Row label="Other deductions" amount={deductions.other_deductions} />
            <Row label="Total deductions" amount={deductions.total} />
          </tbody>
        </table>

        <h2>Net pay</h2>
        <table className="pr-print-table">
          <tbody>
            <tr className="pr-print-total-row">
              <td>Net salary</td>
              <td className="pr-print-num">{money(summary.net_salary.usd)}</td>
              <td className="pr-print-num">{money(summary.net_salary.zig)}</td>
            </tr>
          </tbody>
        </table>

        <p className="pr-print-note">
          Indicative figures: tax and deductions follow the rules configured for this
          evaluation and are not an official statement of pay.
        </p>
        {payslip.notes && <p className="pr-print-note">Notes: {payslip.notes}</p>}
      </div>
    </div>
  );
}

export default PayslipPrintPage;
