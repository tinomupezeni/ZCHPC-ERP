import { Download } from "lucide-react";
import { format } from "date-fns";
import { formatUSD, formatZIG } from "../ui/utils";

export default function PayslipModal({ PayrollRecord, setShowPayslip }) {
  const baseUSD = parseFloat(PayrollRecord.base_salary_usd);
  const netUSD = parseFloat(PayrollRecord.net_salary_usd);
  const baseZIG = parseFloat(PayrollRecord.base_salary_zig);
  const netZIG = parseFloat(PayrollRecord.net_salary_zig);
  const rate = parseFloat(PayrollRecord.exchange_rate);

  const deductions = [
    {
      name: "PAYE",
      usd: parseFloat(PayrollRecord.paye_usd),
      zig: parseFloat(PayrollRecord.paye_zig),
    },
    {
      name: "AIDS Levy",
      usd: parseFloat(PayrollRecord.aids_levy_usd),
      zig: parseFloat(PayrollRecord.aids_levy_zig),
    },
    {
      name: "NSSA (Employee)",
      usd: parseFloat(PayrollRecord.nssa_employee_usd),
      zig: parseFloat(PayrollRecord.nssa_employee_zig),
    },
  ];

  const totalDeductionsUSD = deductions.reduce((sum, d) => sum + d.usd, 0);
  const totalDeductionsZIG = deductions.reduce((sum, d) => sum + d.zig, 0);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b flex justify-between items-center">
          <h2 className="text-2xl font-bold">Payslip</h2>
          <div className="flex gap-4">
            <button
              onClick={setShowPayslip}
              className="text-gray-500 hover:text-gray-700"
            >
              Close
            </button>
            <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg">
              <Download className="h-4 w-4" />
              Download PDF
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Employee + Payment Details */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-2">Employee Details</h3>
              <div className="space-y-2 text-sm">
                <p>
                  <span className="text-gray-500">Name:</span>{" "}
                  {PayrollRecord.employee_name} {PayrollRecord.employee_surname}
                </p>
                <p>
                  <span className="text-gray-500">Employee ID:</span>{" "}
                  {PayrollRecord.employee_id}
                </p>
                <p>
                  <span className="text-gray-500">Department:</span>{" "}
                  {PayrollRecord.employee_department}
                </p>
              </div>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Payment Details</h3>
              <div className="space-y-2 text-sm">
                <p>
                  <span className="text-gray-500">Period:</span>{" "}
                  {PayrollRecord.period}
                </p>
                <p>
                  <span className="text-gray-500">Payment Date:</span>{" "}
                  {format(new Date(), "MMMM dd, yyyy")}
                </p>
                <p>
                  <span className="text-gray-500">Exchange Rate:</span> 1 USD =
                  {rate} ZIG
                </p>
              </div>
            </div>
          </div>

          {/* Salary Table */}
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Description
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    USD
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    ZIG
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {/* Gross Salary */}
                <tr>
                  <td className="px-6 py-4 text-sm font-medium">Basic Salary</td>
                  <td className="px-6 py-4 text-sm text-right">
                    {formatUSD(baseUSD)}
                  </td>
                  <td className="px-6 py-4 text-sm text-right">
                    {formatZIG(baseZIG)}
                  </td>
                </tr>

                {/* Allowances if any */}
                {parseFloat(PayrollRecord.total_allowances_usd) > 0 && (
                  <tr>
                    <td className="px-6 py-4 text-sm">Allowances</td>
                    <td className="px-6 py-4 text-sm text-right">
                      {formatUSD(PayrollRecord.total_allowances_usd)}
                    </td>
                    <td className="px-6 py-4 text-sm text-right">
                      {formatZIG(PayrollRecord.total_allowances_zig)}
                    </td>
                  </tr>
                )}

                {/* Deductions */}
                <tr className="bg-red-50">
                  <td className="px-6 py-4 text-sm font-medium">Deductions</td>
                  <td className="px-6 py-4 text-sm text-right font-medium">
                    -{formatUSD(totalDeductionsUSD)}
                  </td>
                  <td className="px-6 py-4 text-sm text-right font-medium">
                    -{formatZIG(totalDeductionsZIG)}
                  </td>
                </tr>
                {deductions.map((d, i) => (
                  <tr key={i}>
                    <td className="px-6 py-4 text-sm pl-10">{d.name}</td>
                    <td className="px-6 py-4 text-sm text-right text-red-600">
                      -{formatUSD(d.usd)}
                    </td>
                    <td className="px-6 py-4 text-sm text-right text-red-600">
                      -{formatZIG(d.zig)}
                    </td>
                  </tr>
                ))}

                {/* Net Salary */}
                <tr className="bg-gray-100 font-semibold border-t-2 border-gray-300">
                  <td className="px-6 py-4 text-sm">Net Salary</td>
                  <td className="px-6 py-4 text-sm text-right">
                    {formatUSD(netUSD)}
                  </td>
                  <td className="px-6 py-4 text-sm text-right">
                    {formatZIG(netZIG)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Summary</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600">Gross Pay (USD)</p>
                <p className="text-xl font-bold">{formatUSD(baseUSD)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Deductions (USD)</p>
                <p className="text-xl font-bold text-red-600">
                  -{formatUSD(totalDeductionsUSD)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Net Pay (USD)</p>
                <p className="text-2xl font-bold">{formatUSD(netUSD)}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mt-4">
              <div>
                <p className="text-sm text-gray-600">Gross Pay (ZiG)</p>
                <p className="text-xl font-bold">{formatZIG(baseZIG)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Deductions (ZiG)</p>
                <p className="text-xl font-bold text-red-600">
                  -{formatZIG(totalDeductionsZIG)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Net Pay (ZiG)</p>
                <p className="text-2xl font-bold">{formatZIG(netZIG)}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
