import React from "react";
import {
  X,
  Edit2,
  Save,
  Loader,
  User,
  Briefcase,
  DollarSign,
  Phone,
  Calendar,
  Clock,
  MapPin,
  Building,
  CreditCard,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";
import { differenceInYears, differenceInMonths } from "date-fns";
import { useEmployeeDetail } from "@/hooks/useEmployeeDetail";
import { FieldProps } from "@/types/employee";

export default function EmployeeDetailModal({
  employee: initialEmployee,
  onClose,
  onUpdate,
}) {
  const {
    employee,
    formData,
    loading,
    isEditing,
    setIsEditing,
    saving,
    activeTab,
    setActiveTab,
    departments,
    positions,
    handleChange,
    handleSave,
  } = useEmployeeDetail(initialEmployee, onUpdate);

  const getTenure = () => {
    if (!employee.date_joined) return "New";
    const start = new Date(employee.date_joined);
    const now = new Date();
    const years = differenceInYears(now, start);
    const months = differenceInMonths(now, start) % 12;
    return years > 0 ? `${years}y ${months}m` : `${months}m`;
  };

  // Internal Field Component to access hook state via closure
  const Field: React.FC<FieldProps> = ({
    icon: Icon,
    label,
    name,
    type = "text",
    options = null,
  }) => {
    const value = formData[name];
    const displayValue = employee[name];

    const safeOptions = Array.isArray(options) ? options : [];

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
              className="w-full p-2 bg-white border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="">Select {label}</option>
              {safeOptions.map((opt: any) => (
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
              className="w-full p-2 bg-white border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 outline-none"
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
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-[2px]"
        onClick={onClose}
      />

      <div className="relative w-full max-w-3xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="relative bg-gradient-to-r from-slate-800 to-slate-900 text-white p-8">
              <div className="flex justify-between items-start">
                <div className="flex gap-6 items-center">
                  <div className="h-20 w-20 rounded-2xl bg-white/10 border-2 border-white/20 flex items-center justify-center text-3xl font-bold text-blue-200">
                    {employee.first_name?.[0]}
                    {employee.surname?.[0]}
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold tracking-tight">
                      {employee.first_name} {employee.surname}
                    </h2>
                    <div className="flex items-center gap-3 mt-2 text-blue-200/90">
                      <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/10 text-sm">
                        <Briefcase className="h-3.5 w-3.5" />{" "}
                        {employee.position || "No Position"}
                      </span>
                      <span className="text-sm">•</span>
                      <span className="text-sm">
                        {employee.department || "No Dept"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  {!isEditing ? (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="p-2 hover:bg-white/10 rounded-lg text-blue-200 hover:text-white"
                    >
                      <Edit2 className="h-5 w-5" />
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => setIsEditing(false)}
                        className="px-3 py-1.5 text-sm bg-white/10 hover:bg-white/20 rounded-lg"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow-lg"
                      >
                        {saving ? (
                          <Loader className="h-4 w-4 animate-spin" />
                        ) : (
                          <Save className="h-4 w-4" />
                        )}{" "}
                        Save
                      </button>
                    </>
                  )}
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
              </div>

              {/* Stats Row */}
              <div className="flex gap-8 mt-8 pt-6 border-t border-white/10">
                <StatItem label="Tenure" value={getTenure()} icon={Clock} />
                <div>
                  <p className="text-xs text-blue-300 uppercase font-semibold">
                    Status
                  </p>
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 mt-1 rounded-full text-sm font-medium ${
                      employee.is_active
                        ? "bg-green-500/20 text-green-300"
                        : "bg-red-500/20 text-red-300"
                    }`}
                  >
                    <div
                      className={`h-1.5 w-1.5 rounded-full ${
                        employee.is_active ? "bg-green-400" : "bg-red-400"
                      }`}
                    />
                    {employee.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <StatItem
                  label="Leave Balance"
                  value={`${employee.leave_days_entitled || 0} Days`}
                />
              </div>
            </div>

            {/* Tabs Navigation */}
            <div className="flex border-b border-gray-200 px-6 sticky top-0 bg-white z-10">
              {["overview", "personal", "job", "financial"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-4 text-sm font-medium border-b-2 transition-colors capitalize ${
                    activeTab === tab
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-8 bg-gray-50/50">
              <div className="max-w-2xl mx-auto space-y-8">
                {(activeTab === "overview" || activeTab === "personal") && (
                  <Section title="Personal Details" icon={User}>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                      <Field label="First Name" name="first_name" />
                      <Field label="Surname" name="surname" />
                      <Field label="Email" name="email" type="email" />
                      <Field label="Phone" name="phone" icon={Phone} />
                      <Field
                        label="National ID"
                        name="national_id"
                        icon={ShieldCheck}
                      />
                      <Field
                        label="Date of Birth"
                        name="date_of_birth"
                        type="date"
                        icon={Calendar}
                      />
                      <Field
                        label="Gender"
                        name="gender"
                        options={[{ value: "Male" }, { value: "Female" }]}
                      />
                      <Field
                        label="Marital Status"
                        name="marital_status"
                        options={[
                          { value: "Single" },
                          { value: "Married" },
                          { value: "Divorced" },
                        ]}
                      />
                    </div>
                  </Section>
                )}

                {(activeTab === "overview" || activeTab === "job") && (
                  <Section title="Employment Information" icon={Briefcase}>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                      <Field
                        label="Department"
                        name={isEditing ? "department_id" : "department"}
                        icon={Building}
                        options={departments}
                      />
                      <Field
                        label="Position"
                        name={isEditing ? "position_id" : "position"}
                        icon={MapPin}
                        options={positions}
                      />
                      <Field
                        label="Type"
                        name="employee_type"
                        options={[
                          { value: "Full-time" },
                          { value: "Part-time" },
                          { value: "Contract" },
                        ]}
                      />
                      <Field
                        label="Date Joined"
                        name="date_joined"
                        type="date"
                        icon={Calendar}
                      />
                    </div>
                  </Section>
                )}

                {(activeTab === "overview" || activeTab === "financial") && (
                  <Section
                    title="Financial & Statutory"
                    icon={DollarSign}
                    color="text-green-600"
                  >
                    <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                      <div className="p-3 bg-green-50 border border-green-100 rounded-lg">
                        <Field
                          label="Salary (USD)"
                          name="usd_salary"
                          type="number"
                        />
                      </div>
                      <div className="p-3 bg-yellow-50 border border-yellow-100 rounded-lg">
                        <Field
                          label="Salary (ZiG)"
                          name="zig_salary"
                          type="number"
                        />
                      </div>
                      <Field
                        label="Bank Name"
                        name="bank_name"
                        icon={Building}
                      />
                      <Field
                        label="Account Number"
                        name="bank_account"
                        icon={CreditCard}
                      />
                    </div>
                  </Section>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Small Layout Helpers
const StatItem = ({ label, value, icon: Icon }: any) => (
  <div>
    <p className="text-xs text-blue-300 uppercase font-semibold tracking-wider">
      {label}
    </p>
    <p className="text-lg font-medium mt-0.5 flex items-center gap-2">
      {Icon && <Icon className="h-4 w-4 text-blue-400" />} {value}
    </p>
  </div>
);

const Section = ({
  title,
  icon: Icon,
  children,
  color = "text-blue-500",
}: any) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-6 animate-in fade-in slide-in-from-bottom-4">
    <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2 border-b pb-3">
      <Icon className={`h-5 w-5 ${color}`} /> {title}
    </h3>
    {children}
  </div>
);
