import { useEffect, useState } from "react";
import { fetchPurchaseRequests } from "../api/procurementApi";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Request {
  id: string;
  requester: string;
  amount: string;
  status: "approved" | "pending" | "denied";
}

interface Props {
  onSelect?: (id: string) => void;
}

const PurchaseRequestsTable = ({ onSelect }: Props) => {
  const [requests, setRequests] = useState<Request[]>([]);

  useEffect(() => {
    fetchPurchaseRequests().then(res => setRequests(res.data));
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return <Badge className="bg-green-100 text-green-800">Approved</Badge>;
      case "pending":
        return <Badge className="bg-amber-100 text-amber-800">Pending</Badge>;
      case "denied":
        return <Badge className="bg-red-100 text-red-800">Denied</Badge>;
      default:
        return <Badge>Unknown</Badge>;
    }
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-800">Purchase Requests</h2>
        <span className="text-sm text-gray-500">{requests.length} requests</span>
      </div>
      <div className="overflow-x-auto">
        {requests.length === 0 ? (
          <div className="p-4 text-center text-gray-500">No data found</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">ID</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Requester</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Amount</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {requests.map((r, idx) => (
                <tr key={r.id} className={`${idx % 2 === 0 ? "bg-gray-50" : ""} hover:bg-gray-100 transition`}>
                  <td className="px-4 py-3 font-medium text-gray-700">{r.id}</td>
                  <td className="px-4 py-3 text-gray-700">{r.requester}</td>
                  <td className="px-4 py-3 text-gray-700">{r.amount}</td>
                  <td className="px-4 py-3">{getStatusBadge(r.status)}</td>
                  <td className="px-4 py-3 flex space-x-2">
                    <Button size="sm" variant="outline" onClick={() => onSelect?.(r.id)}>View</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default PurchaseRequestsTable;
