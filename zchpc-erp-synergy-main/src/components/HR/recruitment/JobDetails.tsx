import React, { useEffect, useState } from "react";
import { Briefcase } from "lucide-react";

export type JobListing = {
  id: number;
  title: string;
  department: string;
  status: "Open" | "Closed";
  postedDate: string; // expected format: "YYYY-MM-DD"
  applicants: number;
  description: string;
  requirements: string;
  location: string;
  salaryRange: string;
};

type Props = {
  isOpen: boolean;
  job: JobListing | null;
  onClose: () => void;
  /**
   * onSave may return a Promise (e.g. to perform an API call).
   * If provided, the modal will await it and reflect saving/error states.
   */
  onSave?: (job: JobListing) => Promise<void> | void;
};

const JobDetailsModal: React.FC<Props> = ({ isOpen, job, onClose, onSave }) => {
  const [form, setForm] = useState<JobListing | null>(job);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm(job);
    setIsSaving(false);
    setSaveSuccess(false);
    setError(null);
  }, [job, isOpen]);

  if (!isOpen || !form) return null;

  const handleChange = (field: keyof JobListing, value: string | number) =>
    setForm((prev) => (prev ? { ...prev, [field]: value } : prev));

  const validate = (f: JobListing) => {
    if (!f.title.trim()) return "Title is required.";
    if (Number.isNaN(Number(f.applicants)) || Number(f.applicants) < 0)
      return "Applicants must be a non-negative number.";
    // validate postedDate basic format (YYYY-MM-DD)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(f.postedDate)) return "Posted Date must be YYYY-MM-DD.";
    return null;
  };

  const handleSave = async () => {
    if (!form) return;
    setError(null);
    const v = validate(form);
    if (v) {
      setError(v);
      return;
    }

    setIsSaving(true);
    try {
      if (onSave) await onSave(form);
      // success UI
      setIsSaving(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 1600);
    } catch (err) {
      console.error("Save failed", err);
      setError(
        err && typeof err === "object" && "message" in err
          ? String((err as any).message)
          : "Failed to save. Try again."
      );
      setIsSaving(false);
    }
  };

  // small helper for label + control
  const FieldRow: React.FC<{ label: string; control: React.ReactNode }> = ({ label, control }) => (
    <div className="grid grid-cols-3 gap-4 items-start py-2">
      <div className="col-span-1">
        <label className="text-sm font-medium text-gray-500">{label}</label>
      </div>
      <div className="col-span-2">{control}</div>
    </div>
  );

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl ring-1 ring-slate-100 overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-4 px-6 py-4 bg-gradient-to-r from-sky-600 to-indigo-600">
          <div className="flex items-center justify-center h-10 w-10 rounded-md bg-white/10">
            <Briefcase className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-white text-lg font-semibold leading-none">Job Details</h3>
            <p className="text-white/80 text-xs mt-0.5">View and edit the job information below</p>
          </div>

          <div className="flex-1" />

          {/* keep onClose available to call but no close icon in UI per request */}
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          <div className="bg-white rounded-lg border border-gray-50 p-4 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Left column */}
              <div>
                <FieldRow
                  label="Title"
                  control={
                    <input
                      value={form.title}
                      onChange={(e) => handleChange("title", e.target.value)}
                      className="w-full text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                      placeholder="Job title"
                    />
                  }
                />

                <FieldRow
                  label="Department"
                  control={
                    <input
                      value={form.department}
                      onChange={(e) => handleChange("department", e.target.value)}
                      className="w-full text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                      placeholder="Department"
                    />
                  }
                />

                <FieldRow
                  label="Status"
                  control={
                    <select
                      value={form.status}
                      onChange={(e) => handleChange("status", e.target.value as JobListing["status"])}
                      className="w-full text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                    >
                      <option value="Open">Open</option>
                      <option value="Closed">Closed</option>
                    </select>
                  }
                />

                {/* ---------- Posted Date: native date picker ---------- */}
                <FieldRow
                  label="Posted Date"
                  control={
                    // input type="date" displays a calendar control in most browsers
                    <input
                      type="date"
                      value={form.postedDate || ""}
                      onChange={(e) => {
                        // browser returns yyyy-mm-dd, which matches form.postedDate format
                        handleChange("postedDate", e.target.value);
                      }}
                      className="w-full text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                      placeholder="YYYY-MM-DD"
                    />
                  }
                />
              </div>

              {/* Right column */}
              <div>
                <FieldRow
                  label="Applicants"
                  control={
                    <input
                      type="number"
                      min={0}
                      value={String(form.applicants)}
                      onChange={(e) => handleChange("applicants", Number(e.target.value))}
                      className="w-36 text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                    />
                  }
                />

                <FieldRow
                  label="Location"
                  control={
                    <input
                      value={form.location}
                      onChange={(e) => handleChange("location", e.target.value)}
                      className="w-full text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                      placeholder="City / Region"
                    />
                  }
                />

                <FieldRow
                  label="Salary Range"
                  control={
                    <input
                      value={form.salaryRange}
                      onChange={(e) => handleChange("salaryRange", e.target.value)}
                      className="w-full text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                      placeholder="e.g. $40k - $60k"
                    />
                  }
                />
              </div>
            </div>

            {/* Description & Requirements */}
            <div className="mt-4 space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => handleChange("description", e.target.value)}
                  rows={4}
                  className="mt-2 w-full text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Requirements</label>
                <textarea
                  value={form.requirements}
                  onChange={(e) => handleChange("requirements", e.target.value)}
                  rows={4}
                  className="mt-2 w-full text-sm rounded-md border px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
                />
              </div>
            </div>

            {/* error / success */}
            <div className="mt-4">
              {error && <div className="text-sm text-red-600">{error}</div>}
              {saveSuccess && <div className="text-sm text-green-700">Saved ✓</div>}
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 flex items-center justify-end gap-3">
            {/* Save button (keeps same color design) */}
            <button
              onClick={handleSave}
              disabled={isSaving}
              className={`px-4 py-2 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-indigo-600 text-white hover:bg-indigo-700 ${
                isSaving ? "opacity-60 cursor-not-allowed" : ""
              }`}
            >
              {isSaving ? (
                <span className="inline-flex items-center gap-2">
                  <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  Saving...
                </span>
              ) : (
                "Save"
              )}
            </button>

            {/* Optional small neutral button to call onClose (useful for closing modal) */}
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-md border border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobDetailsModal;