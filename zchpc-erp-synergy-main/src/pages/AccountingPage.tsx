import { PlusCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import AccountDashboard from "@/components/Accounting/AccountDashboard";
import CurrencyManager from "@/components/Accounting/Currencies";

// HRPage.tsx
interface AccountProps {
  openTab: string;
}

const AccountingPage = ({ openTab }: AccountProps) => {
  const renderContent = () => {
    switch (openTab) {
      case "accounting-currencies":
        return <CurrencyManager />;
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
        <div className="flex items-center space-x-2">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            New Transaction
          </Button>
        </div>
      </div>

      {renderContent()}
    </div>
  );
};

export default AccountingPage;
