import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import { SidebarItemConfig } from "./navConfig";

interface SidebarItemProps {
  item: SidebarItemConfig;
  collapsed: boolean;
  expandedItems: Record<string, boolean>;
  setExpandedItems: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
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
}) => {
  const navigate = useNavigate();
  const location = useLocation();

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
    <div style={{ paddingLeft: `${level * 16}px` }}>
      <Button
        variant={isActive ? "secondary" : "ghost"}
        className={cn(
          "justify-start w-full transition-colors duration-200 hover:bg-muted rounded-md",
          level === 0 ? "h-10" : "h-8 text-sm",
          isActive && "font-semibold"
        )}
        onClick={handleClick}
      >
        {item.icon && (
          <item.icon className={cn("h-4 w-4", !collapsed && "mr-2")} />
        )}
        {!collapsed && <span className="flex-1 text-left">{item.title}</span>}
        {hasSubItems && !collapsed && (
          isExpanded ? (
            <ChevronUp className="h-4 w-4 ml-2" />
          ) : (
            <ChevronDown className="h-4 w-4 ml-2" />
          )
        )}
      </Button>

      {/* Render Sub-items */}
      {hasSubItems && isExpanded && !collapsed && (
        <div className="mt-1 space-y-1">
          {item.subItems!.map((subItem) => (
            <SidebarItem
              key={subItem.path}
              item={subItem}
              collapsed={collapsed}
              expandedItems={expandedItems}
              setExpandedItems={setExpandedItems}
              level={level + 1}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}
    </div>
  );
};