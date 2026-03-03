import {
  LayoutDashboard,
  Users,
  CreditCard,
  DollarSign,
  Package,
  FileText,
  ShoppingCart,
  Settings,
} from "lucide-react";

export interface SidebarItemConfig {
  title: string;
  icon: React.ElementType;
  path: string;
  permission: string[]; // A list of roles that can see this
  subItems?: SidebarItemConfig[];
}



export const navItems: SidebarItemConfig[] = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    path: "/dashboard",
    permission: ["admin"], // Now an array
  },
  {
    title: "HR",
    icon: Users,
    path: "/hr",
    permission: ["hr", "admin"], // Now an array
    subItems: [
      { title: "Employees", path: "/hr/hr-employees", permission: ["hr"] },
      {
        title: "Attendance",
        path: "/hr/hr-attendance",
        permission: ["hr"],
      },
      {
        title: "Recruitment",
        path: "/hr/hr-recruitment",
        permission: ["hr"],
      },
      //  {
      //     title: "Performance Management",
      //     path: "/hr-performance",
      //     permission: ["hr"],
      //   },
      {
        title: "Training & Development",
        path: "/hr/hr-training",
        permission: ["hr"],
        subItems: [
          {
            title: "Programs",
            path: "/hr/hr-training-programs",
            permission: ["hr"],
          },
          {
            title: "Sessions",
            path: "/hr/hr-training-sessions",
            permission: ["hr"],
          },
          {
            title: "Enrollments",
            path: "/hr/hr-training-enrollments",
            permission: ["hr"],
          },
          {
            title: "Certifications",
            path: "/hr/hr-training-certifications",
            permission: ["hr"],
          },
        ],
      },
      {
        title: "Reports",
        path: "/hr/hr-reports",
        permission: ["hr"],
      },
      {
        title: "Company Calendar",
        path: "/hr/hr-calendar",
        permission: ["hr"],
      },
      {
        title: "Leave Applications",
        path: "/hr/hr-leave",
        permission: ["hr"],
      },
    ],
  },
  {
    title: "Payroll",
    icon: CreditCard,
    path: "/payroll",
    permission: ["hr", "accountant", "admin"], // Now an array with both permissions
    subItems: [
      {
        title: "Process Payroll",
        path: "/payroll",
        permission: ["hr", "accountant"],
      },
      {
        title: "Salary Setup",
        path: "/payroll/salary-setup",
        permission: ["hr", "accountant"],
      },
      {
        title: "Deductions",
        path: "/payroll/deductions",
        permission: ["hr", "accountant"],
      },
      {
        title: "Tax Tables",
        path: "/payroll/tax-tables",
        permission: ["hr", "accountant"],
      },
      {
        title: "Currencies",
        path: "/payroll/currencies",
        permission: ["hr", "accountant"],
      },
      {
        title: "Payroll Period",
        path: "/payroll/payroll-period",
        permission: ["hr", "accountant"],
      },
      // {
      //   title: "Process Payroll",
      //   path: "/payroll/process-payroll",
      //   permission: ["hr", "accountant"],
      // },
      // {
      //   title: "Payslips",
      //   path: "/payroll/payslips",
      //   permission: ["hr", "accountant"],
      // },
      {
        title: "Compliance Reports",
        path: "/payroll/reports",
        permission: ["hr", "accountant"],
      },
    ],
  },
  {
    title: "Sales",
    icon: ShoppingCart,
    path: "/sales",
    permission: ["sales", "admin"],
  },
  {
    title: "Accounting",
    icon: DollarSign,
    path: "/accounting",
    permission: ["accountant", "admin"],
    subItems: [
      {
        title: "General Ledger",
        path: "/accounting/accounting-general-ledger",
        permission: ["accountant"],
      },
      {
        title: "Payroll Process",
        path: "/accounting/accounting-payroll",
        permission: ["accountant"],
      },
      {
        title: "Currencies",
        path: "/accounting/accounting-currencies",
        permission: ["accountant"],
      },
      {
        title: "Accounts Payable",
        path: "/accounting/accounting-payable",
        permission: ["accountant"],
      },
      {
        title: "Accounts Receivable",
        path: "/accounting/accounting-receivable",
        permission: ["accountant"],
      },
      {
        title: "Financial Reports",
        path: "/accounting/accounting-reports",
        permission: ["accountant"],
      },
      {
        title: "Tax Management",
        path: "/accounting/accounting-tax",
        permission: ["accountant"],
      },
    ],
  },
  {
    title: "Procurement",
    icon: FileText,
    path: "/procurement",
    permission: ["procurement", "admin"],
    subItems: [
      {
        title: "Orders",
        path: "/procurement/purchase-orders",
        permission: ["procurement"],
      },
      {
        title: "Suppliers",
        path: "/procurement/suppliers",
        permission: ["procurement"],
      },
      {
        title: "Purchase Requests",
        path: "/procurement/purchase-requests",
        permission: ["procurement"],
      },
      {
        title: "Budget Centers",
        path: "/procurement/budget-centers",
        permission: ["procurement"],
      },
      {
        title: "Deliveries",
        path: "/procurement/deliveries",
        permission: ["procurement"],
      },
      {
        title: "Reports",
        path: "/procurement/reports",
        permission: ["procurement"],
      },
    ],
  },
  {
    title: "Inventory",
    icon: Package,
    path: "/inventory",
    permission: ["inventory", "admin"],
    subItems: [
      { title: "Stock", path: "/inventory/stock", permission: ["inventory"] },
      {
        title: "Categories",
        path: "/inventory/categories",
        permission: ["inventory"],
      },
      {
        title: "Movements",
        path: "/inventory/movements",
        permission: ["inventory"],
      },
    ],
  },
  {
    title: "Settings",
    icon: Settings,
    path: "/settings",
    permission: ["admin"],
  },
];
