
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Archive, 
  BarChart, 
  Box, 
  Package, 
  Plus, 
  Search, 
  TrendingDown, 
  TrendingUp, 
  Truck
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useState } from 'react';

// Dummy data
const inventoryItems = [
  { id: 'INV-001', name: 'Enterprise Servers', category: 'Hardware', stock: 24, status: 'in-stock' },
  { id: 'INV-002', name: 'Network Switches', category: 'Hardware', stock: 18, status: 'in-stock' },
  { id: 'INV-003', name: 'Cloud Storage (1TB)', category: 'Services', stock: 'Unlimited', status: 'available' },
  { id: 'INV-004', name: 'Desktop Computers', category: 'Hardware', stock: 5, status: 'low-stock' },
  { id: 'INV-005', name: 'Office Chairs', category: 'Furniture', stock: 15, status: 'in-stock' },
  { id: 'INV-006', name: 'Meeting Tables', category: 'Furniture', stock: 0, status: 'out-of-stock' },
  { id: 'INV-007', name: 'Security Software', category: 'Software', stock: 32, status: 'in-stock' },
  { id: 'INV-008', name: 'Office Supplies Kit', category: 'Supplies', stock: 8, status: 'low-stock' },
  { id: 'INV-009', name: 'Laptops', category: 'Hardware', stock: 12, status: 'in-stock' },
  { id: 'INV-010', name: 'Mobile Phones', category: 'Hardware', stock: 0, status: 'out-of-stock' },
];

const InventoryPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'in-stock':
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-200">In Stock</Badge>;
      case 'low-stock':
        return <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-200">Low Stock</Badge>;
      case 'out-of-stock':
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-200">Out of Stock</Badge>;
      case 'available':
        return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">Available</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };
  
  // Filter inventory items based on search term
  const filteredItems = inventoryItems.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Inventory Management</h1>
          <p className="text-muted-foreground">Track and manage inventory items</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Item
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-full">
                <Package className="h-4 w-4 text-blue-700" />
              </div>
              <CardTitle className="text-lg">Total Items</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">683</div>
            <p className="text-sm text-muted-foreground">Across 12 categories</p>
          </CardContent>
        </Card>
        
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-red-100 rounded-full">
                <TrendingDown className="h-4 w-4 text-red-700" />
              </div>
              <CardTitle className="text-lg">Low Stock</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">24</div>
            <p className="text-sm text-muted-foreground">Items need reordering</p>
          </CardContent>
        </Card>
        
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-green-100 rounded-full">
                <TrendingUp className="h-4 w-4 text-green-700" />
              </div>
              <CardTitle className="text-lg">Stock Value</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$245,890</div>
            <p className="text-sm text-muted-foreground">↑ 12% from last month</p>
          </CardContent>
        </Card>
      </div>
      
      <Card className="subtle-shadow">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0 pb-2">
          <CardTitle>Inventory Items</CardTitle>
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search items..."
                className="pl-8 w-[200px] md:w-[300px]"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full caption-bottom text-sm">
              <thead className="[&_tr]:border-b">
                <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-[100px]">
                    ID
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">
                    Name
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">
                    Category
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">
                    Stock
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">
                    Status
                  </th>
                  <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="[&_tr:last-child]:border-0">
                {filteredItems.map((item) => (
                  <tr 
                    key={item.id} 
                    className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <td className="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-medium">
                      {item.id}
                    </td>
                    <td className="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      {item.name}
                    </td>
                    <td className="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      {item.category}
                    </td>
                    <td className="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      {item.stock}
                    </td>
                    <td className="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      {getStatusBadge(item.status)}
                    </td>
                    <td className="p-4 align-middle [&:has([role=checkbox])]:pr-0 text-right">
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="subtle-shadow">
          <CardHeader>
            <CardTitle>Warehouse Summary</CardTitle>
            <CardDescription>Inventory distribution by location</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { name: 'Main Warehouse', items: 420, capacity: '75%' },
                { name: 'East Storage', items: 183, capacity: '45%' },
                { name: 'West Storage', items: 80, capacity: '20%' }
              ].map((warehouse, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between">
                    <div className="flex items-center space-x-2">
                      <Archive className="h-4 w-4 text-primary" />
                      <span className="font-medium">{warehouse.name}</span>
                    </div>
                    <span className="text-sm">{warehouse.items} items</span>
                  </div>
                  <div className="relative pt-1">
                    <div className="overflow-hidden h-2 text-xs flex rounded bg-primary/20">
                      <div 
                        style={{ width: warehouse.capacity }}
                        className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary"
                      ></div>
                    </div>
                    <span className="text-xs text-muted-foreground mt-1">
                      Capacity: {warehouse.capacity}
                    </span>
                  </div>
                </div>
              ))}
              <div className="flex justify-end mt-2">
                <Button variant="outline" size="sm">
                  View Detailed Report
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="subtle-shadow">
          <CardHeader>
            <CardTitle>Upcoming Inventory Changes</CardTitle>
            <CardDescription>Expected changes to inventory</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-full">
                    <Truck className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium">Inbound Shipment</p>
                    <p className="text-sm text-muted-foreground">
                      20 Enterprise Servers
                    </p>
                  </div>
                </div>
                <div className="text-sm">
                  Nov 5, 2023
                </div>
              </div>
              
              <div className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-full">
                    <Box className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium">Inventory Audit</p>
                    <p className="text-sm text-muted-foreground">
                      Main Warehouse
                    </p>
                  </div>
                </div>
                <div className="text-sm">
                  Nov 8, 2023
                </div>
              </div>
              
              <div className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-full">
                    <Truck className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium">Order Fulfillment</p>
                    <p className="text-sm text-muted-foreground">
                      15 Desktop Computers
                    </p>
                  </div>
                </div>
                <div className="text-sm">
                  Nov 10, 2023
                </div>
              </div>
              
              <div className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-full">
                    <BarChart className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium">Inventory Valuation</p>
                    <p className="text-sm text-muted-foreground">
                      End of Quarter
                    </p>
                  </div>
                </div>
                <div className="text-sm">
                  Dec 31, 2023
                </div>
              </div>
              
              <div className="flex justify-end mt-2">
                <Button variant="outline" size="sm">
                  View Calendar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InventoryPage;
