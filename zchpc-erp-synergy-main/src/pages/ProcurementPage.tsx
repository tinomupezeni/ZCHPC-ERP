
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Box, 
  CreditCard, 
  FileText, 
  Package2, 
  PlusCircle, 
  ShoppingCart, 
  Truck
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const ProcurementPage = () => {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Procurement</h1>
          <p className="text-muted-foreground">Manage purchase orders and suppliers</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            New Purchase Order
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-full">
                <FileText className="h-4 w-4 text-blue-700" />
              </div>
              <CardTitle className="text-lg">Purchase Orders</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">24</div>
            <p className="text-sm text-muted-foreground">8 awaiting approval</p>
          </CardContent>
        </Card>
        
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-purple-100 rounded-full">
                <Box className="h-4 w-4 text-purple-700" />
              </div>
              <CardTitle className="text-lg">Suppliers</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">52</div>
            <p className="text-sm text-muted-foreground">5 new this month</p>
          </CardContent>
        </Card>
        
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-amber-100 rounded-full">
                <CreditCard className="h-4 w-4 text-amber-700" />
              </div>
              <CardTitle className="text-lg">Monthly Spend</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$28,520</div>
            <p className="text-sm text-muted-foreground">↓ 3% from last month</p>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="subtle-shadow">
          <CardHeader>
            <CardTitle>Recent Purchase Orders</CardTitle>
            <CardDescription>Last 5 purchase orders</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { id: 'PO-001', supplier: 'Tech Suppliers Inc', amount: '$3,450', status: 'approved' },
                { id: 'PO-002', supplier: 'Office Goods LLC', amount: '$1,280', status: 'pending' },
                { id: 'PO-003', supplier: 'Hardware Solutions', amount: '$5,670', status: 'approved' },
                { id: 'PO-004', supplier: 'Global Materials', amount: '$2,340', status: 'pending' },
                { id: 'PO-005', supplier: 'Network Systems', amount: '$4,100', status: 'denied' }
              ].map((po, i) => (
                <div key={i} className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-full">
                      <ShoppingCart className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="font-medium">{po.id}: {po.supplier}</p>
                      <p className="text-sm text-muted-foreground">{po.amount}</p>
                    </div>
                  </div>
                  <Badge 
                    className={
                      po.status === 'approved' ? 'bg-green-100 text-green-800' : 
                      po.status === 'pending' ? 'bg-amber-100 text-amber-800' : 
                      'bg-red-100 text-red-800'
                    }
                  >
                    {po.status.charAt(0).toUpperCase() + po.status.slice(1)}
                  </Badge>
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="outline" size="sm">
                View All Purchase Orders
              </Button>
            </div>
          </CardContent>
        </Card>
        
        <Card className="subtle-shadow">
          <CardHeader>
            <CardTitle>Upcoming Deliveries</CardTitle>
            <CardDescription>Expected shipments</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { id: 'DEL-001', supplier: 'Tech Suppliers Inc', items: '12 items', date: '2023-11-05' },
                { id: 'DEL-002', supplier: 'Office Goods LLC', items: '5 items', date: '2023-11-08' },
                { id: 'DEL-003', supplier: 'Hardware Solutions', items: '8 items', date: '2023-11-10' },
                { id: 'DEL-004', supplier: 'Global Materials', items: '3 items', date: '2023-11-15' },
                { id: 'DEL-005', supplier: 'Network Systems', items: '7 items', date: '2023-11-18' }
              ].map((delivery, i) => (
                <div key={i} className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-full">
                      <Truck className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="font-medium">{delivery.id}: {delivery.supplier}</p>
                      <p className="text-sm text-muted-foreground">{delivery.items}</p>
                    </div>
                  </div>
                  <div className="text-sm font-medium">
                    {new Date(delivery.date).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="outline" size="sm">
                <Package2 className="mr-2 h-4 w-4" />
                View All Deliveries
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ProcurementPage;
