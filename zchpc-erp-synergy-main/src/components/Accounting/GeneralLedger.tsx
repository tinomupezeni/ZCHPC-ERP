import React from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Download, Filter, PlusCircle } from "lucide-react";

const GeneralLedger = () => {
  // Mock data
  const ledgerEntries = [
    {
      id: 1,
      date: "2025-09-01",
      description: "Invoice Payment",
      debit: 1200,
      credit: 0,
      balance: 1200,
    },
    {
      id: 2,
      date: "2025-09-05",
      description: "Office Rent",
      debit: 0,
      credit: 500,
      balance: 700,
    },
    {
      id: 3,
      date: "2025-09-12",
      description: "Sales Revenue",
      debit: 1500,
      credit: 0,
      balance: 2200,
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold">General Ledger</h2>
          <p className="text-muted-foreground">
            View and manage all journal entries with running balances
          </p>
        </div>
        <div className="flex items-center space-x-2 mt-4 sm:mt-0">
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" /> Filter
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" /> Export
          </Button>
          <Button>
            <PlusCircle className="h-4 w-4 mr-2" /> New Entry
          </Button>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Debit</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-600">$2,700</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Total Credit</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-600">$500</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">$2,200</p>
          </CardContent>
        </Card>
      </div>

      {/* Ledger table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between w-full">
            <CardTitle>Ledger Entries</CardTitle>
            <Input
              type="text"
              placeholder="Search transactions..."
              className="w-full sm:w-64"
            />
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="text-left border-b">
                  <th className="p-2">Date</th>
                  <th className="p-2">Description</th>
                  <th className="p-2 text-right">Debit</th>
                  <th className="p-2 text-right">Credit</th>
                  <th className="p-2 text-right">Balance</th>
                </tr>
              </thead>
              <tbody>
                {ledgerEntries.map((entry) => (
                  <tr
                    key={entry.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="p-2">{entry.date}</td>
                    <td className="p-2">{entry.description}</td>
                    <td className="p-2 text-right text-blue-600">
                      {entry.debit > 0 ? `$${entry.debit}` : "-"}
                    </td>
                    <td className="p-2 text-right text-red-600">
                      {entry.credit > 0 ? `$${entry.credit}` : "-"}
                    </td>
                    <td className="p-2 text-right font-medium">
                      ${entry.balance}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GeneralLedger;
