"use client";

import { useEffect, useState } from "react";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { Badge } from "../ui/badge";
import { RefreshCw, ShieldAlert, LogIn } from "lucide-react";
import { format } from "date-fns";
import Server from "@/services/Server";

export const Logs = ({ fetchLogs }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await Server.fetchLogs(); // ✅ function passed in as prop
      console.log(data.data);
      
      setLogs(data.data);
    } catch (err) {
      console.error("Failed to fetch logs:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const getEventBadge = (eventType: string) => {
    switch (eventType) {
      case "SUCCESS":
        return (
          <Badge className="bg-green-100 text-green-800 hover:bg-green-200">
            <LogIn className="w-3 h-3 mr-1" /> Success
          </Badge>
        );
      case "FAILED":
        return (
          <Badge className="bg-red-100 text-red-800 hover:bg-red-200">
            <ShieldAlert className="w-3 h-3 mr-1" /> Failed
          </Badge>
        );
      case "LOCKOUT":
        return (
          <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-200">
            Locked Out
          </Badge>
        );
      case "FORCE_RESET":
        return (
          <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">
            Force Reset
          </Badge>
        );
      default:
        return <Badge>Unknown</Badge>;
    }
  };

  return (
    <Card className="subtle-shadow">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0 pb-2">
        <CardTitle>Login Audit Logs</CardTitle>
        <Button variant="outline" size="sm" onClick={loadLogs} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Event</TableHead>
                <TableHead>IP</TableHead>
                <TableHead>User Agent</TableHead>
                <TableHead>Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length > 0 ? (
                logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{log.id}</TableCell>
                    <TableCell>{log.username_attempted || "N/A"}</TableCell>
                    <TableCell>{getEventBadge(log.event_type)}</TableCell>
                    <TableCell>{log.ip_address || "N/A"}</TableCell>
                    <TableCell className="truncate max-w-[200px]">
                      {log.user_agent || "N/A"}
                    </TableCell>
                    <TableCell>
                      {log.timestamp
                        ? format(new Date(log.timestamp), "PPpp")
                        : "N/A"}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-gray-500">
                    No logs available
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};
