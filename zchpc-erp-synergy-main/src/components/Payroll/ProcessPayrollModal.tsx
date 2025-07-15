import React, { useState, useEffect } from "react";
import { X, DollarSign, Check, AlertCircle, Loader, Calendar } from "lucide-react";
import { format } from "date-fns";
import Server from "@/server/Server";
import { toast } from "sonner";

const ProcessPayrollModal = ({ isOpen, onClose, payrollMonth, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [validationResults, setValidationResults] = useState(null);
  const [exchangeRate, setExchangeRate] = useState(30); // Default exchange rate
  const [selectedCurrency, setSelectedCurrency] = useState("dual"); // dual, usd, zig
  const [processingStep, setProcessingStep] = useState("validation"); // validation, confirmation, processing, results
  const [payrollDetails, setPayrollDetails] = useState(null);

  // Fetch payroll validation data when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchValidationData();
    } else {
      // Reset state when closing
      setValidationResults(null);
      setProcessingStep("validation");
      setPayrollDetails(null);
    }
  }, [isOpen]);

  const fetchValidationData = async () => {
    setLoading(true);
    try {
      const response = await Server.validatePayroll({
        month: format(payrollMonth, "yyyy-MM"),
        exchangeRate
      });
      setValidationResults(response.data);
      setProcessingStep("validation");
    } catch (error) {
      console.error("Error validating payroll:", error);
      toast.error("Failed to validate payroll data");
    } finally {
      setLoading(false);
    }
  };

  const fetchExchangeRate = async () => {
    try {
      const response = await Server.fetchExchangeRate();
      setExchangeRate(response.data.rate);
    } catch (error) {
      console.error("Error fetching exchange rate:", error);
      toast.error("Using default exchange rate");
    }
  };

  const processPayroll = async () => {
    setLoading(true);
    setProcessingStep("processing");
    try {
      const response = await Server.processPayroll({
        month: format(payrollMonth, "yyyy-MM"),
        exchangeRate,
        currencyOption: selectedCurrency
      });
      setPayrollDetails(response.data);
      setProcessingStep("results");
      toast.success("Payroll processed successfully");
      onSuccess();
    } catch (error) {
      console.error("Error processing payroll:", error);
      toast.error("Failed to process payroll");
      setProcessingStep("validation");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    setProcessingStep("confirmation");
  };

  const handleBack = () => {
    setProcessingStep("validation");
  };

  const getCurrencyLabel = () => {
    switch(selectedCurrency) {
      case "dual": return "Dual Currency (USD & ZIG)";
      case "usd": return "USD Only";
      case "zig": return "ZIG Only";
      default: return "";
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl w-full max-w-2xl shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-blue-600 p-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-white" />
            <h2 className="text-xl font-semibold text-white">
              Process Payroll - {format(payrollMonth, "MMMM yyyy")}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-blue-200 transition-colors"
            disabled={loading}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content based on current step */}
        <div className="p-6 max-h-[70vh] overflow-y-auto">
          {processingStep === "validation" && (
            <ValidationStep 
              validationResults={validationResults} 
              loading={loading}
              exchangeRate={exchangeRate}
              setExchangeRate={setExchangeRate}
              selectedCurrency={selectedCurrency}
              setSelectedCurrency={setSelectedCurrency}
              onConfirm={handleConfirm}
              onFetchExchangeRate={fetchExchangeRate}
            />
          )}

          {processingStep === "confirmation" && (
            <ConfirmationStep
              validationResults={validationResults}
              currencyOption={getCurrencyLabel()}
              exchangeRate={exchangeRate}
              onBack={handleBack}
              onProcess={processPayroll}
              loading={loading}
            />
          )}

          {processingStep === "processing" && (
            <ProcessingStep />
          )}

          {processingStep === "results" && (
            <ResultsStep 
              payrollDetails={payrollDetails}
              onClose={onClose}
            />
          )}
        </div>
      </div>
    </div>
  );
};

