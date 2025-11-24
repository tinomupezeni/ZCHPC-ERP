// src/components/AddressModal.tsx
import React, { useState, useEffect } from "react";
import { X, Loader } from "lucide-react";
import { Address } from "../types"; // Adjust path as needed

interface AddressModalProps {
  show: boolean;
  onClose: () => void;
  onSave: (address: Omit<Address, 'id'> | Address) => Promise<void>;
  addressToEdit: Address | null;
}

const emptyAddress: Omit<Address, 'id'> = {
  label: "",
  street: "",
  city: "",
  state: "",
  postalCode: "",
  country: "",
};

export default function AddressModal({ show, onClose, onSave, addressToEdit }: AddressModalProps) {
  const [formData, setFormData] = useState<Omit<Address, 'id'> | Address>(emptyAddress);
  const [loading, setLoading] = useState(false);

  // When the modal opens for editing, populate the form
  useEffect(() => {
    if (addressToEdit) {
      setFormData(addressToEdit);
    } else {
      setFormData(emptyAddress);
    }
  }, [addressToEdit, show]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await onSave(formData);
    setLoading(false);
  };

  if (!show) {
    return null;
  }

  const isEditing = !!addressToEdit;

  return (
    // Basic modal structure (backdrop, card)
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            {isEditing ? "Edit Address" : "Add New Address"}
          </h3>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-200">
            <X className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Label</label>
              <input
                type="text"
                name="label"
                value={formData.label}
                onChange={handleChange}
                placeholder="e.g., Headquarters"
                className="w-full border rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Street Address</label>
              <input
                type="text"
                name="street"
                value={formData.street}
                onChange={handleChange}
                placeholder="123 Main St"
                className="w-full border rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">City</label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  className="w-full border rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">State/Province</label>
                <input
                  type="text"
                  name="state"
                  value={formData.state}
                  onChange={handleChange}
                  className="w-full border rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Postal Code</label>
                <input
                  type="text"
                  name="postalCode"
                  value={formData.postalCode}
                  onChange={handleChange}
                  className="w-full border rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Country</label>
                <input
                  type="text"
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  className="w-full border rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
          </div>

          <div className="mt-6 flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded border text-sm hover:bg-gray-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors flex items-center"
            >
              {loading && <Loader className="h-4 w-4 animate-spin mr-2" />}
              {loading ? "Saving..." : "Save Address"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}