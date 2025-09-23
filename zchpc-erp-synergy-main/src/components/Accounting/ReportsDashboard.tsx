// src/components/Accounting/ReportsDashboard.tsx
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar, ResponsiveContainer } from "recharts";
import { BarChart3, FileText, TrendingUp, TrendingDown } from "lucide-react";

const data = [
  { month: "Apr", revenue: 100000, expenses: 70000, profit: 30000 },
  { month: "May", revenue: 120000, expenses: 85000, profit: 35000 },
  { month: "Jun", revenue: 110000, expenses: 80000, profit: 30000 },
  { month: "Jul", revenue: 130000, expenses: 90000, profit: 40000 },
  { month: "Aug", revenue: 125000, expenses: 88000, profit: 37000 },
  { month: "Sep", revenue: 140000, expenses: 95000, profit: 45000 },
];

const ReportsDashboard = () => {
  return (
    <div className="p-6 space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Financial Reports</h2>
        <p className="text-muted-foreground">
          Generate, view, and analyze your financial statements.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="shadow-md hover:shadow-lg transition">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>Revenue</CardTitle>
            <TrendingUp className="h-5 w-5 text-green-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">${data[data.length - 1].revenue.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">
              ↑ {((data[data.length - 1].revenue - data[data.length - 2].revenue) / data[data.length - 2].revenue * 100).toFixed(1)}% vs last month
            </p>
          </CardContent>
        </Card>

        <Card className="shadow-md hover:shadow-lg transition">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>Expenses</CardTitle>
            <TrendingDown className="h-5 w-5 text-red-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">${data[data.length - 1].expenses.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">
              ↓ {((data[data.length - 1].expenses - data[data.length - 2].expenses) / data[data.length - 2].expenses * 100).toFixed(1)}% vs last month
            </p>
          </CardContent>
        </Card>

        <Card className="shadow-md hover:shadow-lg transition">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>Net Profit</CardTitle>
            <BarChart3 className="h-5 w-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">${data[data.length - 1].profit.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">↑ {((data[data.length - 1].profit - data[data.length - 2].profit) / data[data.length - 2].profit * 100).toFixed(1)}% vs last month</p>
          </CardContent>
        </Card>

        <Card className="shadow-md hover:shadow-lg transition">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>Cash Flow</CardTitle>
            <FileText className="h-5 w-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">${(data[data.length - 1].profit * 0.5).toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">Approximate free cash</p>
          </CardContent>
        </Card>
      </div>

      {/* Revenue vs Expenses Line Chart */}
      <Card className="shadow-md">
        <CardHeader>
          <CardTitle>Revenue vs Expenses (Last 6 months)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid stroke="#f5f5f5" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="revenue" stroke="#22c55e" strokeWidth={2} />
              <Line type="monotone" dataKey="expenses" stroke="#ef4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Profit Bar Chart */}
      <Card className="shadow-md">
        <CardHeader>
          <CardTitle>Profit (Last 6 months)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid stroke="#f5f5f5" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="profit" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Reports Table */}
      <Card className="shadow-md">
        <CardHeader>
          <CardTitle>Recent Reports</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="text-left py-2">Report</th>
                <th className="text-left py-2">Period</th>
                <th className="text-left py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="py-2">Balance Sheet</td>
                <td>Q2 2025</td>
                <td className="text-green-600">Generated</td>
              </tr>
              <tr className="border-b">
                <td className="py-2">Income Statement</td>
                <td>Q2 2025</td>
                <td className="text-green-600">Generated</td>
              </tr>
              <tr>
                <td className="py-2">Cash Flow Statement</td>
                <td>Q2 2025</td>
                <td className="text-yellow-600">In Progress</td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
};

export default ReportsDashboard;
