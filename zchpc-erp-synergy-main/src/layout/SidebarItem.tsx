import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import { SidebarItemConfig } from "./navConfig";
import { useAuth } from "@/contexts/AuthContext";

interface SidebarItemProps {
  item: SidebarItemConfig;
  collapsed: boolean;
  expandedItems: Record<string, boolean>;
  setExpandedItems: React.Dispatch<
    React.SetStateAction<Record<string, boolean>>
  >;
  level?: number;
  onNavigate?: () => void; // Optional: for mobile to close menu
}

export const SidebarItem: React.FC<SidebarItemProps> = ({
  item,
  collapsed,
  expandedItems,
  setExpandedItems,
  level = 0,
  onNavigate,
  ...props
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const {user} = useAuth()

  console.log(user);
  

  const isExpanded = expandedItems[item.path || ""] || false;
  const hasSubItems = !!item.subItems?.length;

  const isActive = location.pathname === item.path;

  const handleClick = () => {
    if (hasSubItems) {
      // If it's a parent, toggle expansion (if not collapsed)
      if (!collapsed) {
        setExpandedItems((prev) => ({
          ...prev,
          [item.path]: !prev[item.path],
        }));
      }
      // Optional: navigate to parent path if it's a valid route
      // if (item.path) navigate(item.path);
    } else if (item.path) {
      // If it's a child or simple item, just navigate
      navigate(item.path);
      if (onNavigate) onNavigate(); // Close mobile menu if open
    }
  };

 return (
    <div className="mb-0.5">
      <Button
        variant="ghost"
        className={cn(
          "w-full transition-all duration-200 justify-start h-10 px-3 rounded-lg",
          isActive 
            ? "bg-blue-50 text-blue-700 hover:bg-blue-100" 
            : "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
          collapsed && "justify-center px-0"
        )}
        onClick={handleClick}
      >
        {item.icon && (
          <item.icon className={cn(
            "h-[18px] w-[18px] shrink-0",
            isActive ? "text-blue-600" : "text-slate-400",
            !collapsed && "mr-3"
          )} />
        )}
        
        {!collapsed && (
          <span className="flex-1 text-left text-[13px] font-medium">
            {item.title}
          </span>
        )}

        {hasSubItems && !collapsed && (
          <ChevronDown className={cn(
            "h-3.5 w-3.5 transition-transform duration-200 text-slate-400",
            isExpanded && "rotate-180"
          )} />
        )}
      </Button>

      {/* Sub-items with a cleaner look */}
      {hasSubItems && isExpanded && !collapsed && (
        <div className="mt-1 ml-4 border-l-2 border-slate-100 pl-2 space-y-0.5">
          {item.subItems!.map((subItem) => (
          <SidebarItem
              key={subItem.path}
              item={subItem}
              collapsed={collapsed}
              expandedItems={expandedItems} // Explicitly pass these
              setExpandedItems={setExpandedItems}
              {...props} // Pass the rest
            />
          ))}
        </div>
      )}
    </div>
  );
};