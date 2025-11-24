import React, { useEffect, useState } from "react";
import { Briefcase } from "lucide-react";

// Define the frontend interface (camelCase)
export type JobListing = {
  id: number;
  title: string;
  department: string;
  status: "Open" | "Closed";
  postedDate: string; 
  applicants: number;
  description: string;
  requirements: string;
  location: string;
  salaryRange: string;
};

type Props = {
  isOpen: boolean;
  job: any; // Accept 'any' initially to handle backend data shape variations
  onClose: () => void;
  onSave?: (job: JobListing) => Promise<void> | void;
};

const JobDetailsModal: React.FC<Props> = ({ isOpen, job, onClose, onSave }) => {
  // Initialize with default empty state to prevent null errors
  const [form, setForm] = useState<JobListing>({
    id: 0,
    title: "",
    department: "",
    status: "Open",
    postedDate: "",
    applicants: 0,
    description: "",
    requirements: "",
    location: "",
    salaryRange: "",
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && job) {
      // MAP BACKEND FIELDS TO FRONTEND STATE
      // This handles both snake_case (backend) and camelCase (frontend) inputs
      setForm({
        id: job.id,
        title: job.title || "",
        department: job.department || "", // Or job.department_name if nested
        status: job.status || "Open",
        // Handle date format. Take YYYY-MM-DD part if ISO string
        postedDate: (job.postedDate || job.posted_date || "").split('T')[0], 
        applicants: job.applicants || job.applicants_count || 0,
        description: job.description || "",
        // Handle requirements array or string
        requirements: Array.isArray(job.requirements) 
            ? job.requirements.join('\n') 
            : (job.requirements || job.qualifications?.join('\n') || ""), 
        location: job.location || "",
        salaryRange: job.salaryRange || job.salary_range || "",
      });
      
      setIsSaving(false);
      setSaveSuccess(false);
      setError(null);
    }
  }, [job, isOpen]);

  if (!isOpen) return null;

  const handleChange = (field: keyof JobListing, value: string | number) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const validate = (f: JobListing) => {
    if (!f.title.trim()) return "Title is required.";
    if (Number.isNaN(Number(f.applicants)) || Number(f.applicants) < 0)
      return "Applicants must be a non-negative number.";
    return null;
  };

  const handleSave = async () => {
    setError(null);
    const v = validate(form);
    if (v) {
      setError(v);
      return;
    }

    setIsSaving(true);
    try {
      if (onSave) await onSave(form);
      setIsSaving(false);
      setSaveSuccess(true);
      setTimeout(() => {
          setSaveSuccess(false);
          onClose(); // Optional: Close on success
      }, 1000);
    } catch (err) {
      console.error("Save failed", err);
      setError("Failed to save. Try again.");
      setIsSaving(false);
    }
  };

  // Helper for Rows
  const FieldRow: React.FC<{ label: string; control: React.ReactNode }> = ({ label, control }) => (
    <div className="grid grid-cols-3 gap-4 items-start py-3 border-b border-gray-50 last:border-0">
      <div className="col-span-1 pt-2">
        <label className="text-sm font-medium text-gray-500">{label}</label>
      </div>
      <div className="col-span-2">{control}</div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-white rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
        
        {/* Header */}
        <div className="flex items-center gap-4 px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white shrink-0">
          <div className="p-2 bg-white/10 rounded-lg">
            <Briefcase className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold">Job Details</h3>
            <p className="text-blue-100 text-xs">Edit job information</p>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="px-8 py-6 overflow-y-auto flex-1">
          <div className="space-y-1">
            <FieldRow
              label="Job Title"
              control={
                <input
                  value={form.title}
                  onChange={(e) => handleChange("title", e.target.value)}
                  className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="e.g. Senior Developer"
                />
              }
            />

            <FieldRow
              label="Department"
              control={
                <input
                  value={form.department}
                  onChange={(e) => handleChange("department", e.target.value)}
                  className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="e.g. Engineering"
                />
              }
            />

            <div className="grid grid-cols-2 gap-4">
                <FieldRow
                label="Status"
                control={
                    <select
                    value={form.status}
                    onChange={(e) => handleChange("status", e.target.value as any)}
                    className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                    >
                    <option value="Open">Open</option>
                    <option value="Closed">Closed</option>
                    </select>
                }
                />
                <FieldRow
                label="Posted Date"
                control={
                    <input
                    type="date"
                    value={form.postedDate}
                    onChange={(e) => handleChange("postedDate", e.target.value)}
                    className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                }
                />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <FieldRow
                label="Location"
                control={
                    <input
                    value={form.location}
                    onChange={(e) => handleChange("location", e.target.value)}
                    className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="e.g. New York, Remote"
                    />
                }
                />
                <FieldRow
                label="Applicants"
                control={
                    <input
                    type="number"
                    min={0}
                    value={form.applicants}
                    onChange={(e) => handleChange("applicants", parseInt(e.target.value) || 0)}
                    className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                }
                />
            </div>

            <FieldRow
              label="Salary Range"
              control={
                <input
                  value={form.salaryRange}
                  onChange={(e) => handleChange("salaryRange", e.target.value)}
                  className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="e.g. $50k - $80k"
                />
              }
            />

            <div className="pt-4">
                <label className="block text-sm font-medium text-gray-500 mb-2">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => handleChange("description", e.target.value)}
                  rows={4}
                  className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                  placeholder="Job description..."
                />
            </div>

            <div className="pt-2">
                <label className="block text-sm font-medium text-gray-500 mb-2">Requirements</label>
                <textarea
                  value={form.requirements}
                  onChange={(e) => handleChange("requirements", e.target.value)}
                  rows={4}
                  className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                  placeholder="List requirements here..."
                />
            </div>
          </div>

          {/* Feedback Messages */}
          <div className="mt-4 h-6">
            {error && <p className="text-sm text-red-600 font-medium animate-pulse">{error}</p>}
            {saveSuccess && <p className="text-sm text-green-600 font-medium">Saved Successfully! ✓</p>}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className={`px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors shadow-sm flex items-center gap-2 ${
              isSaving ? "opacity-70 cursor-wait" : ""
            }`}
          >
            {isSaving ? "Saving..." : "Save Changes"}
          </button>
        </div>

      </div>
    </div>
  );
};

export default JobDetailsModal;