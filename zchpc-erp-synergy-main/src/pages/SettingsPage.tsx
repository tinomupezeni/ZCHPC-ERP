import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  UserPlus,
  Search,
  Edit,
  Trash2,
  UserCog,
  Lock,
  Globe,
  Database,
  BarChart4,
  User,
} from "lucide-react";
import { toast } from "sonner";
import AddUser from "@/components/AddUser";
import AddDepartment from "@/components/AddDepartment";
import Server from "@/server/Server";
import EditUserModal from "@/components/EditUserModal";
import Users from "@/components/System/Users";

// Department data
const departments = [
  { id: "1", name: "Management", employees: 3, manager: "Admin User" },
  { id: "2", name: "Sales", employees: 12, manager: "Takudzwa Nyamakanga" },
  { id: "3", name: "Human Resources", employees: 5, manager: "Sarah Mambongo" },
  { id: "4", name: "Operations", employees: 15, manager: "Robert Kawa" },
  { id: "5", name: "Finance", employees: 8, manager: "Emily Munetsi" },
  { id: "6", name: "Purchasing", employees: 6, manager: "Michael Mugadza" },
];

// Role data
const roles = [
  { id: "1", name: "Administrator", users: 1, permissions: "Full Access" },
  { id: "2", name: "Sales Manager", users: 1, permissions: "Sales, Dashboard" },
  { id: "3", name: "HR Manager", users: 1, permissions: "HR, Dashboard" },
  {
    id: "4",
    name: "Inventory Manager",
    users: 1,
    permissions: "Inventory, Dashboard",
  },
  {
    id: "5",
    name: "Accountant",
    users: 1,
    permissions: "Accounting, Dashboard",
  },
  {
    id: "6",
    name: "Procurement Officer",
    users: 1,
    permissions: "Procurement, Dashboard",
  },
];

