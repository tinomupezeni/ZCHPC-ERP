import { Download } from "lucide-react";
import { format } from "date-fns";
import { formatUSD, formatZIG } from "../ui/utils";

export default function PayslipModal({ PayrollRecord, setShowPayslip }) {
  // Backend-calculated salaries
  const baseUSD = parseFloat(PayrollRecord.base_salary_usd);
  const netUSD = parseFloat(PayrollRecord.net_salary_usd);
  const baseZIG = parseFloat(PayrollRecord.base_salary_zig);
  const netZIG = parseFloat(PayrollRecord.net_salary_zig);
  const rate = parseFloat(PayrollRecord.exchange_rate);

  // ZIMRA deductions = base - net
  const zimraUSD = baseUSD - netUSD;
  const zimraZIG = baseZIG - netZIG;

  const deductions = [
    {
      name: "ZIMRA PAYE + AIDS Levy",
      usd:
        baseUSD - netUSD - PayrollRecord.nssa_usd - PayrollRecord.pension_usd,
      zig:
        baseZIG - netZIG - PayrollRecord.nssa_zig - PayrollRecord.pension_zig,
    },
    {
      name: "NSSA Contribution",
      usd: parseFloat(PayrollRecord.nssa_usd),
      zig: parseFloat(PayrollRecord.nssa_zig),
    },
    // {
    //   name: "Pension Contribution",
    //   usd: parseFloat(PayrollRecord.pension_usd),
    //   zig: parseFloat(PayrollRecord.pension_zig),
    // },
  ];

  const totalDeductionsUSD = deductions.reduce(
    (sum, item) => sum + item.usd,
    0
  );
  const totalDeductionsZIG = deductions.reduce(
    (sum, item) => sum + item.zig,
    0
  );

  return (
    <div>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b">
            <div className="flex justify-between items-center">
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
          </div>

          <div className="p-6 space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Employee Details</h3>
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="text-gray-500">Name:</span>{" "}
                    {PayrollRecord.employee_name}
                  </p>
                  <p>
                    <span className="text-gray-500">Employee ID:</span>{" "}
                    {PayrollRecord.employee_id}
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
                    <span className="text-gray-500">Exchange Rate:</span> 1 USD
                    = {PayrollRecord.exchange_rate} ZIG
                  </p>
                </div>
              </div>
            </div>

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
                  {/* Base Salary */}
                  <tr>
                    <td className="px-6 py-4 text-sm font-medium">
                      Basic Salary
                    </td>
                    <td className="px-6 py-4 text-sm text-right">
                      {formatUSD(baseUSD)}
                    </td>
                    <td className="px-6 py-4 text-sm text-right">
                      {formatZIG(baseZIG)}
                    </td>
                  </tr>

                  {/* Deductions */}
                  <tr className="bg-red-50">
                    <td className="px-6 py-4 text-sm font-medium">
                      Deductions
                    </td>
                    <td className="px-6 py-4 text-sm text-right font-medium">
                      -{formatUSD(totalDeductionsUSD)}
                    </td>
                    <td className="px-6 py-4 text-sm text-right font-medium">
                      -{formatZIG(totalDeductionsZIG)}
                    </td>
                  </tr>
                  {deductions.map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 text-sm pl-10">{item.name}</td>
                      <td className="px-6 py-4 text-sm text-right text-red-600">
                        -{formatUSD(item.usd)}
                      </td>
                      <td className="px-6 py-4 text-sm text-right text-red-600">
                        -{formatZIG(item.zig)}
                      </td>
                    </tr>
                  ))}

                  {/* Net Salary */}
                  <tr className="bg-gray-100 font-medium border-t-2 border-gray-300">
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

            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Payment Summary</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Gross Pay (USD)</p>
                  <p className="text-xl font-bold">{formatUSD(baseUSD)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">
                    ZIMRA Deductions (USD)
                  </p>
                  <p className="text-xl font-bold text-red-600">
                    -{formatUSD(zimraUSD)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Net Pay (USD)</p>
                  <p className="text-2xl font-bold">{formatUSD(netUSD)}</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Gross Pay (ZiG)</p>
                  <p className="text-xl font-bold">{formatZIG(baseZIG)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">
                    ZIMRA Deductions (ZiG)
                  </p>
                  <p className="text-xl font-bold text-red-600">
                    -{formatZIG(zimraZIG)}
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
    </div>
  );
}