// Sub-components for each step
const ValidationStep = ({ 
  validationResults, 
  loading, 
  exchangeRate, 
  setExchangeRate,
  selectedCurrency,
  setSelectedCurrency,
  onConfirm,
  onFetchExchangeRate
}) => {
  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h3 className="text-lg font-medium text-gray-800">Payroll Validation</h3>
        <p className="text-sm text-gray-500 mt-1">
          Review validation results before processing payroll
        </p>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-8">
          <Loader className="h-8 w-8 animate-spin text-blue-600" />
          <p className="mt-2 text-sm text-gray-500">Validating payroll data...</p>
        </div>
      ) : validationResults ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
              <div className="text-sm font-medium text-blue-800">Employees</div>
              <div className="text-xl font-bold text-blue-600 mt-1">
                {validationResults.employeeCount}
              </div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg border border-green-100">
              <div className="text-sm font-medium text-green-800">Total Payroll (USD)</div>
              <div className="text-xl font-bold text-green-600 mt-1">
                ${validationResults.totalPayrollUSD.toFixed(2)}
              </div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg border border-purple-100">
              <div className="text-sm font-medium text-purple-800">Total Payroll (ZIG)</div>
              <div className="text-xl font-bold text-purple-600 mt-1">
                {validationResults.totalPayrollZIG.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Currency Options */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Payment Currency</h4>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setSelectedCurrency("dual")}
                className={`p-3 border rounded-lg text-sm font-medium ${selectedCurrency === "dual" ? "bg-blue-50 border-blue-200 text-blue-700" : "border-gray-200 hover:bg-gray-50"}`}
              >
                Dual Currency
              </button>
              <button
                onClick={() => setSelectedCurrency("usd")}
                className={`p-3 border rounded-lg text-sm font-medium ${selectedCurrency === "usd" ? "bg-blue-50 border-blue-200 text-blue-700" : "border-gray-200 hover:bg-gray-50"}`}
              >
                USD Only
              </button>
              <button
                onClick={() => setSelectedCurrency("zig")}
                className={`p-3 border rounded-lg text-sm font-medium ${selectedCurrency === "zig" ? "bg-blue-50 border-blue-200 text-blue-700" : "border-gray-200 hover:bg-gray-50"}`}
              >
                ZIG Only
              </button>
            </div>
          </div>

          {/* Exchange Rate */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <h4 className="text-sm font-medium text-gray-700">Exchange Rate (USD to ZIG)</h4>
              <button 
                onClick={onFetchExchangeRate}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Fetch Latest Rate
              </button>
            </div>
            <input
              type="number"
              value={exchangeRate}
              onChange={(e) => setExchangeRate(parseFloat(e.target.value))}
              step="0.01"
              min="0"
              className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Validation Issues */}
          {validationResults.issues.length > 0 && (
            <div className="border border-yellow-200 bg-yellow-50 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-yellow-800">Validation Issues Found</h4>
                  <ul className="mt-2 space-y-1 text-sm text-yellow-700">
                    {validationResults.issues.map((issue, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span>•</span>
                        <span>{issue.message} ({issue.employeeCount} employees affected)</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end pt-4">
            <button
              onClick={onConfirm}
              disabled={validationResults.issues.some(i => i.severity === "error")}
              className={`px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors ${validationResults.issues.some(i => i.severity === "error") ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              Continue to Processing
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-8 text-gray-500">
          No validation data available
        </div>
      )}
    </div>
  );
};

const ConfirmationStep = ({ 
  validationResults, 
  currencyOption, 
  exchangeRate, 
  onBack, 
  onProcess,
  loading
}) => {
  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h3 className="text-lg font-medium text-gray-800">Confirm Payroll Processing</h3>
        <p className="text-sm text-gray-500 mt-1">
          Please review the details before finalizing payroll
        </p>
      </div>

      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <div className="text-sm font-medium text-gray-700">Payroll Month</div>
            <div className="text-lg font-semibold mt-1">
              {validationResults.payrollMonth}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <div className="text-sm font-medium text-gray-700">Currency Option</div>
            <div className="text-lg font-semibold mt-1">
              {currencyOption}
            </div>
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <div className="text-sm font-medium text-gray-700">Exchange Rate</div>
          <div className="text-lg font-semibold mt-1">
            1 USD = {exchangeRate} ZIG
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <div className="text-sm font-medium text-blue-800">Total Employees</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">
              {validationResults.employeeCount}
            </div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-100">
            <div className="text-sm font-medium text-green-800">Total Amount</div>
            <div className="text-2xl font-bold text-green-600 mt-1">
              ${validationResults.totalPayrollUSD.toFixed(2)} USD
            </div>
            <div className="text-lg text-green-600 mt-1">
              {validationResults.totalPayrollZIG.toFixed(2)} ZIG
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          onClick={onProcess}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-70"
        >
          {loading && <Loader className="h-4 w-4 animate-spin" />}
          Confirm & Process Payroll
        </button>
      </div>
    </div>
  );
};

const ProcessingStep = () => {
  return (
    <div className="flex flex-col items-center justify-center py-8 space-y-4">
      <Loader className="h-12 w-12 animate-spin text-blue-600" />
      <h3 className="text-lg font-medium text-gray-800">Processing Payroll</h3>
      <p className="text-sm text-gray-500 text-center max-w-md">
        Please wait while we process the payroll. This may take a few minutes depending on the number of employees.
      </p>
      <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4">
        <div 
          className="bg-blue-600 h-2.5 rounded-full animate-pulse" 
          style={{ width: "70%" }}
        ></div>
      </div>
    </div>
  );
};

const ResultsStep = ({ payrollDetails, onClose }) => {
  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <div className="flex items-center gap-2">
          <Check className="h-5 w-5 text-green-600" />
          <h3 className="text-lg font-medium text-gray-800">Payroll Processed Successfully</h3>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Payroll for {payrollDetails.payrollMonth} has been completed
        </p>
      </div>

      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-green-50 p-4 rounded-lg border border-green-100">
            <div className="text-sm font-medium text-green-800">Processed Employees</div>
            <div className="text-2xl font-bold text-green-600 mt-1">
              {payrollDetails.processedCount}
            </div>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <div className="text-sm font-medium text-blue-800">Total Amount (USD)</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">
              ${payrollDetails.totalAmountUSD.toFixed(2)}
            </div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
            <div className="text-sm font-medium text-purple-800">Total Amount (ZIG)</div>
            <div className="text-2xl font-bold text-purple-600 mt-1">
              {payrollDetails.totalAmountZIG.toFixed(2)}
            </div>
          </div>
        </div>

        {payrollDetails.failedCount > 0 && (
          <div className="border border-red-200 bg-red-50 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-red-800">Failed Payments</h4>
                <p className="mt-1 text-sm text-red-700">
                  {payrollDetails.failedCount} payments failed to process. You can retry these individually from the payroll dashboard.
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <div className="text-sm font-medium text-gray-700">Transaction Reference</div>
          <div className="text-lg font-mono mt-1">
            {payrollDetails.transactionId || "N/A"}
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <button
          onClick={onClose}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Return to Payroll Dashboard
        </button>
      </div>
    </div>
  );
};

export default ProcessPayrollModal;