import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart3,
  TrendingUp,
  Users,
  Clock,
  CheckCircle2,
  ShoppingCart,
  DollarSign,
  Package,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { useNavigate } from "react-router-dom";
import Server from "../server/Server"; // Make sure to import your Server utility

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    metrics: {
      total_employees: 0,
      total_attendees: 0,
    },
    charts: {
      employee_distribution: [],
      payroll_distribution: [],
    },
    lists: {
      recent_activities: [],
      tasks_due: [],
    },
  });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [today, setToday] = useState(""); // Add this state for the date

  useEffect(() => {
    const todayDate = new Date();
    const options = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    };
    setToday(todayDate.toLocaleDateString("en-US", options));

    const fetchData = async () => {
      try {
        const response = await Server.fetchDashboardData(); // Assuming this is your API call
        setDashboardData(response.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        // Handle error, e.g., show a toast notification
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getModuleIcon = (module) => {
    switch (module) {
      case "sales":
        return <ShoppingCart className="h-4 w-4 text-blue-500" />;
      case "hr":
        return <Users className="h-4 w-4 text-green-500" />;
      case "procurement":
        return <DollarSign className="h-4 w-4 text-amber-500" />;
      case "inventory":
        return <Package className="h-4 w-4 text-purple-500" />;
      case "accounting":
        return <BarChart3 className="h-4 w-4 text-red-500" />;
      default:
        return <BarChart3 className="h-4 w-4" />;
    }
  };

  const renderMetricCard = (title, value, icon, path) => (
    <Card className="hover-scale subtle-shadow">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="p-2 bg-primary/10 rounded-full">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>

        <Button
          variant="ghost"
          size="sm"
          className="mt-2 p-0 h-auto text-xs text-primary flex items-center"
          onClick={() => navigate(path)}
        >
          View details <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="animate-pulse-light">
          <BarChart3 className="h-10 w-10 text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back to your ZCHPC ERP dashboard
          </p>
        </div>
        <Card className="subtle-shadow flex items-center p-4">
          <div className="text-right">
            <p className="text-xl font-semibold text-primary">{today}</p>
            <p className="text-sm text-muted-foreground font-bold">Current Date</p>
          </div>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
        {renderMetricCard(
          "Total Employees",
          dashboardData.metrics.total_employees.toString(),
          <Users className="h-4 w-4 text-primary" />,
          "/hr"
        )}
        {renderMetricCard(
          "Total Attendees Today",
          dashboardData.metrics.total_attendees.toString(),
          <Users className="h-4 w-4 text-primary" />,
          "/attendence"
        )}
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="payroll">Payroll</TabsTrigger>
          <TabsTrigger value="hr">HR</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-1">
            <Card className="subtle-shadow">
              <CardHeader>
                <CardTitle>Tasks Due</CardTitle>
                <CardDescription>
                  Upcoming tasks requiring your attention
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboardData.lists.tasks_due.map((task) => (
                    <div key={task.id} className="flex items-start">
                      <div className="mr-3 mt-0.5">
                        {task.done ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <Clock className="h-4 w-4 text-amber-500" />
                        )}
                      </div>
                      <div className="space-y-1 flex-1">
                        <p
                          className={`text-sm ${
                            task.done
                              ? "line-through text-muted-foreground"
                              : ""
                          }`}
                        >
                          {task.text}
                        </p>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center text-xs text-muted-foreground">
                            {getModuleIcon(task.module)}
                            <span className="ml-1">{task.module}</span>
                          </div>
                          <span className="text-xs font-medium">
                            {task.due}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="payroll" className="space-y-4">
          <Card className="subtle-shadow">
            <CardHeader>
              <CardTitle>Payroll Distribution</CardTitle>
              <CardDescription>Current payroll by department</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={dashboardData.charts.payroll_distribution.map(
                        (item) => ({
                          name: item.employee__department,
                          value:
                            parseFloat(item.total_usd) +
                            parseFloat(item.total_zig),
                        })
                      )}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                    >
                      {dashboardData.charts.payroll_distribution.map(
                        (_, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={COLORS[index % COLORS.length]}
                          />
                        )
                      )}
                    </Pie>
                    <Tooltip
                      formatter={(value) =>
                        new Intl.NumberFormat("en-US", {
                          style: "currency",
                          currency: "USD",
                        }).format(Number(value))
                      }
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-end mt-4">
                <Button onClick={() => navigate("/payroll")}>
                  View Payroll Module
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hr" className="space-y-4">
          <Card className="subtle-shadow">
            <CardHeader>
              <CardTitle>Employee Distribution</CardTitle>
              <CardDescription>Employees by department</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={dashboardData.charts.employee_distribution.map(
                      (item) => ({
                        department: item.department,
                        employees: item.employees,
                      })
                    )}
                    margin={{
                      top: 5,
                      right: 30,
                      left: 20,
                      bottom: 5,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="department" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="employees" fill="#8884d8">
                      {dashboardData.charts.employee_distribution.map(
                        (_, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={COLORS[index % COLORS.length]}
                          />
                        )
                      )}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-end mt-4">
                <Button onClick={() => navigate("/hr")}>View HR Module</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;
