import { useEffect, useState, forwardRef, useImperativeHandle, useMemo } from "react";
import { fetchReportData, exportReportToCSV, ReportData } from "@/services/reports.services";
import { Loader } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface DynamicReportProps {
  reportType: string;
  searchTerm: string;
  period?: string;
  department?: string;
  refreshKey?: number;
}

const DynamicReport = forwardRef<{ exportData: () => void }, DynamicReportProps>(
  ({ reportType, searchTerm, period, department, refreshKey }, ref) => {
    const [data, setData] = useState<ReportData[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
      const loadData = async () => {
        setLoading(true);
        try {
          const filters = {
            period: period || undefined,
            department: department || undefined,
          };
          const result = await fetchReportData(reportType, filters);
          setData(result);
        } catch (error) {
          console.error("Failed to fetch report data:", error);
        } finally {
          setLoading(false);
        }
      };

      if (reportType) {
        loadData();
      }
    }, [reportType, period, department, refreshKey]);

    // Expose export function to parent
    useImperativeHandle(ref, () => ({
      exportData: () => {
        if (data.length > 0) {
          const filename = `${reportType}_report_${new Date().toISOString().split("T")[0]}`;
          exportReportToCSV(data, filename);
        }
      },
    }));

    // Filter data by search term
    const filteredData = useMemo(() => {
      if (!searchTerm.trim()) return data;
      const term = searchTerm.toLowerCase();
      return data.filter((row) =>
        Object.values(row).some((val) =>
          String(val).toLowerCase().includes(term)
        )
      );
    }, [data, searchTerm]);

    // Format cell values for display
    const formatValue = (key: string, value: any): string => {
      if (value === null || value === undefined) return "N/A";
      // Format currency fields
      if (key.includes("usd") || key.includes("salary") || key.includes("_usd")) {
        const num = parseFloat(value);
        if (!isNaN(num)) {
          return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(num);
        }
      }
      if (key.includes("zig") || key.includes("_zig")) {
        const num = parseFloat(value);
        if (!isNaN(num)) {
          return `ZiG ${num.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
        }
      }
      return String(value);
    };

    if (loading) {
      return (
        <div className="flex justify-center p-10">
          <Loader className="animate-spin" />
        </div>
      );
    }

    if (!filteredData || filteredData.length === 0) {
      return (
        <div className="p-10 text-center text-gray-500">
          {data.length > 0 && searchTerm
            ? "No results match your search."
            : "No data available for this report."}
        </div>
      );
    }

    // Dynamic Table Headers based on first data item keys
    const headers = Object.keys(filteredData[0]).filter((k) => k !== "id");

    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {headers.map((h) => (
                <TableHead key={h} className="capitalize whitespace-nowrap">
                  {h.replace(/_/g, " ")}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.map((row: ReportData) => (
              <TableRow key={row.id}>
                {headers.map((h) => (
                  <TableCell key={`${row.id}-${h}`} className="whitespace-nowrap">
                    {formatValue(h, row[h])}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="px-4 py-2 text-xs text-gray-500 border-t bg-gray-50">
          Showing {filteredData.length} of {data.length} records
        </div>
      </div>
    );
  }
);

DynamicReport.displayName = "DynamicReport";

export default DynamicReport;