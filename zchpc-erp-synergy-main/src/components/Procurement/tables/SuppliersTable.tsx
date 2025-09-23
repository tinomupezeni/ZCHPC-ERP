import { useEffect, useState } from "react";
import { fetchSuppliers } from "../api/procurementApi";
import { Button } from "@/components/ui/button";

interface Supplier {
  id: string;
  name: string;
  contact: string;
  status: "active" | "inactive";
}

interface Props {
  onSelect?: (id: string) => void;
}

const SuppliersTable = ({ onSelect }: Props) => {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);

  useEffect(() => {
    fetchSuppliers().then(res => setSuppliers(res.data));
  }, []);

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-800">Suppliers</h2>
        <span className="text-sm text-gray-500">{suppliers.length} suppliers</span>
      </div>
      <div className="overflow-x-auto">
        {suppliers.length === 0 ? (
          <div className="p-4 text-center text-gray-500">No data found</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">ID</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Contact</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {suppliers.map((s, idx) => (
                <tr key={s.id} className={`${idx % 2 === 0 ? "bg-gray-50" : ""} hover:bg-gray-100 transition`}>
                  <td className="px-4 py-3 font-medium text-gray-700">{s.id}</td>
                  <td className="px-4 py-3 text-gray-700">{s.name}</td>
                  <td className="px-4 py-3 text-gray-700">{s.contact}</td>
                  <td className="px-4 py-3">{s.status}</td>
                  <td className="px-4 py-3 flex space-x-2">
                    <Button size="sm" variant="outline" onClick={() => onSelect?.(s.id)}>View</Button>
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

export default SuppliersTable;
