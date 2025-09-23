// src/components/Accounting/AccountsReceivable.tsx
import { useState } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PlusCircle, DollarSign, Clock, AlertTriangle, CheckCircle2, TrendingUp, TrendingDown } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

interface Receivable {
  id: number;
  customer: string;
  invoiceNumber: string;
  amount: number;
  dueDate: string;
  status: "Pending" | "Paid" | "Overdue";
}

const dummyReceivables: Receivable[] = [
  { id: 1, customer: "Client A", invoiceNumber: "INV-1001", amount: 3500, dueDate: "2025-09-28", status: "Pending" },
  { id: 2, customer: "Client B", invoiceNumber: "INV-1002", amount: 1200, dueDate: "2025-09-05", status: "Overdue" },
  { id: 3, customer: "Client C", invoiceNumber: "INV-1003", amount: 5400, dueDate: "2025-09-10", status: "Paid" },
];

const AccountsReceivable = () => {
  const [receivables] = useState<Receivable[]>(dummyReceivables);

  // Analytics summary
  const total = receivables.reduce((sum, r) => sum + r.amount, 0);
  const pending = receivables.filter((r) => r.status === "Pending").reduce((s, r) => s + r.amount, 0);
  const overdue = receivables.filter((r) => r.status === "Overdue").reduce((s, r) => s + r.amount, 0);
  const collected = receivables.filter((r) => r.status === "Paid").reduce((s, r) => s + r.amount, 0);

  // Placeholder Payables total (replace with real API call later)
  const totalPayables = 4200;
  const netCashFlow = collected - totalPayables;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Accounts Receivable</h2>
          <p className="text-muted-foreground">
            Track customer invoices, collections, and outstanding balances.
          </p>
        </div>
        <Button>
          <PlusCircle className="mr-2 h-4 w-4" />
          New Invoice
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Receivables</p>
              <p className="text-xl font-bold">${total.toFixed(2)}</p>
            </div>
            <DollarSign className="h-6 w-6 text-blue-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-muted-foreground">Pending</p>
              <p className="text-xl font-bold">${pending.toFixed(2)}</p>
            </div>
            <Clock className="h-6 w-6 text-yellow-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-muted-foreground">Overdue</p>
              <p className="text-xl font-bold">${overdue.toFixed(2)}</p>
            </div>
            <AlertTriangle className="h-6 w-6 text-red-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-muted-foreground">Collected</p>
              <p className="text-xl font-bold">${collected.toFixed(2)}</p>
            </div>
            <CheckCircle2 className="h-6 w-6 text-green-500" />
          </CardContent>
        </Card>
        {/* Net Cash Flow Impact */}
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-muted-foreground">Net Cash Flow</p>
              <p
                className={`text-xl font-bold ${
                  netCashFlow >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                ${netCashFlow.toFixed(2)}
              </p>
            </div>
            {netCashFlow >= 0 ? (
              <TrendingUp className="h-6 w-6 text-green-500" />
            ) : (
              <TrendingDown className="h-6 w-6 text-red-500" />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs + Table */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="paid">Paid</TabsTrigger>
          <TabsTrigger value="overdue">Overdue</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          <Card>
            <CardHeader className="font-semibold">All Receivables</CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {receivables.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>{r.customer}</TableCell>
                      <TableCell>{r.invoiceNumber}</TableCell>
                      <TableCell>${r.amount.toFixed(2)}</TableCell>
                      <TableCell>{r.dueDate}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            r.status === "Paid"
                              ? "default"
                              : r.status === "Overdue"
                              ? "destructive"
                              : "secondary"
                          }
                        >
                          {r.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AccountsReceivable;
