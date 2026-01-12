import { useState, useEffect } from "react";
import { 
  X, Edit2, Save, Loader, User, Briefcase, DollarSign, 
  Phone, Calendar, Clock, MapPin, Building, CreditCard,
  ShieldCheck, AlertCircle
} from "lucide-react";
import { toast } from "sonner";
import { updateEmployee, getOneEmployee } from "@/services/employees.services";
import { getDepartment, getPositions } from "@/services/hr.services";
import { format, differenceInYears, differenceInMonths } from "date-fns";

export default function EmployeeDetailModal({ employee: initialEmployee, onClose, onUpdate }) {
  const [employee, setEmployee] = useState(initialEmployee); // Holds the full fresh data
  const [loading, setLoading] = useState(true); // Loading state for the fetch
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  // Dropdown Data for Editing
  const [departments, setDepartments] = useState([]);
  const [positions, setPositions] = useState([]);

  // Form Data
  const [formData, setFormData] = useState({});

  // 1. Fetch Full Details on Mount
  useEffect(() => {
    const fetchFullDetails = async () => {
      try {
        const data = await getOneEmployee(initialEmployee.id);
        console.log(data.data);
        
        setEmployee(data.data);
        setFormData(data.data);
        
        // Pre-load dropdowns if we might edit
        const depts = await getDepartment();
        setDepartments(depts);
      } catch (error) {
        toast.error("Could not load full employee details");
      } finally {
        setLoading(false);
      }
    };
    fetchFullDetails();
  }, [initialEmployee.id]);

  // 2. Handle Cascading Dropdowns
  useEffect(() => {
    if (isEditing && formData.department_id) {
       // If department is an ID (edit mode), fetch positions
       // Note: You might need logic here if your API returns department Name string initially
       // Ideally, your 'getOneEmployee' returns both 'department' (name) and 'department_id' (id)
       // If not, you have to rely on user re-selecting department to trigger this.
       if (!isNaN(formData.department_id)) {
          getPositions(formData.department_id).then(setPositions);
       }
    }
  }, [isEditing, formData.department_id]);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData({ 
        ...formData, 
        [name]: type === 'number' ? parseFloat(value) : value 
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Ensure we send IDs for relations
      // If user didn't change dropdowns, we might need to map names back to IDs
      // For now, assuming user re-selects if they want to change it.
      await updateEmployee(employee.id, formData);
      toast.success("Profile updated successfully");
      
      // Refresh local view
      const updated = await getOneEmployee(employee.id);
      setEmployee(updated);
      setFormData(updated);
      
      onUpdate(); // Refresh parent list
      setIsEditing(false);
    } catch (error) {
      console.error(error);
      toast.error("Update failed. Check your inputs.");
    } finally {
      setSaving(false);
    }
  };

  // --- Helper: Calculate Tenure ---
  const getTenure = () => {
    if (!employee.date_joined) return "New";
    const start = new Date(employee.date_joined);
    const now = new Date();
    const years = differenceInYears(now, start);
    const months = differenceInMonths(now, start) % 12;
    if (years > 0) return `${years}y ${months}m`;
    return `${months}m`;
  };

  // --- Helper: Render Field ---
  const Field = ({ icon: Icon, label, name, type = "text", options = null }) => {
    const value = formData[name];
    const displayValue = employee[name]; // Read-only value might be different (e.g. ID vs Name)

    return (
      <div className="group">
        <label className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase mb-1.5">
          {Icon && <Icon className="h-3 w-3" />} {label}
        </label>
        {isEditing ? (
          options ? (
            <select
              name={name}
              value={value || ""}
              onChange={handleChange}
              className="w-full p-2 bg-white border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            >
              <option value="">Select {label}</option>
              {options?.map(opt => (
                <option key={opt.value || opt.id} value={opt.value || opt.id}>
                  {opt.label || opt.name || opt.title}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={type}
              name={name}
              value={value || ""}
              onChange={handleChange}
              className="w-full p-2 bg-white border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          )
        ) : (
          <div className="text-sm font-medium text-gray-900 py-1 border-b border-transparent group-hover:border-gray-100 transition-colors">
            {displayValue || <span className="text-gray-400 italic">--</span>}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-[2px] transition-opacity" onClick={onClose} />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-3xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <>
            {/* --- 1. Modern Header --- */}
            <div className="relative bg-gradient-to-r from-slate-800 to-slate-900 text-white shrink-0 overflow-hidden">
              {/* Background Pattern */}
              <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]" />
              
              <div className="relative px-8 py-8">
                <div className="flex justify-between items-start">
                  <div className="flex gap-6 items-center">
                    {/* Avatar */}
                    <div className="h-20 w-20 rounded-2xl bg-white/10 border-2 border-white/20 flex items-center justify-center text-3xl font-bold shadow-inner backdrop-blur-md text-blue-200">
                      {employee.first_name?.[0]}{employee.surname?.[0]}
                    </div>
                    
                    {/* Name & Title */}
                    <div>
                      <h2 className="text-3xl font-bold tracking-tight">
                        {employee.first_name} {employee.surname}
                      </h2>
                      <div className="flex items-center gap-3 mt-2 text-blue-200/90">
                        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/10 text-sm">
                          <Briefcase className="h-3.5 w-3.5" /> {employee.position || "No Position"}
                        </span>
                        <span className="text-sm">•</span>
                        <span className="text-sm">{employee.department || "No Dept"}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    {!isEditing ? (
                      <button 
                        onClick={() => setIsEditing(true)}
                        className="p-2 hover:bg-white/10 rounded-lg transition-colors text-blue-200 hover:text-white"
                        title="Edit Profile"
                      >
                        <Edit2 className="h-5 w-5" />
                      </button>
                    ) : (
                      <div className="flex gap-2">
                        <button 
                          onClick={() => setIsEditing(false)}
                          className="px-3 py-1.5 text-sm bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
                        >
                          Cancel
                        </button>
                        <button 
                          onClick={handleSave}
                          disabled={saving}
                          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow-lg transition-all"
                        >
                          {saving ? <Loader className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                          Save
                        </button>
                      </div>
                    )}
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
                      <X className="h-6 w-6" />
                    </button>
                  </div>
                </div>

                {/* Stats Row */}
                <div className="flex gap-8 mt-8 pt-6 border-t border-white/10">
                  <div>
                    <p className="text-xs text-blue-300 uppercase font-semibold tracking-wider">Tenure</p>
                    <p className="text-lg font-medium mt-0.5 flex items-center gap-2">
                      <Clock className="h-4 w-4 text-blue-400" /> {getTenure()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-300 uppercase font-semibold tracking-wider">Status</p>
                    <div className="mt-1">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-sm font-medium ${
                        employee.is_active ? "bg-green-500/20 text-green-300 border border-green-500/30" : "bg-red-500/20 text-red-300"
                      }`}>
                        <div className={`h-1.5 w-1.5 rounded-full ${employee.is_active ? "bg-green-400" : "bg-red-400"}`} />
                        {employee.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-blue-300 uppercase font-semibold tracking-wider">Leave Balance</p>
                    <p className="text-lg font-medium mt-0.5">{employee.leave_days_entitled || 0} Days</p>
                  </div>
                </div>
              </div>
            </div>

            {/* --- 2. Navigation Tabs --- */}
            <div className="flex border-b border-gray-200 px-6 sticky top-0 bg-white z-10">
              {['overview', 'personal', 'job', 'financial'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-4 text-sm font-medium border-b-2 transition-colors capitalize ${
                    activeTab === tab
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* --- 3. Scrollable Content --- */}
            <div className="flex-1 overflow-y-auto p-8 bg-gray-50/50">
              <div className="max-w-2xl mx-auto space-y-8">
                
                {/* SECTION: OVERVIEW / PERSONAL */}
                {(activeTab === 'overview' || activeTab === 'personal') && (
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-6 animate-in fade-in slide-in-from-bottom-4">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2 border-b pb-3">
                      <User className="h-5 w-5 text-blue-500" /> Personal Details
                    </h3>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                      <Field label="First Name" name="first_name" />
                      <Field label="Surname" name="surname" />
                      <Field label="Email" name="email" type="email" />
                      <Field label="Phone" name="phone" icon={Phone} />
                      <Field label="National ID" name="national_id" icon={ShieldCheck} />
                      <Field label="Date of Birth" name="date_of_birth" type="date" icon={Calendar} />
                      <Field 
                        label="Gender" 
                        name="gender" 
                        options={[{value:'Male'}, {value:'Female'}]} 
                      />
                      <Field 
                        label="Marital Status" 
                        name="marital_status" 
                        options={[{value:'Single'}, {value:'Married'}, {value:'Divorced'}]} 
                      />
                    </div>

                    {/* Emergency Contact Sub-section */}
                    <div className="mt-6 pt-6 border-t border-dashed">
                      <h4 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 text-orange-500" /> Emergency Contact
                      </h4>
                      <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                        <Field label="Contact Name" name="emergency_contact_name" />
                        <Field label="Relationship" name="emergency_contact_relationship" />
                        <Field label="Phone" name="emergency_contact_number" />
                      </div>
                    </div>
                  </div>
                )}

                {/* SECTION: JOB / EMPLOYMENT */}
                {(activeTab === 'overview' || activeTab === 'job') && (
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-6 animate-in fade-in slide-in-from-bottom-4 delay-100">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2 border-b pb-3">
                      <Briefcase className="h-5 w-5 text-blue-500" /> Employment Information
                    </h3>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                      {/* For Edit Mode: We need to pass options for Dept & Pos */}
                      {/* In View Mode: It shows the string value */}
                      <Field 
                        label="Department" 
                        name={isEditing ? "department_id" : "department"}
                        icon={Building}
                        options={departments} // Pass loaded departments
                      />
                      <Field 
                        label="Position" 
                        name={isEditing ? "position_id" : "position"}
                        icon={MapPin}
                        options={positions} // Pass loaded positions
                      />
                      <Field 
                        label="Type" 
                        name="employee_type" 
                        options={[{value:'Full-time'}, {value:'Part-time'}, {value:'Contract'}]}
                      />
                      <Field label="Date Joined" name="date_joined" type="date" icon={Calendar} />
                      <Field label="Contract Start" name="contract_from" type="date" />
                      <Field label="Contract End" name="contract_to" type="date" />
                    </div>
                  </div>
                )}

                {/* SECTION: FINANCIAL */}
                {(activeTab === 'overview' || activeTab === 'financial') && (
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-6 animate-in fade-in slide-in-from-bottom-4 delay-200">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2 border-b pb-3">
                      <DollarSign className="h-5 w-5 text-green-600" /> Financial & Statutory
                    </h3>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                      <div className="p-3 bg-green-50 border border-green-100 rounded-lg">
                        <Field label="Salary (USD)" name="usd_salary" type="number" />
                      </div>
                      <div className="p-3 bg-yellow-50 border border-yellow-100 rounded-lg">
                        <Field label="Salary (ZiG)" name="zig_salary" type="number" />
                      </div>
                      <Field label="Bank Name" name="bank_name" icon={Building} />
                      <Field label="Account Number" name="bank_account" icon={CreditCard} />
                      <Field label="NSSA Number" name="nssa_number" />
                      <Field label="Tax Number" name="zimra_tax_number" />
                    </div>

                    {/* Active Deductions List (Read Only View) */}
                    {!isEditing && employee.deductions && employee.deductions.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-xs font-bold uppercase text-gray-500 mb-2">Active Deductions</h4>
                        <div className="flex flex-wrap gap-2">
                          {employee.deductions.map((d, i) => (
                            <span key={i} className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full border border-gray-200">
                              {d.name}: ${d.amount}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}