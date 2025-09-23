import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Box, CreditCard, ShoppingCart, Truck, Package2, PlusCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

const ProcurementDashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    purchaseOrders: 0,
    suppliers: 0,
    monthlySpend: 0,
    recentOrders: [],
    upcomingDeliveries: [],
  });

  useEffect(() => {
    // fetch("/api/procurement/dashboard")
    //   .then(res => res.json())
    //   .then(setDashboardData);
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-full"><FileText className="h-4 w-4 text-blue-700" /></div>
              <CardTitle className="text-lg">Purchase Orders</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboardData.purchaseOrders}</div>
            <p className="text-sm text-muted-foreground">8 awaiting approval</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-purple-100 rounded-full"><Box className="h-4 w-4 text-purple-700" /></div>
              <CardTitle className="text-lg">Suppliers</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboardData.suppliers}</div>
            <p className="text-sm text-muted-foreground">5 new this month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-amber-100 rounded-full"><CreditCard className="h-4 w-4 text-amber-700" /></div>
              <CardTitle className="text-lg">Monthly Spend</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">${dashboardData.monthlySpend}</div>
            <p className="text-sm text-muted-foreground">↓ 3% from last month</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Orders & Deliveries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders Card */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Purchase Orders</CardTitle>
            <CardDescription>Last 5 purchase orders</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.recentOrders.map((po, i) => (
                <div key={i} className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-full"><ShoppingCart className="h-4 w-4" /></div>
                    <div>
                      <p className="font-medium">{po.id}: {po.supplier}</p>
                      <p className="text-sm text-muted-foreground">{po.amount}</p>
                    </div>
                  </div>
                  <Badge className={
                    po.status === 'approved' ? 'bg-green-100 text-green-800' :
                    po.status === 'pending' ? 'bg-amber-100 text-amber-800' :
                    'bg-red-100 text-red-800'
                  }>{po.status.charAt(0).toUpperCase() + po.status.slice(1)}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Deliveries Card */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Deliveries</CardTitle>
            <CardDescription>Expected shipments</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.upcomingDeliveries.map((delivery, i) => (
                <div key={i} className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-full"><Truck className="h-4 w-4" /></div>
                    <div>
                      <p className="font-medium">{delivery.id}: {delivery.supplier}</p>
                      <p className="text-sm text-muted-foreground">{delivery.items}</p>
                    </div>
                  </div>
                  <div className="text-sm font-medium">{new Date(delivery.date).toLocaleDateString()}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ProcurementDashboard;
