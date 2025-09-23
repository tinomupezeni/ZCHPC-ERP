import { useState } from "react";
import { Badge } from "@/components/ui/badge";

interface Request {
  id: string;
  item: string;
  quantity: number;
  status: "approved" | "pending" | "denied";
}

const mockRequests: Request[] = [
  { id: "PR-001", item: "Laptop", quantity: 5, status: "approved" },
  { id: "PR-002", item: "Office Chair", quantity: 20, status: "pending" },
  { id: "PR-003", item: "Mouse", quantity: 50, status: "denied" },
];

const PurchaseRequests = () => {
  const [requests] = useState(mockRequests);

  if (requests.length === 0)
    return <div className="p-4 text-center text-gray-500">No purchase requests found</div>;

  return (
    <div className="space-y-4">
      {requests.map((r) => (
        <div key={r.id} className="flex justify-between items-center p-4 rounded-lg shadow hover:shadow-lg transition">
          <div>
            <p className="font-semibold">{r.item}</p>
            <p className="text-gray-500">Quantity: {r.quantity}</p>
          </div>
          <Badge
            className={
              r.status === "approved"
                ? "bg-green-100 text-green-800"
                : r.status === "pending"
                ? "bg-amber-100 text-amber-800"
                : "bg-red-100 text-red-800"
            }
          >
            {r.status.charAt(0).toUpperCase() + r.status.slice(1)}
          </Badge>
        </div>
      ))}
    </div>
  );
};

export default PurchaseRequests;
