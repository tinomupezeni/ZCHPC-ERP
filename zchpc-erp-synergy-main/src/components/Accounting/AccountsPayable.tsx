// src/components/Accounting/AccountsPayable.tsx
import { useState } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PlusCircle, DollarSign, Clock, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

interface Payable {
  id: number;
  vendor: string;
  invoiceNumber: string;
  amount: number;
  dueDate: string;
  status: "Pending" | "Paid" | "Overdue";
}

const dummyPayables: Payable[] = [
  { id: 1, vendor: "Supplier A", invoiceNumber: "INV-001", amount: 1200, dueDate: "2025-09-30", status: "Pending" },
  { id: 2, vendor: "Supplier B", invoiceNumber: "INV-002", amount: 750, dueDate: "2025-09-10", status: "Overdue" },
  { id: 3, vendor: "Supplier C", invoiceNumber: "INV-003", amount: 2200, dueDate: "2025-09-25", status: "Paid" },
];

const AccountsPayable = () => {
  const [payables] = useState<Payable[]>(dummyPayables);

  // Analytics summary
  const total = payables.reduce((sum, p) => sum + p.amount, 0);
  const pending = payables.filter((p) => p.status === "Pending").reduce((s, p) => s + p.amount, 0);
  const overdue = payables.filter((p) => p.status === "Overdue").reduce((s, p) => s + p.amount, 0);
  const paid = payables.filter((p) => p.status === "Paid").reduce((s, p) => s + p.amount, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Accounts Payable</h2>
          <p className="text-muted-foreground">
            Manage vendor invoices, payments, and outstanding balances.
          </p>
        </div>
        <Button>
          <PlusCircle className="mr-2 h-4 w-4" />
          Add Invoice
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Payables</p>
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
              <p className="text-sm text-muted-foreground">Paid</p>
              <p className="text-xl font-bold">${paid.toFixed(2)}</p>
            </div>
            <CheckCircle2 className="h-6 w-6 text-green-500" />
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
            <CardHeader className="font-semibold">All Payables</CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payables.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>{p.vendor}</TableCell>
                      <TableCell>{p.invoiceNumber}</TableCell>
                      <TableCell>${p.amount.toFixed(2)}</TableCell>
                      <TableCell>{p.dueDate}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            p.status === "Paid"
                              ? "default"
                              : p.status === "Overdue"
                              ? "destructive"
                              : "secondary"
                          }
                        >
                          {p.status}
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

export default AccountsPayable;
