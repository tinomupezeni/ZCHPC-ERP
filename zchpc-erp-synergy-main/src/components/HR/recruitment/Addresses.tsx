// src/components/ListedAddresses.tsx
import { Loader, MapPin, Plus } from "lucide-react";
import React from "react";
import { Address } from "../types"; // Adjust path as needed

// Define the component's props
interface ListedAddressesProps {
  loading: boolean;
  filteredAddresses: Address[];
  currentAddresses: Address[];
  indexOfFirstItem: number;
  indexOfLastItem: number;
  totalPages: number;
  currentPage: number;
  itemsPerPage: number;
  paginate: (pageNumber: number) => void;
  searchTerm: string;
  handleActionSelect: (action: string, address: Address) => void;
  setShowAddAddressModal: (show: boolean) => void;
}

// Renamed function to match component name
export default function ListedAddresses({
  loading,
  filteredAddresses,
  currentAddresses,
  indexOfFirstItem,
  indexOfLastItem,
  totalPages,
  currentPage,
  itemsPerPage,
  paginate,
  searchTerm,
  handleActionSelect,
  setShowAddAddressModal,
}: ListedAddressesProps) {
  return (
    <div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            {/* ... thead ... */}
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Label
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Street Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  City / State
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Postal Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Country
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center">
                    <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                    <p className="mt-2 text-sm text-gray-500">
                      Loading addresses...
                    </p>
                  </td>
                </tr>
              ) : currentAddresses?.length > 0 ? ( // Removed optional chaining
                currentAddresses?.map((address) => (
                  <tr key={address.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {address.label}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {address.street}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {address.city}, {address.state}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {address.postalCode}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {address.country}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="inline-block">
                        <select
                          defaultValue=""
                          onChange={(e) => {
                            const action = e.target.value;
                            handleActionSelect(action, address);
                            setTimeout(() => {
                              (e.target as HTMLSelectElement).value = "";
                            }, 150);
                          }}
                          className="border rounded px-3 py-1 text-sm focus:outline-none"
                        >
                          <option value="" disabled>
                            Actions
                          </option>
                          <option value="edit">Edit Address</option>
                          <option value="delete">Delete Address</option>
                        </select>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                // ... No addresses found state ...
                <tr> 
                  <td colSpan={6} className="px-6 py-8 text-center">
                    <div className="flex flex-col items-center justify-center">
                      <MapPin className="h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">
                        No addresses found
                      </h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {searchTerm
                          ? "Try adjusting your search or filter"
                          : "Add a new address to get started"}
                      </p>
                      {!searchTerm && (
                        <button
                          type="button"
                          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none"
                          onClick={() => setShowAddAddressModal(true)}
                        >
                          <Plus className="-ml-1 mr-2 h-5 w-5" />
                          Add Address
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {filteredAddresses?.length > itemsPerPage && ( // Removed optional chaining
          <div className="px-6 py-4 border-t flex items-center justify-between">
            {/* ... Pagination controls ... */}
            <div className="text-sm text-gray-500">
              Showing{" "}
              <span className="font-medium">{indexOfFirstItem + 1}</span> to{" "}
              <span className="font-medium">
                {Math.min(indexOfLastItem, filteredAddresses.length)}
              </span>{" "}
              of <span className="font-medium">{filteredAddresses.length}</span>{" "}
              results
            </div>
            {/* ... Pagination buttons ... */}
          </div>
        )}
      </div>
    </div>
  );
}