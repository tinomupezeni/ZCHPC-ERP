import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import {
  DollarSign,
  CreditCard,
  BarChart4,
  RefreshCw,
  FileText,
} from "lucide-react";
import { Button } from '@/components/ui/button';

export default function AccountDashboard() {
  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-full">
                <DollarSign className="h-4 w-4 text-blue-700" />
              </div>
              <CardTitle className="text-lg">Today's Zig Rate</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$27,840</div>
            <p className="text-sm text-muted-foreground">
              ↑ 0.12% from last month
            </p>
          </CardContent>
        </Card>
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-full">
                <DollarSign className="h-4 w-4 text-blue-700" />
              </div>
              <CardTitle className="text-lg">Revenue</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$125,840</div>
            <p className="text-sm text-muted-foreground">
              ↑ 12% from last month
            </p>
          </CardContent>
        </Card>

        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-red-100 rounded-full">
                <CreditCard className="h-4 w-4 text-red-700" />
              </div>
              <CardTitle className="text-lg">Expenses</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$48,350</div>
            <p className="text-sm text-muted-foreground">
              ↓ 5% from last month
            </p>
          </CardContent>
        </Card>

        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-green-100 rounded-full">
                <BarChart4 className="h-4 w-4 text-green-700" />
              </div>
              <CardTitle className="text-lg">Profit</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$77,490</div>
            <p className="text-sm text-muted-foreground">
              ↑ 18% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 py-2">
        <Card className="subtle-shadow">
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
            <CardDescription>Last 5 financial transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex justify-between items-center">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`p-2 rounded-full ${
                        i % 2 === 0 ? "bg-green-100" : "bg-red-100"
                      }`}
                    >
                      {i % 2 === 0 ? (
                        <DollarSign className="h-4 w-4 text-green-700" />
                      ) : (
                        <CreditCard className="h-4 w-4 text-red-700" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">
                        {i % 2 === 0 ? "Payment Received" : "Expense Payment"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {new Date().toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <p
                    className={`font-semibold ${
                      i % 2 === 0 ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {i % 2 === 0 ? "+" : "-"}$
                    {(Math.random() * 1000).toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="outline" size="sm">
                <RefreshCw className="mr-2 h-3 w-3" />
                View All Transactions
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="subtle-shadow">
          <CardHeader>
            <CardTitle>Financial Reports</CardTitle>
            <CardDescription>
              Access financial statements and reports
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                {
                  name: "Income Statement",
                  icon: <BarChart4 className="h-4 w-4" />,
                },
                {
                  name: "Balance Sheet",
                  icon: <FileText className="h-4 w-4" />,
                },
                { name: "Cash Flow", icon: <DollarSign className="h-4 w-4" /> },
                { name: "Tax Summary", icon: <FileText className="h-4 w-4" /> },
                {
                  name: "Budget Report",
                  icon: <CreditCard className="h-4 w-4" />,
                },
              ].map((report, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 rounded-md hover:bg-muted hover-scale"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-full">
                      {report.icon}
                    </div>
                    <span>{report.name}</span>
                  </div>
                  <Button variant="ghost" size="sm">
                    View
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
