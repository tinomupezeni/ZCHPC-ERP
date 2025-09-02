import React, { useState, useEffect } from "react";
import { format } from "date-fns";
import { DollarSign, Search, PlusCircle, Loader, XCircle, Calendar, X } from "lucide-react";
import Server from "@/server/Server";
import { toast } from "sonner";
import { formatUSD, formatZIG } from "../ui/utils";

const CurrencyRates = () => {
  const [rates, setRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newRate, setNewRate] = useState("");
  const [selectedDate, setSelectedDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const [isAdding, setIsAdding] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchRates();
  }, []);

  const fetchRates = async () => {
    setLoading(true);
    try {
      const response = await Server.getCurrencyRates();
      console.log(response.data);
      
      setRates(response.data);
      toast.success("Currency rates fetched successfully.");
    } catch (error) {
      toast.error("Failed to fetch currency rates.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRate = async (e) => {
    e.preventDefault();
    if (newRate === "" || isNaN(newRate) || parseFloat(newRate) <= 0) {
      toast.error("Please enter a valid ZIG rate.");
      return;
    }
    if (!selectedDate) {
      toast.error("Please select a date.");
      return;
    }

    setIsAdding(true);
    try {
      const rateData = {
        date: selectedDate,
        usdRate: 1, // USD is the base currency
        zigRate: parseFloat(newRate),
      };
      await Server.addCurrencyRate(rateData);
      setNewRate("");
      setSelectedDate(format(new Date(), "yyyy-MM-dd"));
      setIsModalOpen(false);
      toast.success("New currency rate added.");
      fetchRates(); // Refresh the list
    } catch (error) {
      toast.error("Failed to add currency rate.");
      console.error(error);
    } finally {
      setIsAdding(false);
    }
  };

  const filteredRates = rates.filter(rate =>
    rate.date.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Currency Rates</h1>
          <p className="text-sm text-gray-500">
            View and manage daily exchange rates for USD and ZIG.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="e.g, 2023-08-15"
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <PlusCircle className="h-4 w-4" />
            Add Rate
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                USD
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ZIG Rate
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan="3" className="px-6 py-8 text-center">
                  <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                  <p className="mt-2 text-sm text-gray-500">
                    Loading currency rates...
                  </p>
                </td>
              </tr>
            ) : filteredRates.length > 0 ? (
              filteredRates.map((rate) => (
                <tr key={rate.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {rate.date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatUSD(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatZIG(rate.average)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3" className="px-6 py-8 text-center">
                  <div className="flex flex-col items-center justify-center">
                    <XCircle className="h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">
                      No currency rates found
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Try adjusting your search or add a new rate to get started.
                    </p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
          <div className="relative p-8 bg-white w-96 max-w-lg mx-auto rounded-lg shadow-lg">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Add New Currency Rate</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>
            <form onSubmit={handleAddRate}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Date</label>
                <div className="mt-1 relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">USD Rate</label>
                <div className="mt-1 relative">
                  <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                  <input
                    type="text"
                    value="1.00"
                    disabled
                    className="w-full pl-10 pr-4 py-2 border rounded-lg bg-gray-100 text-gray-500 cursor-not-allowed"
                  />
                </div>
              </div>
              <div className="mb-6">
                <label htmlFor="zigRate" className="block text-sm font-medium text-gray-700">ZIG Rate</label>
                <div className="mt-1 relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 font-medium">ZIG</span>
                  <input
                    id="zigRate"
                    type="number"
                    step="0.01"
                    placeholder="Enter ZIG rate"
                    value={newRate}
                    onChange={(e) => setNewRate(e.target.value)}
                    className="w-full pl-12 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAdding}
                  className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {isAdding ? <Loader className="h-4 w-4 animate-spin" /> : <PlusCircle className="h-4 w-4" />}
                  Add Rate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CurrencyRates;