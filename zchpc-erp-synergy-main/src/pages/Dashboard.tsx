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
  Package,
  DollarSign,
  ShoppingCart,
  ArrowRight,
  Clock,
  CheckCircle2,
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

// Sample data for charts
const salesData = [
  { month: "Jan", value: 2400 },
  { month: "Feb", value: 1398 },
  { month: "Mar", value: 9800 },
  { month: "Apr", value: 3908 },
  { month: "May", value: 4800 },
  { month: "Jun", value: 3800 },
  { month: "Jul", value: 4300 },
];

const inventoryData = [
  { name: "Electronics", value: 400 },
  { name: "Office", value: 300 },
  { name: "Furniture", value: 200 },
  { name: "Supplies", value: 100 },
];

const purchaseData = [
  { category: "Equipment", amount: 12000 },
  { category: "Services", amount: 8000 },
  { category: "Materials", amount: 5000 },
  { category: "Office", amount: 3000 },
  { category: "Travel", amount: 2000 },
];

const hrData = [
  { department: "Engineering", employees: 45 },
  { department: "Sales", employees: 30 },
  { department: "Marketing", employees: 15 },
  { department: "HR", employees: 10 },
  { department: "Finance", employees: 12 },
];

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

// Recent activities
const activities = [
  {
    id: 1,
    text: "New sales order created by John",
    time: "5 minutes ago",
    module: "sales",
  },
  {
    id: 2,
    text: "Employee onboarding completed for Sarah",
    time: "1 hour ago",
    module: "hr",
  },
  {
    id: 3,
    text: "Purchase order #458 approved",
    time: "3 hours ago",
    module: "procurement",
  },
  {
    id: 4,
    text: "Inventory report generated",
    time: "5 hours ago",
    module: "inventory",
  },
  {
    id: 5,
    text: "Monthly financial report submitted",
    time: "Yesterday",
    module: "accounting",
  },
];

// Tasks due
const tasks = [
  {
    id: 1,
    text: "Review quarterly financial report",
    due: "Today",
    module: "accounting",
    done: false,
  },
  {
    id: 2,
    text: "Approve new hire requests",
    due: "Tomorrow",
    module: "hr",
    done: false,
  },
  {
    id: 3,
    text: "Finalize vendor contracts",
    due: "Today",
    module: "procurement",
    done: true,
  },
  {
    id: 4,
    text: "Update sales forecasts",
    due: "3 days",
    module: "sales",
    done: false,
  },
  {
    id: 5,
    text: "Complete inventory audit",
    due: "This week",
    module: "inventory",
    done: true,
  },
];

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => {
      setLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  const getModuleIcon = (module: string) => {
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

  const renderMetricCard = (
    title: string,
    value: string,
    icon: React.ReactNode,
    trend: string,
    path: string
  ) => (
    <Card className="hover-scale subtle-shadow">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="p-2 bg-primary/10 rounded-full">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground pt-1 flex items-center">
          <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
          {trend} from last month
        </p>
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
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back to your ZCHPC ERP dashboard
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
        {renderMetricCard(
          "Employees",
          "112",
          <Users className="h-4 w-4 text-primary" />,
          "↑ 5.4%",
          "/hr"
        )}
        {renderMetricCard(
          "Total Attendees today",
          "103",
          <Users className="h-4 w-4 text-primary" />,
          "↑ 12.2%",
          "/hr"
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
                  {tasks.map((task) => (
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
                      data={[
                        { name: "Engineering", value: 125000 },
                        { name: "Marketing", value: 75000 },
                        { name: "Sales", value: 85000 },
                        { name: "HR", value: 50000 },
                        { name: "Operations", value: 65000 },
                      ]}
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
                      {[
                        { name: "Engineering", value: 125000 },
                        { name: "Marketing", value: 75000 },
                        { name: "Sales", value: 85000 },
                        { name: "HR", value: 50000 },
                        { name: "Operations", value: 65000 },
                      ].map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[index % COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) =>
                        new Intl.NumberFormat("en-US", {
                          style: "currency",
                          currency: "USD",
                        }).format(value)
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
                    data={hrData}
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
                      {hrData.map((_, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[index % COLORS.length]}
                        />
                      ))}
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
