import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  BarChart3,
  LayoutDashboard,
  LogOut,
  Settings,
  Users,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  ChevronDown,
  ChevronUp,
  CreditCard,
  DollarSign,
  Package,
  FileText,
  ShoppingCart,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

interface MainLayoutProps {
  children: React.ReactNode;
  setOpenTab: (value: string) => void;
}

interface SidebarItem {
  title: string;
  icon: React.ElementType;
  path: string;
  permission: string;
  subItems?: {
    title: string;
    path: string;
    permission: string;
  }[];
}

// Navigation items with permissions and subitems
const navItems: SidebarItem[] = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    path: "/dashboard",
    permission: "admin",
  },
  {
    title: "HR",
    icon: Users,
    path: "/hr",
    permission: "hr",
    subItems: [
      { title: "Employees", path: "#hr-employees", permission: "hr" },
      { title: "Attendance", path: "#hr-attendance", permission: "hr" },
      { title: "Recruitment", path: "#hr-recruitment", permission: "hr" },
      {
        title: "Performance Management",
        path: "#hr-performance",
        permission: "hr",
      },
      {
        title: "Training & Development",
        path: "#hr-training",
        permission: "hr",
      },
    ],
  },
  {
    title: "Payroll",
    icon: CreditCard,
    path: "/payroll",
    permission: "hr",
    subItems: [
      { title: "Employees", path: "#employees", permission: "hr" },
      { title: "Salary Setup", path: "#salary-setup", permission: "hr" },
      { title: "Deductions", path: "#deductions", permission: "hr" },
      { title: "Tax Tables", path: "#tax-tables", permission: "hr" },
      { title: "Payroll Period", path: "#payroll-period", permission: "hr" },
      { title: "Process Payroll", path: "#process-payroll", permission: "hr" },
      { title: "Payslips", path: "#payslips", permission: "hr" },
      { title: "Compliance Reports", path: "#reports", permission: "hr" },
    ],
  },
  { title: "Sales", icon: ShoppingCart, path: "/sales", permission: "sales" },
  {
    title: "Accounting",
    icon: DollarSign,
    path: "/accounting",
    permission: "accounting",
    subItems: [
      {
        title: "General Ledger",
        path: "#accounting-general-ledger",
        permission: "accounting",
      },
      {
        title: "Currencies",
        path: "#accounting-currencies",
        permission: "accounting",
      },
      {
        title: "Accounts Payable",
        path: "#accounting-payable",
        permission: "accounting",
      },
      {
        title: "Accounts Receivable",
        path: "#accounting-receivable",
        permission: "accounting",
      },
      {
        title: "Financial Reports",
        path: "#accounting-reports",
        permission: "accounting",
      },
      {
        title: "Tax Management",
        path: "#accounting-tax",
        permission: "accounting",
      },
    ],
  },
  {
    title: "Procurement",
    icon: FileText,
    path: "/procurement",
    permission: "procurement",
    subItems: [
      {
        title: "Orders",
        path: "#procurement/orders",
        permission: "procurement",
      },
      {
        title: "Suppliers",
        path: "#procurement/suppliers",
        permission: "procurement",
      },
      {
        title: "Reports",
        path: "#procurement/reports",
        permission: "procurement",
      },
    ],
  },
  {
    title: "Inventory",
    icon: Package,
    path: "/inventory",
    permission: "inventory",
    subItems: [
      { title: "Stock", path: "/inventory/stock", permission: "inventory" },
      {
        title: "Categories",
        path: "#inventory/categories",
        permission: "inventory",
      },
      {
        title: "Movements",
        path: "#inventory/movements",
        permission: "inventory",
      },
    ],
  },

  {
    title: "Settings",
    icon: Settings,
    path: "/settings",
    permission: "admin",
    subItems: [
      { title: "General", path: "#settings/general", permission: "admin" },
      { title: "Users", path: "#settings/users", permission: "admin" },
      {
        title: "Permissions",
        path: "#settings/permissions",
        permission: "admin",
      },
    ],
  },
];

