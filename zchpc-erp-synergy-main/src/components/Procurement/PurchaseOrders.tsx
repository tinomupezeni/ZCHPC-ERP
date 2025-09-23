import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface PurchaseOrder {
  id: string;
  supplier: string;
  amount: string;
  status: "approved" | "pending" | "denied";
}

const mockOrders: PurchaseOrder[] = [
  { id: "PO-001", supplier: "Tech Suppliers Inc", amount: "$3,450", status: "approved" },
  { id: "PO-002", supplier: "Office Goods LLC", amount: "$1,280", status: "pending" },
  { id: "PO-003", supplier: "Hardware Solutions", amount: "$5,670", status: "approved" },
  { id: "PO-004", supplier: "Global Materials", amount: "$2,340", status: "pending" },
  { id: "PO-005", supplier: "Network Systems", amount: "$4,100", status: "denied" },
];

interface Props {
  onSelect?: (id: string) => void;
}

const PurchaseOrders = ({ onSelect }: Props) => {
  const [orders] = useState(mockOrders);

  if (orders.length === 0)
    return <div className="p-4 text-center text-gray-500">No purchase orders found</div>;

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left">ID</th>
            <th className="px-4 py-2 text-left">Supplier</th>
            <th className="px-4 py-2 text-left">Amount</th>
            <th className="px-4 py-2 text-left">Status</th>
            <th className="px-4 py-2 text-left">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {orders.map((po) => (
            <tr key={po.id} className="hover:bg-gray-50 transition">
              <td className="px-4 py-2">{po.id}</td>
              <td className="px-4 py-2">{po.supplier}</td>
              <td className="px-4 py-2">{po.amount}</td>
              <td className="px-4 py-2">
                <Badge
                  className={
                    po.status === "approved"
                      ? "bg-green-100 text-green-800"
                      : po.status === "pending"
                      ? "bg-amber-100 text-amber-800"
                      : "bg-red-100 text-red-800"
                  }
                >
                  {po.status.charAt(0).toUpperCase() + po.status.slice(1)}
                </Badge>
              </td>
              <td className="px-4 py-2">
                <Button size="sm" onClick={() => onSelect?.(po.id)}>
                  View
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PurchaseOrders;
