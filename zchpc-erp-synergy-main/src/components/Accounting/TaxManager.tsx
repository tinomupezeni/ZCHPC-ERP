// src/components/Accounting/TaxManagement.tsx
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DollarSign, CheckCircle2, AlertTriangle, Clock, FileText } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

interface TaxEntry {
  id: number;
  type: string;
  period: string;
  amount: number;
  status: "Pending" | "Paid" | "Overdue";
}

const dummyTaxEntries: TaxEntry[] = [
  { id: 1, type: "VAT", period: "Sep 2025", amount: 2500, status: "Pending" },
  { id: 2, type: "Income Tax", period: "Aug 2025", amount: 4800, status: "Paid" },
  { id: 3, type: "Withholding Tax", period: "Sep 2025", amount: 1200, status: "Overdue" },
];

const TaxManagement = () => {
  const [taxEntries] = useState<TaxEntry[]>(dummyTaxEntries);

  // Analytics summary
  const totalTax = taxEntries.reduce((sum, t) => sum + t.amount, 0);
  const paid = taxEntries.filter((t) => t.status === "Paid").reduce((sum, t) => sum + t.amount, 0);
  const pending = taxEntries.filter((t) => t.status === "Pending").reduce((sum, t) => sum + t.amount, 0);
  const overdue = taxEntries.filter((t) => t.status === "Overdue").reduce((sum, t) => sum + t.amount, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Tax Management</h2>
          <p className="text-muted-foreground">
            Monitor tax obligations, payments, and compliance.
          </p>
        </div>
        <Button>
          <FileText className="mr-2 h-4 w-4" />
          Generate Tax Report
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Tax</p>
              <p className="text-xl font-bold">${totalTax.toFixed(2)}</p>
            </div>
            <DollarSign className="h-6 w-6 text-blue-500" />
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
      </div>

      {/* Tabs + Table */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="paid">Paid</TabsTrigger>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="overdue">Overdue</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          <Card>
            <CardHeader className="font-semibold">All Tax Entries</CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Period</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {taxEntries.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell>{t.type}</TableCell>
                      <TableCell>{t.period}</TableCell>
                      <TableCell>${t.amount.toFixed(2)}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            t.status === "Paid"
                              ? "default"
                              : t.status === "Overdue"
                              ? "destructive"
                              : "secondary"
                          }
                        >
                          {t.status}
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

export default TaxManagement;
