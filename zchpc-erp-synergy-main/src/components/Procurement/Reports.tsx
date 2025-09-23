import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface Report {
  id: string;
  title: string;
  type: string;
  generated_on: string;
}

const mockReports: Report[] = [
  { id: "R-001", title: "Monthly Procurement Summary", type: "PDF", generated_on: "2025-09-01" },
  { id: "R-002", title: "Supplier Performance", type: "Excel", generated_on: "2025-09-05" },
  { id: "R-003", title: "Budget Utilization", type: "PDF", generated_on: "2025-09-10" },
];

const Reports = () => {
  const [reports] = useState(mockReports);

  if (reports.length === 0)
    return <div className="p-4 text-center text-gray-500">No reports available</div>;

  return (
    <div className="space-y-4">
      {reports.map((r) => (
        <Card key={r.id} className="hover:shadow-lg transition">
          <CardHeader>
            <CardTitle>{r.title}</CardTitle>
            <CardDescription>{r.type}</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Generated On: {new Date(r.generated_on).toLocaleDateString()}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default Reports;
