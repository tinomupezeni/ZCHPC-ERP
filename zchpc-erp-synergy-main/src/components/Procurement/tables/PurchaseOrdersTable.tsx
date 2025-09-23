import { useEffect, useState } from "react";
import { fetchPurchaseOrders } from "../api/procurementApi";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, CheckCircle, XCircle } from "lucide-react";

interface PurchaseOrder {
  id: string;
  supplier: string;
  amount: string;
  status: "approved" | "pending" | "denied";
}

interface Props {
  onSelect?: (id: string) => void;
}

const PurchaseOrdersTable = ({ onSelect }: Props) => {
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);

  useEffect(() => {
    fetchPurchaseOrders().then(res => setOrders(res.data));
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return <Badge className="bg-green-100 text-green-800 flex items-center space-x-1"><CheckCircle className="w-4 h-4" /> <span>Approved</span></Badge>;
      case "pending":
        return <Badge className="bg-amber-100 text-amber-800 flex items-center space-x-1"><span>Pending</span></Badge>;
      case "denied":
        return <Badge className="bg-red-100 text-red-800 flex items-center space-x-1"><XCircle className="w-4 h-4" /> <span>Denied</span></Badge>;
      default:
        return <Badge>Unknown</Badge>;
    }
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-800">Purchase Orders</h2>
        <span className="text-sm text-gray-500">{orders.length} orders</span>
      </div>
      <div className="overflow-x-auto">
        {orders.length === 0 ? (
          <div className="p-4 text-center text-gray-500">No data found</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">ID</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Supplier</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Amount</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {orders.map((po, idx) => (
                <tr key={po.id} className={`${idx % 2 === 0 ? "bg-gray-50" : ""} hover:bg-gray-100 transition`}>
                  <td className="px-4 py-3 font-medium text-gray-700">{po.id}</td>
                  <td className="px-4 py-3 text-gray-700">{po.supplier}</td>
                  <td className="px-4 py-3 text-gray-700">{po.amount}</td>
                  <td className="px-4 py-3">{getStatusBadge(po.status)}</td>
                  <td className="px-4 py-3 flex space-x-2">
                    <Button size="sm" variant="outline" onClick={() => onSelect?.(po.id)}>View</Button>
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

export default PurchaseOrdersTable;
