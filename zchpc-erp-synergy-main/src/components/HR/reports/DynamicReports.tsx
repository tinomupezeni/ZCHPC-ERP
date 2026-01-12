import { useEffect, useState } from "react";
import { fetchReportData } from "@/services/reports.services";
import { Loader } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function DynamicReport({ reportType, searchTerm }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await fetchReportData(reportType);
        setData(result);
      } catch (error) {
        // Error handling handled by service/toast usually
      } finally {
        setLoading(false);
      }
    };
    
    if (reportType) {
      loadData();
    }
  }, [reportType]);

  if (loading) return <div className="flex justify-center p-10"><Loader className="animate-spin"/></div>;
  if (!data || data.length === 0) return <div className="p-10 text-center text-gray-500">No data available for this report.</div>;

  // Dynamic Table Headers based on first data item keys
  const headers = Object.keys(data[0]).filter(k => k !== 'id');

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            {headers.map(h => (
              <TableHead key={h} className="capitalize">{h.replace(/_/g, ' ')}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row: any) => (
            <TableRow key={row.id}>
              {headers.map(h => (
                <TableCell key={`${row.id}-${h}`}>
                  {/* Simple formatting for money/dates could go here */}
                  {row[h]}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}