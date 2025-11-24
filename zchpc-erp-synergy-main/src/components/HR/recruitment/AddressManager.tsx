// src/components/AddressManager.tsx
import React, { useState, useEffect, useMemo } from "react";
import Addresses from "./Addresses"; // Your table component
import AddressModal from "./AddressModal";       // The new modal
import * as addressService from "../../../server/address.services"; // The API
import { Address } from "../types";
import { toast } from "sonner"; // Or your preferred notification library

const ITEMS_PER_PAGE = 5;

export default function AddressManager() {
  const [allAddresses, setAllAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  
  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [addressToEdit, setAddressToEdit] = useState<Address | null>(null);

  // --- Data Fetching ---
  const fetchAddresses = async () => {
    setLoading(true);
    try {
      const data = await addressService.getAddresses();
      setAllAddresses(data);
    } catch (error) {
      console.error("Failed to fetch addresses:", error);
      toast.error("Failed to load addresses.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAddresses();
  }, []);

  // --- Memoized Filtering & Pagination ---
  const filteredAddresses = useMemo(() => {
    return allAddresses.filter(
      (address) =>
        address.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        address.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
        address.street.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [allAddresses, searchTerm]);

  const currentAddresses = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredAddresses.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredAddresses, currentPage]);

  const totalPages = Math.ceil(filteredAddresses.length / ITEMS_PER_PAGE);

  // --- Event Handlers ---
  const handlePaginate = (pageNumber: number) => {
    setCurrentPage(pageNumber);
  };

  const handleActionSelect = (action: string, address: Address) => {
    if (action === "edit") {
      setAddressToEdit(address);
    }
    if (action === "delete") {
      // You'd probably want a confirmation modal here
      handleDeleteAddress(address.id);
    }
  };

  const handleSaveNewAddress = async (addressData: Omit<Address, 'id'>) => {
    try {
      await addressService.createAddress(addressData);
      toast.success("Address added successfully!");
      setShowAddModal(false);
      await fetchAddresses(); // Refetch data
    } catch (error) {
      console.error("Failed to create address:", error);
      toast.error("Failed to add address.");
    }
  };

  const handleSaveEditedAddress = async (addressData: Address) => {
    try {
      await addressService.updateAddress(addressData);
      toast.success("Address updated successfully!");
      setAddressToEdit(null);
      await fetchAddresses(); // Refetch data
    } catch (error) {
      console.error("Failed to update address:", error);
      toast.error("Failed to update address.");
    }
  };

  const handleDeleteAddress = async (addressId: number | string) => {
    if (!window.confirm("Are you sure you want to delete this address?")) {
        return;
    }
    
    try {
      await addressService.deleteAddress(addressId);
      toast.success("Address deleted successfully!");
      await fetchAddresses(); // Refetch data
    } catch (error) {
      console.error("Failed to delete address:", error);
      toast.error("Failed to delete address.");
    }
  };

  return (
    <div className="space-y-4">
      {/* TODO: Add Search Bar Component here */}
      {/* <input
        type="text"
        placeholder="Search addresses..."
        className="w-full p-2 border rounded-md"
        value={searchTerm}
        onChange={(e) => {
          setSearchTerm(e.target.value);
          setCurrentPage(1); // Reset to first page on search
        }}
      /> */}

      <Addresses
        loading={loading}
        filteredAddresses={filteredAddresses}
        currentAddresses={currentAddresses}
        indexOfFirstItem={(currentPage - 1) * ITEMS_PER_PAGE}
        indexOfLastItem={currentPage * ITEMS_PER_PAGE}
        totalPages={totalPages}
        currentPage={currentPage}
        itemsPerPage={ITEMS_PER_PAGE}
        paginate={handlePaginate}
        searchTerm={searchTerm}
        handleActionSelect={handleActionSelect}
        setShowAddAddressModal={setShowAddModal}
      />

      {/* --- Modals --- */}
      <AddressModal
        show={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSave={handleSaveNewAddress}
        addressToEdit={null}
      />

      <AddressModal
        show={!!addressToEdit}
        onClose={() => setAddressToEdit(null)}
        onSave={handleSaveEditedAddress}
        addressToEdit={addressToEdit}
      />
    </div>
  );
}