import { useState } from "react";
import { createPurchaseOrder } from "../api/procurementApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const CreatePurchaseOrderModal = ({ open, onClose, onCreated }: Props) => {
  const [supplier, setSupplier] = useState("");
  const [amount, setAmount] = useState("");

  const handleSubmit = async () => {
    await createPurchaseOrder({ supplier, amount });
    onCreated();
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg w-96">
        <h2 className="text-lg font-bold mb-4">Create Purchase Order</h2>
        <Input placeholder="Supplier Name" value={supplier} onChange={(e) => setSupplier(e.target.value)} />
        <Input placeholder="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <div className="mt-4 flex justify-end space-x-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Create</Button>
        </div>
      </div>
    </div>
  );
};

export default CreatePurchaseOrderModal;
