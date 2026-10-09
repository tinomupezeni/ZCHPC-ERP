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
  // Backend permission modules (the part of a permission before the first
  // dot, e.g. "payroll" for "payroll.run.process"); the item shows when the
  // user holds any permission in one of them. "admin" means the full "*" grant.
  permission: string[];
  moduleIdentifier?: string; // Link to backend system module
  subItems?: SidebarItemConfig[];
}



export const navItems: SidebarItemConfig[] = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    path: "/dashboard",
    permission: ["admin"],
  },
  {
    title: "HR",
    icon: Users,
    path: "/hr",
    permission: ["hr"],
    moduleIdentifier: "hr",
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
    permission: ["payroll"],
    moduleIdentifier: "payroll",
    subItems: [
      {
        title: "Process Payroll",
        path: "/payroll",
        permission: ["payroll"],
      },
      {
        title: "Salary Setup",
        path: "/payroll/salary-setup",
        permission: ["payroll"],
      },
      {
        title: "Deductions",
        path: "/payroll/deductions",
        permission: ["payroll"],
      },
      {
        title: "Tax Tables",
        path: "/payroll/tax-tables",
        permission: ["payroll"],
      },
      {
        title: "Currencies",
        path: "/payroll/currencies",
        permission: ["payroll"],
      },
      {
        title: "Payroll Period",
        path: "/payroll/payroll-period",
        permission: ["payroll"],
      },
      // {
      //   title: "Process Payroll",
      //   path: "/payroll/process-payroll",
      //   permission: ["payroll"],
      // },
      // {
      //   title: "Payslips",
      //   path: "/payroll/payslips",
      //   permission: ["payroll"],
      // },
      {
        title: "Compliance Reports",
        path: "/payroll/reports",
        permission: ["payroll"],
      },
    ],
  },
  {
    title: "Sales",
    icon: ShoppingCart,
    path: "/sales",
    permission: ["sales"],
    moduleIdentifier: "sales",
  },
  {
    title: "Accounting",
    icon: DollarSign,
    path: "/accounting",
    permission: ["accounts"],
    moduleIdentifier: "accounts",
    subItems: [
      {
        title: "General Ledger",
        path: "/accounting/accounting-general-ledger",
        permission: ["accounts"],
      },
      {
        title: "Payroll Process",
        path: "/accounting/accounting-payroll",
        permission: ["accounts"],
      },
      {
        title: "Currencies",
        path: "/accounting/accounting-currencies",
        permission: ["accounts"],
      },
      {
        title: "Accounts Payable",
        path: "/accounting/accounting-payable",
        permission: ["accounts"],
      },
      {
        title: "Accounts Receivable",
        path: "/accounting/accounting-receivable",
        permission: ["accounts"],
      },
      {
        title: "Financial Reports",
        path: "/accounting/accounting-reports",
        permission: ["accounts"],
      },
      {
        title: "Tax Management",
        path: "/accounting/accounting-tax",
        permission: ["accounts"],
      },
    ],
  },
  {
    title: "Procurement",
    icon: FileText,
    path: "/procurement",
    permission: ["procurement"],
    moduleIdentifier: "procurement",
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
    permission: ["inventory"],
    moduleIdentifier: "inventory",
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
  {
    title: "App Store",
    icon: Package,
    path: "/modules",
    permission: ["admin"],
  },
];
