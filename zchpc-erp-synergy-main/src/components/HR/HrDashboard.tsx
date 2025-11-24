import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  CalendarDays,
  Briefcase,
  Award,
  Users,
  FileText,
  GraduationCap,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Server from "../../server/Server"; // Make sure to import your Server utility
import { hrDashboard } from "@/server/hr.services";
import { useNavigate } from "react-router-dom";

// Define a type or interface for the data to ensure consistency and help with autocompletion
interface HrDashboardData {
  metrics: {
    totalEmployees: number;
    totalDepartments: number;
    openPositions: number;
    inInterviewStage: number;
    timeOffRequests: number;
    pendingTimeOff: number;
  };
  newEmployees: {
    id: number;
    name: string;
    role: string;
    department: string;
    joinDate: string;
    avatarUrl?: string; // Optional avatar URL
  }[];
  trainingPrograms: {
    id: number;
    title: string;
    date: string;
    participants: number;
  }[];
  upcomingReviews: {
    id: number;
    name: string;
    date: string;
    type: string;
  }[];
}

export default function HrDashboard() {
  const [data, setData] = useState<HrDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [today, setToday] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // Set the current date when the component mounts
    const todayDate = new Date();
    const options: Intl.DateTimeFormatOptions = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    };
    setToday(todayDate.toLocaleDateString("en-US", options));

    // Fetch data from the server
    const fetchData = async () => {
      try {
        const response = await hrDashboard(); // Assuming this is your API call
        setData(response.data);
      } catch (error) {
        console.error("Failed to fetch HR dashboard data:", error);
        // Handle error, e.g., show a toast notification
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="animate-pulse-light">
          <Users className="h-10 w-10 text-blue-700" />
        </div>
      </div>
    );
  }

  // Handle case where data is not available after loading
  if (!data) {
    return (
      <div className="text-center p-8">
        <h2 className="text-2xl font-bold">No HR data available.</h2>
        <p className="text-muted-foreground mt-2">
          Please check your server connection.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Employees Card */}
        <Card className="subtle-shadow" onClick={() => navigate('/hr/hr-employees')}>
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-full">
                <Users className="h-4 w-4 text-blue-700" />
              </div>
              <CardTitle className="text-lg">Employees</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {data.metrics.totalEmployees}
            </div>
            <p className="text-sm text-muted-foreground">
              {data.metrics.totalDepartments} departments
            </p>
          </CardContent>
        </Card>

        {/* Open Positions Card */}
        <Card className="subtle-shadow" onClick={() => navigate('/hr/hr-recruitment')}>
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-green-100 rounded-full">
                <Briefcase className="h-4 w-4 text-green-700" />
              </div>
              <CardTitle className="text-lg">Open Positions</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {data.metrics.openPositions}
            </div>
            <p className="text-sm text-muted-foreground">
              {data.metrics.inInterviewStage} in interview stage
            </p>
          </CardContent>
        </Card>

        {/* Time Off Requests Card */}
        <Card className="subtle-shadow" onClick={() => navigate('/hr/hr-recruitment')}>
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-amber-100 rounded-full">
                <CalendarDays className="h-4 w-4 text-amber-700" />
              </div>
              <CardTitle className="text-lg">Time Off Requests</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {data.metrics.timeOffRequests}
            </div>
            <p className="text-sm text-muted-foreground">
              {data.metrics.pendingTimeOff} pending approval
            </p>
          </CardContent>
        </Card>
      </div>
   

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* New Employees List */}
        <Card className="subtle-shadow">
          <CardHeader>
            <CardTitle>New Employees</CardTitle>
            <CardDescription>Recently hired employees</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.newEmployees.map((employee) => (
                <div
                  key={employee.id}
                  className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale"
                >
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage
                        src={
                          employee.avatarUrl ||
                          `https://api.dicebear.com/7.x/initials/svg?seed=${employee.name}`
                        }
                        alt={employee.name}
                      />
                      <AvatarFallback>{employee.name.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{employee.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {employee.role}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className="bg-blue-100 text-blue-800">
                      {employee.department}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">
                      Joined {new Date(employee.joinDate).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                className="p-0 h-auto text-xs text-primary flex items-center"
                onClick={() => navigate("/hr/employees")}
              >
                View All Employees <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          {/* Training Programs List */}
          <Card className="subtle-shadow">
            <CardHeader>
              <CardTitle>Training Programs</CardTitle>
              <CardDescription>Upcoming employee training</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.trainingPrograms.map((training) => (
                  <div
                    key={training.id}
                    className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-primary/10 rounded-full">
                        <GraduationCap className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-medium">{training.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(training.date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-sm">
                      {training.participants} participants
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Upcoming Reviews List */}
          <Card className="subtle-shadow">
            <CardHeader>
              <CardTitle>Upcoming Reviews</CardTitle>
              <CardDescription>
                Employee performance evaluations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.upcomingReviews.map((review) => (
                  <div
                    key={review.id}
                    className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-primary/10 rounded-full">
                        <Award className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-medium">{review.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {review.type} Review
                        </p>
                      </div>
                    </div>
                    <div className="text-sm">
                      {new Date(review.date).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  className="p-0 h-auto text-xs text-primary flex items-center"
                  onClick={() => navigate("/hr/reviews")}
                >
                  <FileText className="mr-1 h-3 w-3" />
                  View Schedule <ArrowRight className="ml-1 h-3 w-3" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
