import React, { useState } from "react";
import { Trash, PlusCircle, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { format } from "date-fns";

interface CurrencyRate {
  rate: number;
  date: Date;
}

interface Currency {
  code: string;
  rates: CurrencyRate[];
}

const CurrencyManager = () => {
  const [currencies, setCurrencies] = useState<Currency[]>([
    { code: "USD", rates: [{ rate: 1, date: new Date() }] },
    { code: "EUR", rates: [{ rate: 0.92, date: new Date() }] },
    { code: "ZWL", rates: [{ rate: 5500, date: new Date() }] },
  ]);
  const [selectedCurrency, setSelectedCurrency] = useState<string | null>(null);
  const [newRate, setNewRate] = useState({ rate: "", date: "" });

  const addRate = () => {
    if (!newRate.rate || !newRate.date || !selectedCurrency) return;

    setCurrencies((prev) =>
      prev.map((currency) =>
        currency.code === selectedCurrency
          ? {
            ...currency,
            rates: [
              { rate: parseFloat(newRate.rate), date: new Date(newRate.date) },
              ...currency.rates, // Keep history sorted
            ],
          }
          : currency
      )
    );
    setNewRate({ rate: "", date: "" });
  };

  const removeRate = (currencyCode: string, index: number) => {
    setCurrencies((prev) =>
      prev.map((currency) =>
        currency.code === currencyCode
          ? { ...currency, rates: currency.rates.filter((_, i) => i !== index) }
          : currency
      )
    );
  };

  return (
    <div className="p-6 bg-white shadow-lg rounded-xl">
      {selectedCurrency ? (
        // Currency Details Page
        <div>
          <Button className="mb-4 flex items-center gap-2" onClick={() => setSelectedCurrency(null)}>
            <ArrowLeft className="h-5 w-5" />
            Back to Currencies
          </Button>
          <h2 className="text-2xl font-bold mb-4">{selectedCurrency} Exchange Rates</h2>

          {/* Add New Rate */}
          <div className="flex gap-4 mb-4">
            <Input
              type="number"
              placeholder="New Exchange Rate"
              value={newRate.rate}
              onChange={(e) => setNewRate({ ...newRate, rate: e.target.value })}
            />
            <Input
              type="date"
              value={newRate.date}
              onChange={(e) => setNewRate({ ...newRate, date: e.target.value })}
            />
            <Button onClick={addRate} className="bg-blue-600 text-white flex items-center gap-2">
              <PlusCircle className="h-5 w-5" />
              Add Rate
            </Button>
          </div>

          {/* Exchange Rates Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Exchange Rate</TableHead>
                <TableHead>Date Added</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currencies
                .find((c) => c.code === selectedCurrency)
                ?.rates.sort((a, b) => b.date.getTime() - a.date.getTime())
                .map((rate, index) => (
                  <TableRow key={index}>
                    <TableCell>{rate.rate}</TableCell>
                    <TableCell>{format(rate.date, "yyyy-MM-dd")}</TableCell>
                    <TableCell>
                      <Button
                        size="icon"
                        variant="destructive"
                        onClick={() => removeRate(selectedCurrency, index)}
                      >
                        <Trash className="h-5 w-5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        // Currency List Page
        <div>
          <h2 className="text-2xl font-bold mb-4">Available Currencies</h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Currency</TableHead>
                <TableHead>Latest Exchange Rate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currencies.map((currency) => (
                <TableRow key={currency.code} onClick={() => setSelectedCurrency(currency.code)} className="cursor-pointer hover:bg-gray-100">
                  <TableCell>{currency.code}</TableCell>
                  <TableCell>{currency.rates[0].rate}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
      <div className="space-y-4">
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {currencies.map((cur) => (
            <div key={cur.id} className="p-4 border rounded shadow-sm">
              <p className="font-semibold">{cur.name} ({cur.code})</p>
              <p>Symbol: {cur.symbol}</p>
              <p>Rate to Base: {cur.rate_to_base}</p>
              <div className="mt-2 flex space-x-2">
                <Button size="sm" variant="outline">Edit</Button>
                <Button size="sm" variant="destructive">Delete</Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CurrencyManager;
