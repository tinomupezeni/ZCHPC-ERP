import React, { useState, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  LogOut,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { navItems } from "./navConfig"; // 1. Moved nav items to a separate file
import { SidebarItem } from "./SidebarItem"; // 2. Created a sub-component for nav items

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>(
    {}
  );
  
  // 3. This is how you get the user data!
  const { user, logout, checkPermission } = useAuth();
  
  const location = useLocation();
  const navigate = useNavigate();

  const toggleSidebar = () => setCollapsed((prev) => !prev);
  const toggleMobileMenu = () => setMobileMenuOpen((prev) => !prev);

  // 4. This recursive function filters the nav list based on the user's role
  const filteredNavItems = useMemo(() => {
    const filterItems = (items: typeof navItems): typeof navItems => {
      return items
        .filter((item) => checkPermission(item.permission))
        .map((item) => ({
          ...item,
          subItems: item.subItems ? filterItems(item.subItems) : undefined,
        }));
    };
    return filterItems(navItems);
  }, [checkPermission]); // 'navItems' is constant, so checkPermission is the only dependency

  // 5. FIXED: Correctly access nested user data
  const userName = `${user?.first_name || ""} ${user?.last_name || ""}`;
  const userRole = user?.employee_profile?.role || "Staff";
  const userFallback = (user?.first_name?.[0] || "U") + (user?.last_name?.[0] || "");
  const userAvatarUrl = `https://api.dicebear.com/7.x/initials/svg?seed=${userName}`;

  return (
    <div className="flex min-h-screen bg-background">
      {/* --- Desktop Sidebar --- */}
      <aside
        className={cn(
          "fixed inset-y-0 z-20 flex h-full flex-col border-r bg-card transition-all duration-300 ease-in-out",
          collapsed ? "w-[70px]" : "w-[240px]",
          "hidden md:flex"
        )}
      >
        {/* Logo and Collapse Button */}
        <div className="flex h-16 items-center justify-between px-4">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-6 w-6 text-primary" />
              <span className="text-lg font-semibold">ZCHPC ERP</span>
            </div>
          )}
          {collapsed && <BarChart3 className="h-6 w-6 text-primary" />}
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
        
        {/* Navigation */}
        <div className="flex-1 overflow-auto py-2">
          <nav className="grid gap-1 px-2">
            {filteredNavItems.map((item) => (
              <SidebarItem
                key={item.path || item.title}
                item={item}
                collapsed={collapsed}
                expandedItems={expandedItems}
                setExpandedItems={setExpandedItems}
              />
            ))}
          </nav>
        </div>
        
        {/* User Profile & Logout */}
        <div className="mt-auto border-t p-4">
          <div className={cn("flex items-center", collapsed && "justify-center")}>
            <Avatar className="h-8 w-8">
              <AvatarImage src={userAvatarUrl} />
              <AvatarFallback>{userFallback}</AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="ml-2">
                <p className="text-sm font-medium">{userName}</p>
                <p className="text-xs text-muted-foreground">{userRole}</p>
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
            <LogOut className={cn("h-4 w-4", !collapsed && "mr-2")} />
            {!collapsed && <span>Logout</span>}
          </Button>
        </div>
      </aside>

      {/* --- Mobile Header & Menu --- */}
      <div className="md:hidden flex items-center h-16 px-4 border-b bg-card w-full justify-between sticky top-0 z-30">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">ZCHPC ERP</span>
        </div>
        <Button variant="ghost" size="icon" onClick={toggleMobileMenu}>
          <Menu className="h-6 w-6" />
        </Button>
      </div>
      
      {/* Mobile Sidebar (Overlay) */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 bg-background/80 backdrop-blur-sm" onClick={toggleMobileMenu}>
          <aside className="fixed inset-y-0 right-0 z-50 w-3/4 bg-card shadow-lg" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b">
              <span className="text-lg font-semibold">Menu</span>
              <Button variant="ghost" size="icon" onClick={toggleMobileMenu}>
                <X className="h-6 w-6" />
              </Button>
            </div>
            <nav className="grid gap-1 p-4">
              {filteredNavItems.map((item) => (
                 <SidebarItem
                    key={item.path || item.title}
                    item={item}
                    collapsed={false} // Always expanded on mobile
                    expandedItems={expandedItems}
                    setExpandedItems={setExpandedItems}
                    onNavigate={toggleMobileMenu} // Close menu on nav
                 />
              ))}
            </nav>
          </aside>
        </div>
      )}

      {/* --- Main Content Area --- */}
      <main
        className={cn(
          "flex-1 transition-all duration-300 ease-in-out",
          "md:ml-[240px]",
          collapsed && "md:ml-[70px]",
          "mt-16 md:mt-0" // Account for mobile header
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