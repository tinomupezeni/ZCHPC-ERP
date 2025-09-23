// src/components/Accounting/PayrollNotifications.tsx
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bell, UserCheck, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import PayrollDetails from "./PayrollDetails";

interface PayrollNotification {
    id: number;
    batch: string;
    date: string;
    totalAmount: number;
    totalEmployees: number;
    status: "Pending" | "Processed";
}

interface EmployeePayroll {
    id: number;
    name: string;
    bank: string;
    accountNumber: string;
    netPay: number;
    status: "Pending" | "Paid";
}

// Dummy data
const dummyNotifications: PayrollNotification[] = [
    { id: 1, batch: "Sep Payroll", date: "2025-09-20", totalAmount: 45000, totalEmployees: 25, status: "Pending" },
    { id: 2, batch: "Aug Payroll", date: "2025-08-20", totalAmount: 44000, totalEmployees: 24, status: "Processed" },
];

const dummyEmployeeData: EmployeePayroll[] = [
    { id: 1, name: "John Doe", bank: "CBZ", accountNumber: "1234567890", netPay: 1800, status: "Pending" },
    { id: 2, name: "Jane Smith", bank: "FBC", accountNumber: "0987654321", netPay: 1750, status: "Pending" },
    { id: 3, name: "Bob Johnson", bank: "Steward", accountNumber: "1122334455", netPay: 1900, status: "Pending" },
];

const PayrollNotifications = () => {
    const [selectedPayroll, setSelectedPayroll] = useState<PayrollNotification | null>(null);

    // Summary analytics
    const totalPending = dummyNotifications.filter(n => n.status === "Pending").length;
    const totalProcessed = dummyNotifications.filter(n => n.status === "Processed").length;
    const totalAmount = dummyNotifications.reduce((sum, n) => sum + n.totalAmount, 0);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold">Payroll Notifications</h2>
                <p className="text-muted-foreground">
                    Notifications from HR about payroll batches that require processing.
                </p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card>
                    <CardContent className="flex justify-between items-center p-4">
                        <div>
                            <p className="text-sm text-muted-foreground">Pending Payrolls</p>
                            <p className="text-xl font-bold">{totalPending}</p>
                        </div>
                        <Bell className="h-6 w-6 text-yellow-500" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex justify-between items-center p-4">
                        <div>
                            <p className="text-sm text-muted-foreground">Processed Payrolls</p>
                            <p className="text-xl font-bold">{totalProcessed}</p>
                        </div>
                        <Bell className="h-6 w-6 text-green-500" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex justify-between items-center p-4">
                        <div>
                            <p className="text-sm text-muted-foreground">Total Payroll Amount</p>
                            <p className="text-xl font-bold">${totalAmount.toLocaleString()}</p>
                        </div>
                        <DollarSign className="h-6 w-6 text-blue-500" />
                    </CardContent>
                </Card>
            </div>

            {/* Payroll Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {dummyNotifications.map((n) => (
                    <Card
                        key={n.id}
                        className="shadow-md hover:shadow-xl transition-transform transform hover:-translate-y-1"
                    >
                        <CardHeader className="flex justify-between items-center pb-2">
                            <div className="flex items-center space-x-3">
                                <div className="p-2 bg-blue-100 rounded-full">
                                    <Bell className="h-5 w-5 text-blue-600" />
                                </div>
                                <CardTitle className="text-lg">{n.batch}</CardTitle>
                            </div>
                            <Badge variant={n.status === "Pending" ? "warning" : "success"} className="capitalize">
                                {n.status}
                            </Badge>
                        </CardHeader>

                        <CardContent className="space-y-2">
                            <div className="flex justify-between items-center text-sm text-muted-foreground">
                                <div className="flex items-center space-x-1">
                                    <UserCheck className="h-4 w-4 text-gray-500" />
                                    <span>{n.totalEmployees} Employees</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                    <DollarSign className="h-4 w-4 text-gray-500" />
                                    <span>${n.totalAmount.toLocaleString()}</span>
                                </div>
                            </div>

                            <div className="flex justify-between items-center mt-4">
                                <p className="text-xs text-muted-foreground">Payroll Date: {n.date}</p>
                                {n.status === "Pending" && (
                                    <Button
                                        size="sm"
                                        variant="default"
                                        onClick={() => setSelectedPayroll(selectedPayroll?.id === n.id ? null : n)}
                                    >
                                        {selectedPayroll?.id === n.id ? "Hide Details" : "Process Payroll"}
                                    </Button>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Full-width Expandable Employee Table */}
            {selectedPayroll && (
                <div className="mt-6 w-full">
                    <PayrollDetails payrollBatch={selectedPayroll.batch} data={dummyEmployeeData} />
                </div>
            )}
        </div>
    );
};

export default PayrollNotifications;
