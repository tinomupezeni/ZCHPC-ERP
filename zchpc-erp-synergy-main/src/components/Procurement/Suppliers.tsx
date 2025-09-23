import { useState } from "react";
import { Badge } from "@/components/ui/badge";

interface Supplier {
  id: string;
  name: string;
  contact: string;
  status: "active" | "inactive";
}

const mockSuppliers: Supplier[] = [
  { id: "S-001", name: "Tech Suppliers Inc", contact: "+1-202-555-0191", status: "active" },
  { id: "S-002", name: "Office Goods LLC", contact: "+1-202-555-0102", status: "active" },
  { id: "S-003", name: "Hardware Solutions", contact: "+1-202-555-0145", status: "inactive" },
  { id: "S-004", name: "Global Materials", contact: "+1-202-555-0123", status: "active" },
];

const Suppliers = () => {
  const [suppliers] = useState(mockSuppliers);

  if (suppliers.length === 0)
    return <div className="p-4 text-center text-gray-500">No suppliers found</div>;

  return (
    <div className="space-y-4">
      {suppliers.map((s) => (
        <div key={s.id} className="flex justify-between items-center p-4 rounded-lg shadow hover:shadow-lg transition">
          <div>
            <p className="font-semibold">{s.name}</p>
            <p className="text-gray-500">{s.contact}</p>
          </div>
          <Badge className={s.status === "active" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
            {s.status.charAt(0).toUpperCase() + s.status.slice(1)}
          </Badge>
        </div>
      ))}
    </div>
  );
};

export default Suppliers;
