import React, { useState, useMemo } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import { navItems } from "./navConfig";
import { SidebarItem } from "./SidebarItem";
import { LogOut, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export const MainLayout: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, checkPermission, isLoading } = useAuth();
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>(
    {}
  );

  const filteredNavItems = useMemo(() => {
    // If loading, show nothing (or we will show the skeleton below)
    if (isLoading || !user) return [];

    const filterItems = (items: typeof navItems): typeof navItems => {
      return items
        .filter((item) => checkPermission(item.permission))
        .map((item) => ({
          ...item,
          subItems: item.subItems ? filterItems(item.subItems) : undefined,
        }));
    };
    return filterItems(navItems);
  }, [user, isLoading, checkPermission]); // Dependency on 'user' is key for refresh fix

  console.log(user);
  

  const userName = `${user?.first_name || ""} ${user?.last_name || ""}`;
  const userRole = user?.employee_profile?.role || "Staff";
  const userFallback =
    (user?.first_name?.[0] || "U") + (user?.last_name?.[0] || "");

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <aside
        className={cn(
          "fixed inset-y-0 z-20 flex h-full flex-col border-r bg-white transition-all",
          collapsed ? "w-[70px]" : "w-[260px]"
        )}
      >
        <div className="flex h-16 items-center px-6 border-b">
          <BarChart3 className="h-6 w-6 text-blue-600 mr-2" />
          {!collapsed && (
            <span className="font-bold text-slate-900">ZCHPC ERP</span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto py-6 px-3">
          <nav className="space-y-1">
            {isLoading ? (
              <div className="space-y-3 p-2 animate-pulse">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-9 bg-slate-100 rounded-md w-full" />
                ))}
              </div>
            ) : (
              filteredNavItems.map((item) => (
                <SidebarItem
                  key={item.path}
                  item={item}
                  collapsed={collapsed}
                  expandedItems={expandedItems}
                  setExpandedItems={setExpandedItems}
                />
              ))
            )}
          </nav>
        </div>

        <div className="mt-auto border-t p-4 bg-slate-50/50">
          <div className="flex items-center px-2">
            <Avatar className="h-8 w-8">
              <AvatarImage
                src={`https://api.dicebear.com/7.x/initials/svg?seed=${userName}`}
              />
              <AvatarFallback>{userFallback}</AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="ml-3 overflow-hidden">
                <p className="text-xs font-bold text-slate-900 truncate">
                  {userName}
                </p>
                <p className="text-[10px] text-slate-500 uppercase">
                  {userRole}
                </p>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            onClick={logout}
            className="mt-2 w-full justify-start text-slate-400 hover:text-red-600"
          >
            <LogOut className="h-4 w-4 mr-2" />
            {!collapsed && <span className="text-xs font-bold">Logout</span>}
          </Button>
        </div>
      </aside>

      <main
        className={cn(
          "flex-1 transition-all",
          !collapsed ? "ml-[260px]" : "ml-[70px]"
        )}
      >
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
};