const MainLayout: React.FC<MainLayoutProps> = ({ children, setOpenTab }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>(
    {}
  );
  const { user, logout, checkPermission } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  const toggleItemExpand = (path: string) => {
    navigate(path);
    setOpenTab("");
    setExpandedItems((prev) => ({
      ...Object.fromEntries(Object.keys(prev).map((key) => [key, false])),
      [path]: !prev[path],
    }));
  };

  const handleNavigation = (path: string) => {
    setOpenTab("");
    setOpenTab(path);
    setMobileMenuOpen(false);
    navigate(path);
  };

  const isActivePath = (path: string) => {
    return location.pathname === path || location.hash === path;
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 z-20 flex h-full flex-col border-r bg-card transition-all duration-300 ease-in-out",
          collapsed ? "w-[70px]" : "w-[240px]",
          "hidden md:flex"
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 py-4">
          <div
            className={cn(
              "flex items-center",
              collapsed && "justify-center w-full"
            )}
          >
            {!collapsed && (
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-6 w-6 text-primary" />
                <span className="text-lg font-semibold">ZCHPC ERP</span>
              </div>
            )}
            {collapsed && <BarChart3 className="h-6 w-6 text-primary" />}
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className={cn("h-8 w-8", collapsed && "hidden")}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          {collapsed && (
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="absolute -right-4 top-9 h-8 w-8 rounded-full border bg-background shadow-md"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          )}
        </div>
        <div className="flex-1 overflow-auto py-2">
          <nav className="grid gap-1 px-2">
            {navItems.map(
              (item) =>
                checkPermission(item.permission) && (
                  <div key={item.path}>
                    <Button
                     variant={isActivePath(item.path) ? "secondary" : "ghost"}
                     className={cn(
                       "justify-start h-10 w-full transition-colors duration-200 hover:bg-muted rounded-md",
                       collapsed && "justify-center px-2",
                       isActivePath(item.path) && "bg-muted font-semibold"
                     )}
                      onClick={() => {
                        if (
                          (item.subItems && !collapsed) ||
                          item.title == "Dashboard"
                        ) {
                          toggleItemExpand(item.path);
                        } else {
                          handleNavigation(item.path);
                        }
                      }}
                    >
                      <item.icon
                        className={cn("h-4 w-4", !collapsed && "mr-2")}
                      />
                      {!collapsed && (
                        <>
                          <span className="flex-1 text-left">{item.title}</span>
                          {item.subItems &&
                            (expandedItems[item.path] ? (
                              <ChevronUp className="h-4 w-4 ml-2" />
                            ) : (
                              <ChevronDown className="h-4 w-4 ml-2" />
                            ))}
                        </>
                      )}
                    </Button>

                    {!collapsed &&
                      item.subItems &&
                      expandedItems[item.path] && (
                        <div className="ml-2 mt-1 mb-2 space-y-1">
                          {item.subItems.map(
                            (subItem) =>
                              checkPermission(subItem.permission) && (
                                <Button
                                  key={subItem.path}
                                  variant={
                                    isActivePath(subItem.path)
                                      ? "secondary"
                                      : "ghost"
                                  }
                                  className={cn(
                                    "justify-start h-8 w-full text-sm pl-8 transition-colors duration-200 hover:bg-muted rounded-md",
                                    isActivePath(subItem.path) &&
                                      "bg-muted font-medium"
                                  )}
                                  onClick={() => handleNavigation(subItem.path)}
                                >
                                  {subItem.title}
                                </Button>
                              )
                          )}
                        </div>
                      )}
                  </div>
                )
            )}
          </nav>
        </div>
        <div className="mt-auto border-t p-4">
          <div
            className={cn("flex items-center", collapsed && "justify-center")}
          >
            <Avatar className="h-8 w-8">
              <AvatarImage src={user?.avatar} alt={user?.name} />
              <AvatarFallback>{user?.name?.charAt(0) || "U"}</AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="ml-2">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.role}</p>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            className={cn(
              "mt-2 w-full justify-start text-muted-foreground",
              collapsed && "justify-center px-0"
            )}
            onClick={logout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            {!collapsed && <span>Logout</span>}
          </Button>
        </div>
      </aside>

      {/* Mobile Menu */}
      <div className="md:hidden flex items-center h-16 px-4 border-b bg-card w-full justify-between">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">ZCHPC ERP</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMobileMenuOpen(true)}
        >
          <Menu className="h-6 w-6" />
        </Button>
      </div>

      {/* Mobile Sidebar */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
          <div className="fixed inset-y-0 right-0 z-50 w-3/4 bg-card shadow-lg">
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-6 w-6 text-primary" />
                <span className="text-lg font-semibold">ZCHPC ERP</span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileMenuOpen(false)}
              >
                <X className="h-6 w-6" />
              </Button>
            </div>
            <nav className="grid gap-1 p-4">
              {navItems.map(
                (item) =>
                  checkPermission(item.permission) && (
                    <div key={item.path}>
                      <Button
                        variant={
                          isActivePath(item.path) ? "secondary" : "ghost"
                        }
                        className="justify-start h-10 w-full"
                        onClick={() => {
                          if (item.subItems) {
                            toggleItemExpand(item.path);
                          } else {
                            // handleNavigation(item.path);
                            navigate(`#${item.path}`);
                          }
                        }}
                      >
                        <item.icon className="h-4 w-4 mr-2" />
                        <span className="flex-1 text-left">{item.title}</span>
                        {item.subItems &&
                          (expandedItems[item.path] ? (
                            <ChevronUp className="h-4 w-4 ml-2" />
                          ) : (
                            <ChevronDown className="h-4 w-4 ml-2" />
                          ))}
                      </Button>

                      {item.subItems && expandedItems[item.path] && (
                        <div className="ml-6 mt-1 mb-2 space-y-1">
                          {item.subItems.map(
                            (subItem) =>
                              checkPermission(subItem.permission) && (
                                <Button
                                  key={subItem.path}
                                  variant={
                                    location.pathname === subItem.path
                                      ? "secondary"
                                      : "ghost"
                                  }
                                  className="justify-start h-8 w-full text-sm pl-4"
                                  onClick={() => handleNavigation(subItem.path)}
                                >
                                  {subItem.title}
                                </Button>
                              )
                          )}
                        </div>
                      )}
                    </div>
                  )
              )}
              <Separator className="my-2" />
              <div className="flex items-center p-2">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.avatar} alt={user?.name} />
                  <AvatarFallback>
                    {user?.name?.charAt(0) || "U"}
                  </AvatarFallback>
                </Avatar>
                <div className="ml-2">
                  <p className="text-sm font-medium">{user?.name}</p>
                  <p className="text-xs text-muted-foreground">{user?.role}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                className="w-full justify-start text-muted-foreground"
                onClick={logout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>Logout</span>
              </Button>
            </nav>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main
        className={cn(
          "flex-1 transition-all duration-300 ease-in-out",
          "md:ml-[240px]",
          collapsed && "md:ml-[70px]"
        )}
      >
        <div className="container py-6 md:py-8 px-2 md:px-8 max-w-8xl">
          {children}
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
