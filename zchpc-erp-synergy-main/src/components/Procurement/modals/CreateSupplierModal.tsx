import { useState } from "react";
import { createSupplier } from "../api/procurementApi";
import { Button } from "../../ui/button";
import {  Input } from "../../ui/input";
import { Checkbox } from "../../ui/checkbox";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const CreateSupplierModal = ({ open, onClose, onCreated }: Props) => {
  const [name, setName] = useState("");
  const [contact, setContact] = useState("");
  const [active, setActive] = useState(true);

  const handleSubmit = async () => {
    await createSupplier({ name, contact, active });
    onCreated();
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg w-96">
        <h2 className="text-lg font-bold mb-4">Add Supplier</h2>
        <Input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <Input placeholder="Contact" value={contact} onChange={(e) => setContact(e.target.value)} />
        <div className="mt-2">
          <Checkbox checked={active} onChange={(e) => setActive(e.target.checked)}>Active</Checkbox>
        </div>
        <div className="mt-4 flex justify-end space-x-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Add</Button>
        </div>
      </div>
    </div>
  );
};

export default CreateSupplierModal;
