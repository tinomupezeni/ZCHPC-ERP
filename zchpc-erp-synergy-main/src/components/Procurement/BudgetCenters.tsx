import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Budget {
  id: string;
  name: string;
  allocated_amount: number;
  used_amount: number;
  remaining_amount: number;
}

const mockBudgets: Budget[] = [
  { id: "B-001", name: "IT Department", allocated_amount: 50000, used_amount: 32000, remaining_amount: 18000 },
  { id: "B-002", name: "HR Department", allocated_amount: 30000, used_amount: 15000, remaining_amount: 15000 },
  { id: "B-003", name: "Operations", allocated_amount: 40000, used_amount: 25000, remaining_amount: 15000 },
];

const BudgetCenters = () => {
  const [budgets] = useState(mockBudgets);

  if (budgets.length === 0)
    return <div className="p-4 text-center text-gray-500">No budget data found</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {budgets.map((b) => (
        <Card key={b.id} className="hover:shadow-lg transition">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">{b.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <p>Allocated: ${b.allocated_amount.toLocaleString()}</p>
            <p>Used: ${b.used_amount.toLocaleString()}</p>
            <p>Remaining: ${b.remaining_amount.toLocaleString()}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default BudgetCenters;
