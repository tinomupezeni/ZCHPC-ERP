import React, { useState, useMemo, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import { navItems, NAV_SECTIONS } from "./navConfig";
import { SidebarItem } from "./SidebarItem";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { getActiveModules, SystemModule } from "@/services/system.services";

export const MainLayout: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, checkPermission, isLoading } = useAuth();
  const [activeModules, setActiveModules] = useState<string[]>([]);
  const [isModulesLoading, setIsModulesLoading] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>(
    {}
  );

  useEffect(() => {
    const fetchActiveModules = async () => {
      try {
        const modules = await getActiveModules();
        setActiveModules(modules.map((m: SystemModule) => m.identifier));
      } catch (error) {
        console.error("Failed to fetch active modules", error);
      } finally {
        setIsModulesLoading(false);
      }
    };
    fetchActiveModules();
  }, []);

  const filteredNavItems = useMemo(() => {
    // If loading, show nothing (or we will show the skeleton below)
    if (isLoading || isModulesLoading || !user) return [];

    const filterItems = (items: typeof navItems): typeof navItems => {
      return items
        .filter((item) => {
          // Check role permission
          if (!checkPermission(item.permission)) return false;

          // Check if module is active (if it's a modular item)
          if (item.moduleIdentifier && !activeModules.includes(item.moduleIdentifier)) {
            return false;
          }

          return true;
        })
        .map((item) => ({
          ...item,
          subItems: item.subItems ? filterItems(item.subItems) : undefined,
        }));
    };
    return filterItems(navItems);
  }, [user, isLoading, isModulesLoading, activeModules, checkPermission]); // Dependency on 'user' is key for refresh fix

  // Group visible top-level items into labeled sections (design refresh
  // 2026-09-29). Sections are fixed-order; empty ones (permission/module
  // filtered) are skipped. Sub-items keep their parent's group.
  const groupedNavItems = NAV_SECTIONS.map((section) => ({
    section,
    items: filteredNavItems.filter((item) => (item.section ?? "System") === section),
  })).filter((group) => group.items.length > 0);

  const userName = `${user?.first_name || ""} ${user?.last_name || ""}`;
  // Get role display name - check multiple sources
  const userRole = user?.employee_profile?.role_display_name
    || user?.employee_profile?.role
    || user?.role
    || "Staff";
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
        <div className="flex h-16 items-center px-4 border-b">
          <img src="/logo.png" alt="ZCHPC ERP" className="h-10 w-auto" />
          {!collapsed && (
            <span className="font-bold text-slate-900 ml-2">ZCHPC ERP</span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto py-6 px-3">
          <nav className="space-y-1" aria-label="Primary">
            {isLoading ? (
              <div className="space-y-3 p-2 animate-pulse">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-9 bg-slate-100 rounded-md w-full" />
                ))}
              </div>
            ) : (
              groupedNavItems.map((group) => (
                <div key={group.section}>
                  {!collapsed && (
                    <p className="px-3 pt-4 pb-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider first:pt-0">
                      {group.section}
                    </p>
                  )}
                  {group.items.map((item) => (
                    <SidebarItem
                      key={item.path}
                      item={item}
                      collapsed={collapsed}
                      expandedItems={expandedItems}
                      setExpandedItems={setExpandedItems}
                    />
                  ))}
                </div>
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