const SettingsPage = () => {
  // const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [addUser, setAddUser] = useState(false);
  const [editUserModal, setEditUserModal] = useState(false);
  const [addDepartment, setAddDepartment] = useState(false);
  const [editEmployeeId, setEditEmployeeId] = useState('')

  // Settings state
  const [settings, setSettings] = useState({
    enableEmailNotifications: true,
    enablePushNotifications: false,
    darkMode: false,
    autoBackup: true,
    twoFactorAuth: false,
    dataRetention: 90,
    language: "English",
    timeZone: "UTC-05:00 (Eastern Time)",
  });

  const handleSettingChange = (key: string, value: any) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    toast.success(`Setting updated successfully`);
  };

 
  const fetchUsers = () => {
    Server.fetchUser()
      .then((response) => {
        console.log(response.data);
        setUsers(response.data);
      })
      .catch((error) => {
        console.log(error);
      });
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Manage system settings and users
          </p>
        </div>
      </div>

      <Tabs defaultValue="users">
        <TabsList className="mb-4 w-full md:w-auto">
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="departments">Departments</TabsTrigger>
          <TabsTrigger value="roles">Roles</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <Users setAddUser={setAddUser} />
        </TabsContent>

        <TabsContent value="departments">
          <Card className="subtle-shadow">
            <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0 pb-2">
              <CardTitle>Departments</CardTitle>
              <Button onClick={() => setAddDepartment(true)}>
                <UserCog className="mr-2 h-4 w-4" />
                Add Department
              </Button>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[80px]">ID</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Employees</TableHead>
                      <TableHead>Manager</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {departments.map((dept) => (
                      <TableRow key={dept.id}>
                        <TableCell className="font-medium">{dept.id}</TableCell>
                        <TableCell>{dept.name}</TableCell>
                        <TableCell>{dept.employees}</TableCell>
                        <TableCell>{dept.manager}</TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm">
                            Manage
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="roles">
          <Card className="subtle-shadow">
            <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0 pb-2">
              <CardTitle>User Roles</CardTitle>
              <Button>
                <Lock className="mr-2 h-4 w-4" />
                Add Role
              </Button>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[80px]">ID</TableHead>
                      <TableHead>Role Name</TableHead>
                      <TableHead>Users</TableHead>
                      <TableHead>Permissions</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {roles.map((role) => (
                      <TableRow key={role.id}>
                        <TableCell className="font-medium">{role.id}</TableCell>
                        <TableCell>{role.name}</TableCell>
                        <TableCell>{role.users}</TableCell>
                        <TableCell>{role.permissions}</TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm">
                            Edit Permissions
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences">
          <Card className="subtle-shadow">
            <CardHeader>
              <CardTitle>User Preferences</CardTitle>
              <CardDescription>
                Manage your personal preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Notifications</h3>
                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">
                      Receive email notifications for updates
                    </p>
                  </div>
                  <Switch
                    checked={settings.enableEmailNotifications}
                    onCheckedChange={(checked) =>
                      handleSettingChange("enableEmailNotifications", checked)
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Push Notifications</Label>
                    <p className="text-sm text-muted-foreground">
                      Receive push notifications in the browser
                    </p>
                  </div>
                  <Switch
                    checked={settings.enablePushNotifications}
                    onCheckedChange={(checked) =>
                      handleSettingChange("enablePushNotifications", checked)
                    }
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium">Appearance</h3>
                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Dark Mode</Label>
                    <p className="text-sm text-muted-foreground">
                      Switch to dark theme
                    </p>
                  </div>
                  <Switch
                    checked={settings.darkMode}
                    onCheckedChange={(checked) =>
                      handleSettingChange("darkMode", checked)
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>Language</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <select
                      className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-10"
                      value={settings.language}
                      onChange={(e) =>
                        handleSettingChange("language", e.target.value)
                      }
                    >
                      <option value="English">English</option>
                      <option value="Spanish">Spanish</option>
                      <option value="French">French</option>
                      <option value="German">German</option>
                      <option value="Chinese">Chinese</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Time Zone</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <select
                      className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-10"
                      value={settings.timeZone}
                      onChange={(e) =>
                        handleSettingChange("timeZone", e.target.value)
                      }
                    >
                      <option value="UTC+00:00 (GMT)">UTC+00:00 (GMT)</option>
                      <option value="UTC-05:00 (Eastern Time)">
                        UTC-05:00 (Eastern Time)
                      </option>
                      <option value="UTC-06:00 (Central Time)">
                        UTC-06:00 (Central Time)
                      </option>
                      <option value="UTC-07:00 (Mountain Time)">
                        UTC-07:00 (Mountain Time)
                      </option>
                      <option value="UTC-08:00 (Pacific Time)">
                        UTC-08:00 (Pacific Time)
                      </option>
                      <option value="UTC+01:00 (Central European Time)">
                        UTC+01:00 (Central European Time)
                      </option>
                      <option value="UTC+08:00 (China Standard Time)">
                        UTC+08:00 (China Standard Time)
                      </option>
                    </select>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system">
          <Card className="subtle-shadow">
            <CardHeader>
              <CardTitle>System Settings</CardTitle>
              <CardDescription>
                Global settings for your ERP system
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Security</h3>
                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Two-Factor Authentication</Label>
                    <p className="text-sm text-muted-foreground">
                      Require two-factor authentication for all users
                    </p>
                  </div>
                  <Switch
                    checked={settings.twoFactorAuth}
                    onCheckedChange={(checked) =>
                      handleSettingChange("twoFactorAuth", checked)
                    }
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium">Data Management</h3>
                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Automatic Backups</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically backup system data daily
                    </p>
                  </div>
                  <Switch
                    checked={settings.autoBackup}
                    onCheckedChange={(checked) =>
                      handleSettingChange("autoBackup", checked)
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>Data Retention (days)</Label>
                  <div className="relative">
                    <Database className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="number"
                      placeholder="90"
                      className="pl-10"
                      value={settings.dataRetention}
                      onChange={(e) =>
                        handleSettingChange(
                          "dataRetention",
                          parseInt(e.target.value)
                        )
                      }
                    />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Number of days to keep logs and transaction history
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium">System Information</h3>
                <Separator />

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Version</span>
                    <span className="text-sm">ZCHPC ERP v1.0.0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Last Updated</span>
                    <span className="text-sm">October 30, 2023</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Database Size</span>
                    <span className="text-sm">142 MB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Total Users</span>
                    <span className="text-sm">6 active</span>
                  </div>
                </div>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline">
                    <BarChart4 className="mr-2 h-4 w-4" />
                    System Diagnostics
                  </Button>
                  <Button>
                    <Database className="mr-2 h-4 w-4" />
                    Run Backup Now
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      {addUser && (
        <AddUser
          setShowModal={() => setAddUser(false)}
          onSuccess={() => fetchUsers()}
        />
      )}
      {editUserModal && <EditUserModal  closeModal={() => setEditUserModal(false)} userId={editEmployeeId} />}
      {addDepartment && (
        <AddDepartment
          setShowModal={() => setAddDepartment(false)}
          onSuccess={undefined}
        />
      )}
    </div>
  );
};

export default SettingsPage;
