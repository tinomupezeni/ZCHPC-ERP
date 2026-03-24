import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Plus, X, Check, Copy, ShieldCheck, UserCircle } from "lucide-react";
import {
  getDepartment,
  addDepartment,
  getRoles,
  addRole,
  addUser,
} from "@/services/hr.services";

export default function AddUser({ setShowModal, onSuccess }) {
  const [step, setStep] = useState(1); // 1: Form, 2: Confirm, 3: Credentials
  const [employee, setEmployee] = useState({
    first_name: "",
    last_name: "",
    role: "",
    email: "",
    department: "",
    password: "",
  });
  const [createdCredentials, setCreatedCredentials] = useState(null);

  // Data lists
  const [departments, setDepartments] = useState([]);
  const [dbRoles, setDbRoles] = useState([]);
  const [loading, setLoading] = useState(false);

  // Inline Add states
  const [isAddingDept, setIsAddingDept] = useState(false);
  const [newDeptName, setNewDeptName] = useState("");
  const [isAddingRole, setIsAddingRole] = useState(false);
  const [newRoleName, setNewRoleName] = useState("");

  const fetchInitialData = async () => {
    try {
      const [deptRes, roleRes] = await Promise.all([
        getDepartment(),
        getRoles(),
      ]);
      setDepartments(deptRes.data);
      setDbRoles(roleRes); // Assuming role service returns .data already based on previous service update
    } catch (err) {
      toast.error("Failed to load system data");
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleQuickAddDept = async () => {
    if (!newDeptName.trim()) return;
    try {
      const res = await addDepartment({ name: newDeptName });
      setDepartments([...departments, res.data]);
      setEmployee({ ...employee, department: res.data.id });
      setNewDeptName("");
      setIsAddingDept(false);
      toast.success("Department created");
    } catch (err) {
      toast.error("Department already exists");
    }
  };

  const handleQuickAddRole = async () => {
    if (!newRoleName.trim()) return;
    try {
      const res = await addRole({
        name: newRoleName.toUpperCase().replace(/\s+/g, "_"),
        display_name: newRoleName,
      });
      setDbRoles([...dbRoles, res]);
      setEmployee({ ...employee, role: res.id });
      setNewRoleName("");
      setIsAddingRole(false);
      toast.success("Role created");
    } catch (err) {
      toast.error("Failed to create role");
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await addUser(employee);
      setCreatedCredentials(response.data);
      setStep(3);
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.email?.[0] || "Registration failed");
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  const getDeptName = () =>
    departments.find((d) => String(d.id) === String(employee.department))?.name;
  const getRoleName = () =>
    dbRoles.find((r) => String(r.id) === String(employee.role))?.display_name;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden border border-slate-200">
        {/* Step 1: Entry Form */}
        {step === 1 && (
          <>
            <div className="p-6 border-b bg-slate-50 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-slate-800">
                  New System User
                </h2>
                <p className="text-sm text-slate-500">
                  Step 1: Enter basic information
                </p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X />
              </button>
            </div>
            <form
              className="p-6 space-y-5"
              onSubmit={(e) => {
                e.preventDefault();
                setStep(2);
              }}
            >
              <div className="grid grid-cols-2 gap-4">
                <input
                  placeholder="First Name"
                  value={employee.first_name}
                  onChange={(e) =>
                    setEmployee({ ...employee, first_name: e.target.value })
                  }
                  required
                  className="p-2.5 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  placeholder="Surname"
                  value={employee.last_name}
                  onChange={(e) =>
                    setEmployee({ ...employee, last_name: e.target.value })
                  }
                  required
                  className="p-2.5 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Role Section */}
                <div className="space-y-1">
                  <div className="flex justify-between items-center">
                    <label className="text-[12px] font-bold text-slate-400 uppercase">
                      Role
                    </label>
                    {!isAddingRole && (
                      <button
                        type="button"
                        onClick={() => setIsAddingRole(true)}
                        className="text-[12px] text-blue-600 font-bold hover:underline"
                      >
                        Add New
                      </button>
                    )}
                  </div>
                  {isAddingRole ? (
                    <div className="flex gap-1">
                      <input
                        autoFocus
                        placeholder="Role Name"
                        value={newRoleName}
                        onChange={(e) => setNewRoleName(e.target.value)}
                        className="flex-1 p-2 text-sm border border-blue-300 rounded-lg outline-none"
                      />
                      <button
                        type="button"
                        onClick={handleQuickAddRole}
                        className="p-1.5 bg-blue-600 text-white rounded-lg"
                      >
                        <Check className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsAddingRole(false)}
                        className="p-1.5 bg-slate-100 text-slate-400 rounded-lg"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <select
                      value={employee.role}
                      onChange={(e) =>
                        setEmployee({ ...employee, role: e.target.value })
                      }
                      required
                      className="w-full p-2.5 border rounded-lg text-sm"
                    >
                      <option value="">Select Role</option>
                      {dbRoles?.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.display_name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {/* Dept Section */}
                <div className="space-y-1">
                  <div className="flex justify-between items-center">
                    <label className="text-[12px] font-bold text-slate-400 uppercase">
                      Department
                    </label>
                    {!isAddingDept && (
                      <button
                        type="button"
                        onClick={() => setIsAddingDept(true)}
                        className="text-[12px] text-blue-600 font-bold hover:underline"
                      >
                        Add New
                      </button>
                    )}
                  </div>
                  {isAddingDept ? (
                    <div className="flex gap-1">
                      <input
                        autoFocus
                        placeholder="Dept Name"
                        value={newDeptName}
                        onChange={(e) => setNewDeptName(e.target.value)}
                        className="flex-1 p-2 text-sm border border-blue-300 rounded-lg outline-none"
                      />
                      <button
                        type="button"
                        onClick={handleQuickAddDept}
                        className="p-1.5 bg-blue-600 text-white rounded-lg"
                      >
                        <Check className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsAddingDept(false)}
                        className="p-1.5 bg-slate-100 text-slate-400 rounded-lg"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <select
                      value={employee.department}
                      onChange={(e) =>
                        setEmployee({ ...employee, department: e.target.value })
                      }
                      required
                      className="w-full p-2.5 border rounded-lg text-sm"
                    >
                      <option value="">Select Dept</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              <input
                placeholder="Work Email"
                type="email"
                value={employee.email}
                onChange={(e) =>
                  setEmployee({ ...employee, email: e.target.value })
                }
                required
                className="w-full p-2.5 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
              />

              <div className="space-y-1">
                <label className="text-[12px] font-bold text-slate-400 uppercase">
                  Password
                </label>
                <input
                  placeholder="Enter password (min 8 characters)"
                  type="password"
                  value={employee.password}
                  onChange={(e) =>
                    setEmployee({ ...employee, password: e.target.value })
                  }
                  required
                  minLength={8}
                  className="w-full p-2.5 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-slate-400">
                  This will be the user's login password
                </p>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  type="submit"
                  className="px-8 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-all"
                >
                  Continue to Summary
                </button>
              </div>
            </form>
          </>
        )}

        {/* Step 2: Confirmation Summary */}
        {step === 2 && (
          <div className="p-8 space-y-6">
            <div className="text-center">
              <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <UserCircle className="h-10 w-10 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-slate-800">
                Review Details
              </h2>
              <p className="text-slate-500 text-sm">
                Verify information before system activation
              </p>
            </div>

            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100 space-y-4">
              <div className="flex justify-between border-b pb-2">
                <span className="text-slate-500 text-sm">Full Name</span>
                <span className="font-semibold text-slate-800">
                  {employee.first_name} {employee.last_name}
                </span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-slate-500 text-sm">Role</span>
                <span className="font-semibold text-blue-600 uppercase text-sm tracking-wider">
                  {getRoleName()}
                </span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-slate-500 text-sm">Department</span>
                <span className="font-semibold text-slate-800">
                  {getDeptName()}
                </span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-slate-500 text-sm">Email</span>
                <span className="font-semibold text-slate-800">
                  {employee.email}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 text-sm">Password</span>
                <span className="font-semibold text-slate-800">
                  {"•".repeat(employee.password.length || 8)}
                </span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="flex-1 py-3 border border-slate-200 rounded-xl font-bold text-slate-600 hover:bg-slate-50"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex-1 py-3 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 shadow-lg shadow-green-100 transition-all"
              >
                {loading ? "Processing..." : "Confirm & Create"}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Credentials Display */}
        {step === 3 && createdCredentials && (
          <div className="p-8 space-y-6 text-center animate-in fade-in zoom-in duration-300">
            <div className="h-20 w-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <ShieldCheck className="h-12 w-12 text-green-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-800">
                Account Created
              </h2>
              <p className="text-slate-500 mt-1 text-sm">
                Provide these credentials to the employee
              </p>
            </div>

            <div className="space-y-3">
              <div className="p-4 bg-slate-900 rounded-xl text-left">
                <label className="text-[12px] text-slate-500 font-bold uppercase tracking-widest">
                  Login Email
                </label>
                <div className="flex justify-between items-center mt-1">
                  <code className="text-blue-400 font-mono text-sm">
                    {createdCredentials.email}
                  </code>
                  <button
                    onClick={() => handleCopy(createdCredentials.email)}
                    className="text-slate-400 hover:text-white"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div className="p-4 bg-slate-900 rounded-xl text-left">
                <label className="text-[12px] text-slate-500 font-bold uppercase tracking-widest">
                  Password
                </label>
                <div className="flex justify-between items-center mt-1">
                  <code className="text-green-400 font-mono text-sm">
                    {employee.password || createdCredentials.password}
                  </code>
                  <button
                    onClick={() => handleCopy(employee.password || createdCredentials.password)}
                    className="text-slate-400 hover:text-white"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowModal(false)}
              className="w-full py-4 bg-slate-800 text-white rounded-xl font-bold hover:bg-slate-900 transition-all"
            >
              Done & Return
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
