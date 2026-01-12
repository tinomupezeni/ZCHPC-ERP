import { useState, useEffect } from "react";
import { toast } from "sonner";
import { X, ShieldCheck, CheckSquare, Square, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { updateRole } from "@/services/hr.services"; // You'll need to add this to hr.services

const SYSTEM_MODULES = [
  {
    id: "DASHBOARD",
    label: "Dashboard",
    description: "Access to system overview and analytics",
  },
  {
    id: "HR",
    label: "Human Resources",
    description: "Manage employees, recruitment, and attendance",
  },
  {
    id: "PAYROLL",
    label: "Payroll",
    description: "Process salaries, deductions, and tax tables",
  },
  {
    id: "ACCOUNTING",
    label: "Accounting",
    description: "General ledger and financial reporting",
  },
  {
    id: "PROCUREMENT",
    label: "Procurement",
    description: "Purchase orders and supplier management",
  },
  {
    id: "INVENTORY",
    label: "Inventory",
    description: "Stock management and movements",
  },
  {
    id: "SALES",
    label: "Sales",
    description: "Sales orders and customer tracking",
  },
  {
    id: "SETTINGS",
    label: "System Settings",
    description: "Manage users, roles, and global config",
  },
];

export default function EditPermissionsModal({ role, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);

  useEffect(() => {
    if (role && role.permissions) {
      setSelectedPermissions(role.permissions);
    }
  }, [role]);

  const togglePermission = (moduleId: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(moduleId)
        ? prev.filter((p) => p !== moduleId)
        : [...prev, moduleId]
    );
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // magic happens here: updating the JSONField in Postgres
      await updateRole(role.id, { permissions: selectedPermissions });
      toast.success(`Permissions updated for ${role.display_name}`);
      onSuccess();
      onClose();
    } catch (error) {
      toast.error("Failed to update permissions");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="p-6 border-b bg-slate-50 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-amber-500 p-2 rounded-lg text-white">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800">
                Edit Permissions
              </h2>
              <p className="text-sm text-slate-500">
                Role: {role.display_name}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {SYSTEM_MODULES.map((mod) => {
              const isActive = selectedPermissions.includes(mod.id);
              return (
                <div
                  key={mod.id}
                  onClick={() => togglePermission(mod.id)}
                  className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex items-start gap-3 ${
                    isActive
                      ? "border-amber-500 bg-amber-50/50"
                      : "border-slate-100 hover:border-slate-200"
                  }`}
                >
                  <div className="mt-1">
                    {isActive ? (
                      <CheckSquare className="h-5 w-5 text-amber-600" />
                    ) : (
                      <Square className="h-5 w-5 text-slate-300" />
                    )}
                  </div>
                  <div>
                    <p className="font-bold text-sm text-slate-800">
                      {mod.label}
                    </p>
                    <p className="text-xs text-slate-500 leading-tight mt-0.5">
                      {mod.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="p-6 border-t bg-slate-50 flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            disabled={loading}
            onClick={handleSave}
            className="bg-amber-600 hover:bg-amber-700"
          >
            <Save className="mr-2 h-4 w-4" />
            {loading ? "Saving Changes..." : "Save Permissions"}
          </Button>
        </div>
      </div>
    </div>
  );
}
