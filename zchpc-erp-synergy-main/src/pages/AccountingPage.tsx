import { PlusCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import AccountDashboard from "@/components/Accounting/AccountDashboard";
import CurrencyManager from "@/components/Accounting/Currencies";
import PartnerManager from "@/components/Accounting/PartnerManager";
import JournalEntries from "@/components/Accounting/JournalEntries";
import ReportsDashboard from "@/components/Accounting/ReportsDashboard";
import GeneralLedger from "@/components/Accounting/GeneralLedger";
import AccountsPayable from "@/components/Accounting/AccountsPayable";
import AccountsReceivable from "@/components/Accounting/AccountsReceivable";
import TaxManager from "@/components/Accounting/TaxManager";
import PayrollNotifications from "@/components/Accounting/PayrollNotifications";

interface AccountProps {
  openTab: string;
}

const AccountingPage = ({ openTab }: AccountProps) => {
  const renderContent = () => {
    switch (openTab) {
      case "/accounting/accounting-general-ledger":
        return <GeneralLedger />;
      case "/accounting/accounting-currencies":
        return <CurrencyManager />;
      case "/accounting/accounting-payable":
        return <AccountsPayable />;
      case "/accounting/accounting-receivable":
        return <AccountsReceivable />;
      case "/accounting/accounting-reports":
        return <ReportsDashboard />;
      case "/accounting/accounting-tax":
        return <TaxManager />;
      // Optional extras:
      case "/accounting/accounting-partners":
        return <PartnerManager />;
      case "/accounting/accounting-entries":
        return <JournalEntries />;
      case "/accounting/accounting-payroll":
        return <PayrollNotifications />;
      default:
        return <AccountDashboard />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Accounting</h1>
          <p className="text-muted-foreground">
            Manage financial transactions and reports
          </p>
        </div>
      </div>

      {renderContent()}
    </div>
  );
};

export default AccountingPage;
