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
  UserPlus,
  FileText,
  GraduationCap,
  DollarSign,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
export default function HrDashboard() {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-blue-100 rounded-full">
                <Users className="h-4 w-4 text-blue-700" />
              </div>
              <CardTitle className="text-lg">Employees</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">11</div>
            <p className="text-sm text-muted-foreground">6 departments</p>
          </CardContent>
        </Card>

        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-green-100 rounded-full">
                <Briefcase className="h-4 w-4 text-green-700" />
              </div>
              <CardTitle className="text-lg">Open Positions</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">8</div>
            <p className="text-sm text-muted-foreground">
              4 in interview stage
            </p>
          </CardContent>
        </Card>

        <Card className="subtle-shadow">
          <CardHeader className="pb-2">
            <div className="flex items-center space-x-2">
              <div className="p-2 bg-amber-100 rounded-full">
                <CalendarDays className="h-4 w-4 text-amber-700" />
              </div>
              <CardTitle className="text-lg">Time Off Requests</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">6</div>
            <p className="text-sm text-muted-foreground">3 pending approval</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="subtle-shadow">
          <CardHeader>
            <CardTitle>New Employees</CardTitle>
            <CardDescription>Recently hired employees</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                {
                  name: "Maxwell Marara",
                  role: "Marketing Manager",
                  department: "Marketing",
                  joinDate: "2023-10-15",
                },
                {
                  name: "David Dube",
                  role: "Software Engineer",
                  department: "Engineering",
                  joinDate: "2023-10-12",
                },
                {
                  name: "Lisa Marwei",
                  role: "Sales Representative",
                  department: "Sales",
                  joinDate: "2023-10-10",
                },
                {
                  name: "Michael Muramba",
                  role: "Financial Analyst",
                  department: "Finance",
                  joinDate: "2023-10-05",
                },
                {
                  name: "Sarah Moyo",
                  role: "Customer Support",
                  department: "Operations",
                  joinDate: "2023-10-02",
                },
              ].map((employee, i) => (
                <div
                  key={i}
                  className="flex justify-between items-center p-3 rounded-md hover:bg-muted hover-scale"
                >
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage
                        src={`https://api.dicebear.com/7.x/initials/svg?seed=${employee.name}`}
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
              <Button variant="outline" size="sm">
                View All Employees
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="subtle-shadow">
            <CardHeader>
              <CardTitle>Training Programs</CardTitle>
              <CardDescription>Upcoming employee training</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    title: "Leadership Skills",
                    date: "2023-11-10",
                    participants: 12,
                  },
                  {
                    title: "Technical Workshop",
                    date: "2023-11-15",
                    participants: 18,
                  },
                  {
                    title: "Safety Training",
                    date: "2023-11-20",
                    participants: 25,
                  },
                ].map((training, i) => (
                  <div
                    key={i}
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

          <Card className="subtle-shadow">
            <CardHeader>
              <CardTitle>Upcoming Reviews</CardTitle>
              <CardDescription>
                Employee performance evaluations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { name: "Robert Mapepi", date: "2023-11-05", type: "Annual" },
                  {
                    name: "Emily Dangamvura",
                    date: "2023-11-08",
                    type: "Quarterly",
                  },
                  { name: "James Marawa", date: "2023-11-12", type: "Project" },
                ].map((review, i) => (
                  <div
                    key={i}
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
                <Button variant="outline" size="sm">
                  <FileText className="mr-2 h-4 w-4" />
                  View Schedule
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
