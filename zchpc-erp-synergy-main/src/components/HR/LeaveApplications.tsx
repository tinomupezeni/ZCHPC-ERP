import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import {
  CheckCircle,
  XCircle,
  Clock,
  Calendar,
  User,
  FileText,
  Search,
} from "lucide-react";
import { toast } from "sonner";
import apiClient from "@/services/apiClient";
import { format } from "date-fns";

interface LeaveRequest {
  id: number;
  employee: number;
  employee_name: string;
  leave_type: number;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  number_of_days: number;
  reason: string;
  status: string;
  requested_on: string;
  reviewed_by: number | null;
  reviewed_by_name: string | null;
  review_date: string | null;
}

interface LeaveType {
  id: number;
  name: string;
  default_days_allowed: number;
}

const LeaveApplications = () => {
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRequest, setSelectedRequest] = useState<LeaveRequest | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("pending");
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");

  useEffect(() => {
    fetchLeaveRequests();
    fetchLeaveTypes();
  }, []);

  const fetchLeaveRequests = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get("/leave/requests/all/");
      setLeaveRequests(response.data);
    } catch (error) {
      console.error("Failed to fetch leave requests:", error);
      toast.error("Failed to load leave requests");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchLeaveTypes = async () => {
    try {
      const response = await apiClient.get("/leave/types/");
      setLeaveTypes(response.data);
    } catch (error) {
      console.error("Failed to fetch leave types:", error);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      // Get current user ID from localStorage or auth context
      const userStr = localStorage.getItem("user");
      const reviewerId = userStr ? JSON.parse(userStr).id : 1;

      await apiClient.post(`/leave/requests/${id}/review/`, {
        reviewer_id: reviewerId,
        approved: true,
      });
      toast.success("Leave request approved");
      fetchLeaveRequests();
      setIsDetailModalOpen(false);
    } catch (error) {
      console.error("Failed to approve leave request:", error);
      toast.error("Failed to approve leave request");
    }
  };

  const handleReject = async (id: number) => {
    try {
      // Get current user ID from localStorage or auth context
      const userStr = localStorage.getItem("user");
      const reviewerId = userStr ? JSON.parse(userStr).id : 1;

      await apiClient.post(`/leave/requests/${id}/review/`, {
        reviewer_id: reviewerId,
        approved: false,
      });
      toast.success("Leave request rejected");
      fetchLeaveRequests();
      setIsDetailModalOpen(false);
    } catch (error) {
      console.error("Failed to reject leave request:", error);
      toast.error("Failed to reject leave request");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Pending":
        return (
          <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
            <Clock className="h-3 w-3 mr-1" />
            Pending
          </Badge>
        );
      case "Approved":
        return (
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <CheckCircle className="h-3 w-3 mr-1" />
            Approved
          </Badge>
        );
      case "Rejected":
        return (
          <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
            <XCircle className="h-3 w-3 mr-1" />
            Rejected
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const filteredRequests = leaveRequests.filter((request) => {
    // Filter by tab
    if (activeTab !== "all" && request.status.toLowerCase() !== activeTab) {
      return false;
    }
    // Filter by search term
    if (
      searchTerm &&
      !request.employee_name.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    // Filter by leave type
    if (filterType !== "all" && request.leave_type.toString() !== filterType) {
      return false;
    }
    return true;
  });

  const pendingCount = leaveRequests.filter((r) => r.status === "Pending").length;
  const approvedCount = leaveRequests.filter((r) => r.status === "Approved").length;
  const rejectedCount = leaveRequests.filter((r) => r.status === "Rejected").length;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Leave Applications</h2>
          <p className="text-muted-foreground">
            Review and manage employee leave requests
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">{pendingCount}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Approved</p>
                <p className="text-2xl font-bold text-green-600">{approvedCount}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Rejected</p>
                <p className="text-2xl font-bold text-red-600">{rejectedCount}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Requests</p>
                <p className="text-2xl font-bold">{leaveRequests.length}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by employee name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Leave Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {leaveTypes.map((type) => (
                  <SelectItem key={type.id} value={type.id.toString()}>
                    {type.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Leave Requests Table */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="pending">
                Pending ({pendingCount})
              </TabsTrigger>
              <TabsTrigger value="approved">
                Approved ({approvedCount})
              </TabsTrigger>
              <TabsTrigger value="rejected">
                Rejected ({rejectedCount})
              </TabsTrigger>
              <TabsTrigger value="all">All</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading leave requests...
            </div>
          ) : filteredRequests.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No leave requests found
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Leave Type</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Days</TableHead>
                  <TableHead>Requested On</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRequests.map((request) => (
                  <TableRow key={request.id}>
                    <TableCell className="font-medium">
                      {request.employee_name}
                    </TableCell>
                    <TableCell>{request.leave_type_name}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm">
                        <Calendar className="h-3 w-3" />
                        {format(new Date(request.start_date), "MMM d")} -{" "}
                        {format(new Date(request.end_date), "MMM d, yyyy")}
                      </div>
                    </TableCell>
                    <TableCell>{request.number_of_days}</TableCell>
                    <TableCell>
                      {format(new Date(request.requested_on), "MMM d, yyyy")}
                    </TableCell>
                    <TableCell>{getStatusBadge(request.status)}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedRequest(request);
                            setIsDetailModalOpen(true);
                          }}
                        >
                          View
                        </Button>
                        {request.status === "Pending" && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-green-600 hover:text-green-700"
                              onClick={() => handleApprove(request.id)}
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700"
                              onClick={() => handleReject(request.id)}
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      <Dialog open={isDetailModalOpen} onOpenChange={setIsDetailModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Leave Request Details</DialogTitle>
            <DialogDescription>
              Review the leave request details below
            </DialogDescription>
          </DialogHeader>
          {selectedRequest && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Employee</p>
                  <p className="font-medium flex items-center gap-1">
                    <User className="h-4 w-4" />
                    {selectedRequest.employee_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Leave Type</p>
                  <p className="font-medium">{selectedRequest.leave_type_name}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Start Date</p>
                  <p className="font-medium">
                    {format(new Date(selectedRequest.start_date), "MMMM d, yyyy")}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">End Date</p>
                  <p className="font-medium">
                    {format(new Date(selectedRequest.end_date), "MMMM d, yyyy")}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Number of Days</p>
                <p className="font-medium">{selectedRequest.number_of_days} days</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Reason</p>
                <p className="font-medium">
                  {selectedRequest.reason || "No reason provided"}
                </p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                {getStatusBadge(selectedRequest.status)}
              </div>

              {selectedRequest.reviewed_by_name && (
                <div>
                  <p className="text-sm text-muted-foreground">Reviewed By</p>
                  <p className="font-medium">
                    {selectedRequest.reviewed_by_name} on{" "}
                    {selectedRequest.review_date &&
                      format(new Date(selectedRequest.review_date), "MMM d, yyyy")}
                  </p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            {selectedRequest?.status === "Pending" && (
              <>
                <Button
                  variant="outline"
                  className="text-red-600"
                  onClick={() => handleReject(selectedRequest.id)}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </Button>
                <Button
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => handleApprove(selectedRequest.id)}
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve
                </Button>
              </>
            )}
            {selectedRequest?.status !== "Pending" && (
              <Button variant="outline" onClick={() => setIsDetailModalOpen(false)}>
                Close
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LeaveApplications;
