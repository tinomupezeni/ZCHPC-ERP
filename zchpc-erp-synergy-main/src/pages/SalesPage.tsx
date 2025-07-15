
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  PlusCircle, 
  Download, 
  Filter, 
  ArrowUpDown,
  FileText,
  Users,
  BarChart
} from 'lucide-react';

// Dummy data
const orders = [
  { 
    id: 'ORD-001', 
    customer: 'Acme Inc.', 
    date: '2023-10-15', 
    amount: '$3,500.00',
    status: 'completed'
  },
  { 
    id: 'ORD-002', 
    customer: 'Globex Corp', 
    date: '2023-10-18', 
    amount: '$2,780.50',
    status: 'processing'
  },
  { 
    id: 'ORD-003', 
    customer: 'Initech LLC', 
    date: '2023-10-20', 
    amount: '$1,299.99',
    status: 'pending'
  },
  { 
    id: 'ORD-004', 
    customer: 'Hooli Technologies', 
    date: '2023-10-22', 
    amount: '$7,600.00',
    status: 'completed'
  },
  { 
    id: 'ORD-005', 
    customer: 'Stark Industries', 
    date: '2023-10-23', 
    amount: '$15,200.00',
    status: 'processing'
  },
  { 
    id: 'ORD-006', 
    customer: 'Wayne Enterprises', 
    date: '2023-10-25', 
    amount: '$8,750.75',
    status: 'pending'
  },
  { 
    id: 'ORD-007', 
    customer: 'Cyberdyne Systems', 
    date: '2023-10-28', 
    amount: '$950.25',
    status: 'completed'
  },
  { 
    id: 'ORD-008', 
    customer: 'Umbrella Corporation', 
    date: '2023-10-30', 
    amount: '$4,500.00',
    status: 'cancelled'
  },
];

const customers = [
  { id: 'CUST-001', name: 'Acme Inc.', contact: 'John Smith', email: 'john@acme.com', orders: 12 },
  { id: 'CUST-002', name: 'Globex Corp', contact: 'Jane Doe', email: 'jane@globex.com', orders: 8 },
  { id: 'CUST-003', name: 'Initech LLC', contact: 'Michael Johnson', email: 'michael@initech.com', orders: 5 },
  { id: 'CUST-004', name: 'Hooli Technologies', contact: 'Robert Williams', email: 'robert@hooli.com', orders: 15 },
  { id: 'CUST-005', name: 'Stark Industries', contact: 'Sarah Parker', email: 'sarah@stark.com', orders: 20 },
];

const products = [
  { id: 'PRD-001', name: 'Enterprise Server', category: 'Hardware', price: '$2,500.00', stock: 25 },
  { id: 'PRD-002', name: 'Cloud Storage (1TB)', category: 'Services', price: '$99.99/mo', stock: 'Unlimited' },
  { id: 'PRD-003', name: 'Security Suite Pro', category: 'Software', price: '$750.00', stock: 150 },
  { id: 'PRD-004', name: 'Network Switch', category: 'Hardware', price: '$350.00', stock: 42 },
  { id: 'PRD-005', name: 'Technical Support', category: 'Services', price: '$150.00/hr', stock: 'On Demand' },
];

const SalesPage = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-200">Completed</Badge>;
      case 'processing':
        return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">Processing</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200">Pending</Badge>;
      case 'cancelled':
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-200">Cancelled</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sales Management</h1>
          <p className="text-muted-foreground">Manage orders, customers and products</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            New Order
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
              <CardTitle className="text-lg">Orders</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">128</div>
            <p className="text-sm text-muted-foreground">25 pending approval</p>
          </CardContent>
        </Card>
        
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-green-100 rounded-full">
                <Users className="h-4 w-4 text-green-700" />
              </div>
              <CardTitle className="text-lg">Customers</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">42</div>
            <p className="text-sm text-muted-foreground">8 new this month</p>
          </CardContent>
        </Card>
        
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-purple-100 rounded-full">
                <BarChart className="h-4 w-4 text-purple-700" />
              </div>
              <CardTitle className="text-lg">Revenue</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$85,240</div>
            <p className="text-sm text-muted-foreground">↑ 12% from last month</p>
          </CardContent>
        </Card>
      </div>
      
      <Tabs defaultValue="orders">
        <div className="flex justify-between items-center mb-4">
          <TabsList>
            <TabsTrigger value="orders">Orders</TabsTrigger>
            <TabsTrigger value="customers">Customers</TabsTrigger>
            <TabsTrigger value="products">Products</TabsTrigger>
          </TabsList>
          
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search..."
                className="pl-8 w-[200px] md:w-[300px]"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon">
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        <Card className="subtle-shadow">
          <TabsContent value="orders" className="m-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Order ID</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell className="font-medium">{order.id}</TableCell>
                    <TableCell>{order.customer}</TableCell>
                    <TableCell>{order.date}</TableCell>
                    <TableCell>{order.amount}</TableCell>
                    <TableCell>{getStatusBadge(order.status)}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>
          
          <TabsContent value="customers" className="m-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Total Orders</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {customers.map((customer) => (
                  <TableRow key={customer.id}>
                    <TableCell className="font-medium">{customer.id}</TableCell>
                    <TableCell>{customer.name}</TableCell>
                    <TableCell>{customer.contact}</TableCell>
                    <TableCell>{customer.email}</TableCell>
                    <TableCell>{customer.orders}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>
          
          <TabsContent value="products" className="m-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Stock</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow key={product.id}>
                    <TableCell className="font-medium">{product.id}</TableCell>
                    <TableCell>{product.name}</TableCell>
                    <TableCell>{product.category}</TableCell>
                    <TableCell>{product.price}</TableCell>
                    <TableCell>{product.stock}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>
        </Card>
      </Tabs>
    </div>
  );
};

export default SalesPage;
