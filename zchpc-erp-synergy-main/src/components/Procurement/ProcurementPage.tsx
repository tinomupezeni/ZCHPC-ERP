// pages/ProcurementPage.tsx
import ProcurementDashboard from "./ProcurementDashboard";
import PurchaseOrders from "./PurchaseOrders";
import Suppliers from "./Suppliers";
import PurchaseRequests from "./PurchaseRequests";
import BudgetCenters from "./BudgetCenters";
import Reports from "./Reports";
import Deliveries from "./Deliveries";

interface ProcurementProps {
  openTab: string;
}

const ProcurementPage = ({ openTab }: ProcurementProps) => {
  const renderContent = () => {
    switch (openTab) {
      case "/procurement/dashboard":
        return <ProcurementDashboard />;
      case "/procurement/purchase-orders":
        return <PurchaseOrders />;
      case "/procurement/suppliers":
        return <Suppliers />;
      case "/procurement/purchase-requests":
        return <PurchaseRequests />;
      case "/procurement/budget-centers":
        return <BudgetCenters />;
      case "/procurement/reports":
        return <Reports />;
      case "/procurement/deliveries":
        return <Deliveries />;
      default:
        return <ProcurementDashboard />;
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Procurement</h1>
          <p className="text-muted-foreground">
            Manage purchase orders, vendors, budgets, and deliveries
          </p>
        </div>
      </div>
      {renderContent()}
    </div>
  );
};

export default ProcurementPage;
