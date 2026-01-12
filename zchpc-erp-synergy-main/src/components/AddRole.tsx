import { useState } from "react";
import { toast } from "sonner";
import { X, ShieldCheck, CheckSquare, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { addRole } from "@/services/hr.services";

// Define the available top-level modules based on your navConfig
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

export default function AddRole({ setShowModal, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [roleData, setRoleData] = useState({
    name: "",
    display_name: "",
    permissions: [] as string[],
  });

  const togglePermission = (moduleId: string) => {
    setRoleData((prev) => ({
      ...prev,
      permissions: prev.permissions.includes(moduleId)
        ? prev.permissions.filter((p) => p !== moduleId)
        : [...prev.permissions, moduleId],
    }));
  };

  const handleNameChange = (val: string) => {
    setRoleData({
      ...roleData,
      display_name: val,
      // Auto-generate the slug name (e.g. "Senior Manager" -> "SENIOR_MANAGER")
      name: val.toUpperCase().replace(/\s+/g, "_"),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (roleData.permissions.length === 0) {
      toast.error("Please select at least one permission module");
      return;
    }

    setLoading(true);
    try {
      await addRole(roleData);
      toast.success("Role created successfully");
      onSuccess();
      setShowModal(false);
    } catch (error) {
      toast.error("Failed to create role. It may already exist.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b bg-slate-50 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800">
                Create System Role
              </h2>
              <p className="text-sm text-slate-500">
                Define access levels for modules
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowModal(false)}
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex-1 overflow-y-auto p-6 space-y-6"
        >
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="roleName">Role Display Name</Label>
              <Input
                id="roleName"
                placeholder="e.g. Junior Accountant"
                value={roleData.display_name}
                onChange={(e) => handleNameChange(e.target.value)}
                required
              />
              <p className="text-[10px] text-slate-400 font-mono">
                SYSTEM_ID: {roleData.name || "..."}
              </p>
            </div>

            <div className="space-y-3">
              <Label>Module Access (Permissions)</Label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {SYSTEM_MODULES.map((mod) => (
                  <div
                    key={mod.id}
                    onClick={() => togglePermission(mod.id)}
                    className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex items-start gap-3 ${
                      roleData.permissions.includes(mod.id)
                        ? "border-blue-600 bg-blue-50/50"
                        : "border-slate-100 hover:border-slate-200"
                    }`}
                  >
                    <div className="mt-1">
                      {roleData.permissions.includes(mod.id) ? (
                        <CheckSquare className="h-5 w-5 text-blue-600" />
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
                ))}
              </div>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="p-6 border-t bg-slate-50 flex justify-end gap-3">
          <Button
            variant="outline"
            type="button"
            onClick={() => setShowModal(false)}
          >
            Cancel
          </Button>
          <Button
            disabled={loading}
            type="submit"
            onClick={handleSubmit}
            className="bg-blue-600 hover:bg-blue-700 px-8"
          >
            {loading ? "Saving Role..." : "Create Role"}
          </Button>
        </div>
      </div>
    </div>
  );
}
