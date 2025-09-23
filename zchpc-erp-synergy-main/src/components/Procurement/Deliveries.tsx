import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Truck } from "lucide-react";

interface Delivery {
  id: string;
  supplier: string;
  items: number;
  date: string;
}

const mockDeliveries: Delivery[] = [
  { id: "DEL-001", supplier: "Tech Suppliers Inc", items: 12, date: "2025-09-05" },
  { id: "DEL-002", supplier: "Office Goods LLC", items: 5, date: "2025-09-08" },
  { id: "DEL-003", supplier: "Hardware Solutions", items: 8, date: "2025-09-10" },
];

const Deliveries = () => {
  const [deliveries] = useState(mockDeliveries);

  if (deliveries.length === 0)
    return <div className="p-4 text-center text-gray-500">No deliveries scheduled</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {deliveries.map((d) => (
        <Card key={d.id} className="hover:shadow-lg transition">
          <CardHeader className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Truck className="h-5 w-5 text-blue-600" />
              <CardTitle>{d.id}</CardTitle>
            </div>
            <CardDescription className="text-gray-500">{d.supplier}</CardDescription>
          </CardHeader>
          <CardContent>
            <p>{d.items} items</p>
            <p>Expected Delivery: {new Date(d.date).toLocaleDateString()}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default Deliveries;
