import React, { useEffect, useState } from "react";
import {
  X,
  Trash2,
  Building,
  MapPin,
  DollarSign,
  Mail,
  FileText,
  Target,
  GraduationCap,
  Plus,
  Loader,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import {
  getDepartment,
  getPositions,
  addDepartMethod,
  addPosition,
} from "@/server/hr.services";
import { createJob, updateJob } from "@/server/jobs.services";

// Define the shape of the form data
export type JobListing = {
  id?: number;
  title: string; // Derived from Position Title
  department_id: string | number; // ID for backend
  position_id: string | number; // ID for local logic
  status: string;
  postedDate: string;
  description: string;
  qualifications: string[];
  applicationProcess: string;
  location: string;
  salaryRange: string;
  contactEmail: string;
  responsibilities: string[];
  notes?: string;
};

type Props = {
  isOpen: boolean;
  job: JobListing | null;
  onClose: () => void;
  onSave: (updated: JobListing) => void;
};

const STATUS_OPTIONS = ["Open", "Closed", "Draft", "Pending"];

const PostJobModal: React.FC<Props> = ({ isOpen, job, onClose, onSave }) => {
  const [formData, setFormData] = useState<JobListing | null>(null);
  const [loading, setLoading] = useState(false);

  // Data Sources
  const [departments, setDepartments] = useState<
    { id: number; name: string }[]
  >([]);
  const [positions, setPositions] = useState<{ id: number; title: string }[]>(
    []
  );

  // Inline Add States
  const [isAddingDept, setIsAddingDept] = useState(false);
  const [newDeptName, setNewDeptName] = useState("");
  const [isAddingPos, setIsAddingPos] = useState(false);
  const [newPosTitle, setNewPosTitle] = useState("");
  const [miniLoading, setMiniLoading] = useState(false);

  // 1. Initialize & Fetch Departments
  useEffect(() => {
    if (isOpen) {
      getDepartment()
        .then((res) => setDepartments(res.data))
        .catch(console.error);

      if (job) {
        setFormData({
          ...job,
          // Ensure arrays exist
          responsibilities: job.responsibilities?.length
            ? job.responsibilities
            : [""],
          qualifications: job.qualifications?.length
            ? job.qualifications
            : [""],
        });
        // If editing, we might need to load positions immediately if dept is set
        if (job.department_id) {
          getPositions(job.department_id).then(setPositions);
        }
      } else {
        setFormData({
          title: "",
          department_id: "",
          position_id: "",
          status: "Open",
          postedDate: new Date().toISOString().split("T")[0],
          description: "",
          qualifications: [""],
          applicationProcess: "",
          location: "Harare",
          salaryRange: "",
          contactEmail: "hroffice@zchpc.ac.zw",
          responsibilities: [""],
        });
      }
    }
  }, [isOpen, job]);

  // 2. Cascading: Fetch Positions when Department Changes
  useEffect(() => {
    if (formData?.department_id) {
      getPositions(formData.department_id)
        .then(setPositions)
        .catch(() => setPositions([]));
    } else {
      setPositions([]);
    }
  }, [formData?.department_id]);

  if (!isOpen || !formData) return null;

  const handleChange = (field: keyof JobListing, value: any) => {
    setFormData((prev) => (prev ? { ...prev, [field]: value } : null));
  };

  // --- List Handlers (Responsibilities/Qualifications) ---
  const handleListChange = (
    field: "responsibilities" | "qualifications",
    index: number,
    value: string
  ) => {
    setFormData((prev) => {
      if (!prev) return null;
      const list = [...prev[field]];
      list[index] = value;
      return { ...prev, [field]: list };
    });
  };

  const addListItem = (field: "responsibilities" | "qualifications") => {
    setFormData((prev) =>
      prev ? { ...prev, [field]: [...prev[field], ""] } : null
    );
  };

  const removeListItem = (
    field: "responsibilities" | "qualifications",
    index: number
  ) => {
    setFormData((prev) => {
      if (!prev) return null;
      const list = prev[field].filter((_, i) => i !== index);
      return { ...prev, [field]: list.length ? list : [""] };
    });
  };

  // --- Inline Creation Handlers ---
  const handleCreateDept = async () => {
    if (!newDeptName.trim()) return;
    setMiniLoading(true);
    try {
      const newDept = await addDepartMethod({ name: newDeptName });
      setDepartments([...departments, newDept]);
      handleChange("department_id", newDept.id);
      toast.success("Department added");
      setIsAddingDept(false);
      setNewDeptName("");
    } catch (e) {
      toast.error("Failed to add department");
    } finally {
      setMiniLoading(false);
    }
  };

  const handleCreatePos = async () => {
    if (!newPosTitle.trim() || !formData.department_id) return;
    setMiniLoading(true);
    try {
      const newPos = await addPosition({
        title: newPosTitle,
        department_id: formData.department_id,
      });
      setPositions([...positions, newPos]);
      handleChange("position_id", newPos.id);
      // Auto-set the Job Title to match Position
      handleChange("title", newPos.title);
      toast.success("Position added");
      setIsAddingPos(false);
      setNewPosTitle("");
    } catch (e) {
      toast.error("Failed to add position");
    } finally {
      setMiniLoading(false);
    }
  };

  // --- Submit ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Find the selected position object to get the title string
      const selectedPos = positions.find((p) => p.id == formData.position_id);
      const jobTitle = selectedPos ? selectedPos.title : formData.title;

      const cleanData = {
        ...formData,
        title: jobTitle, // Use Position Title as Job Title
        department_id: formData.department_id || formData.department,
        responsibilities: formData.responsibilities.filter((r) => r.trim()),
        qualifications: formData.qualifications.filter((q) => q.trim()),
      };

      // Mock call - replace with actual API call
      // await addJob(cleanData);

      if (job?.id) {
        // Update existing
        await updateJob(job.id, cleanData);
      } else {
        // Create new
        await createJob(cleanData);
      }
      toast.success(job ? "Job updated" : "Job posted successfully");
      onClose();
    } catch (error) {
      toast.error("Failed to save job");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="relative w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center bg-blue-600 text-white z-10">
          <div>
            <h2 className="text-xl font-bold">
              {job ? "Edit Job Posting" : "Create New Job"}
            </h2>
            <p className="text-sm text-blue-100">
              {job
                ? "Update details for this role"
                : "Fill in details to publish a new role"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-blue-500 rounded-full text-blue-100 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
          <form id="jobForm" onSubmit={handleSubmit} className="space-y-6">
            {/* Section: Position & Dept (Cascading + Inline Add) */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
              <div className="flex items-center gap-2 text-blue-600 font-medium border-b pb-2">
                <Building className="h-4 w-4" /> Role Details
              </div>

              <div className="grid grid-cols-1 gap-4">
                {/* Department Dropdown */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Department
                  </label>
                  {isAddingDept ? (
                    <div className="flex gap-2">
                      <input
                        autoFocus
                        value={newDeptName}
                        onChange={(e) => setNewDeptName(e.target.value)}
                        placeholder="New Department..."
                        className="flex-1 p-2 border rounded-lg bg-blue-50 border-blue-300"
                      />
                      <button
                        type="button"
                        onClick={handleCreateDept}
                        className="p-2 bg-green-600 text-white rounded-lg"
                      >
                        {miniLoading ? (
                          <Loader className="h-4 w-4 animate-spin" />
                        ) : (
                          <Check className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsAddingDept(false)}
                        className="p-2 bg-gray-200 rounded-lg"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <select
                        required
                        value={formData.department_id}
                        onChange={(e) =>
                          handleChange("department_id", e.target.value)
                        }
                        className="flex-1 p-2 border rounded-lg bg-white focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select Department</option>
                        {departments.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.name}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => setIsAddingDept(true)}
                        className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg border"
                      >
                        <Plus className="h-4 w-4 text-gray-600" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Position Dropdown */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Position (Job Title)
                  </label>
                  {isAddingPos ? (
                    <div className="flex gap-2">
                      <input
                        autoFocus
                        value={newPosTitle}
                        onChange={(e) => setNewPosTitle(e.target.value)}
                        placeholder="New Position..."
                        className="flex-1 p-2 border rounded-lg bg-blue-50 border-blue-300"
                      />
                      <button
                        type="button"
                        onClick={handleCreatePos}
                        className="p-2 bg-green-600 text-white rounded-lg"
                      >
                        {miniLoading ? (
                          <Loader className="h-4 w-4 animate-spin" />
                        ) : (
                          <Check className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsAddingPos(false)}
                        className="p-2 bg-gray-200 rounded-lg"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <select
                        required
                        value={formData.position_id}
                        onChange={(e) => {
                          handleChange("position_id", e.target.value);
                          // Auto-fill Title for display
                          const p = positions.find(
                            (pos) => pos.id == e.target.value
                          );
                          if (p) handleChange("title", p.title);
                        }}
                        disabled={!formData.department_id}
                        className="flex-1 p-2 border rounded-lg bg-white focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                      >
                        <option value="">Select Position</option>
                        {positions.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.title}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => setIsAddingPos(true)}
                        disabled={!formData.department_id}
                        className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg border disabled:opacity-50"
                      >
                        <Plus className="h-4 w-4 text-gray-600" />
                      </button>
                    </div>
                  )}
                  {!formData.department_id && (
                    <p className="text-xs text-gray-500 mt-1">
                      Select a department first
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <select
                      value={formData.status}
                      onChange={(e) => handleChange("status", e.target.value)}
                      className="w-full p-2 border rounded-lg bg-white focus:ring-2 focus:ring-blue-500"
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Posted Date
                    </label>
                    <input
                      type="date"
                      value={formData.postedDate}
                      onChange={(e) =>
                        handleChange("postedDate", e.target.value)
                      }
                      className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Location
                    </label>
                    <div className="relative">
                      <MapPin className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        value={formData.location}
                        onChange={(e) =>
                          handleChange("location", e.target.value)
                        }
                        className="w-full pl-9 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Salary Range
                    </label>
                    <div className="relative">
                      <DollarSign className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        value={formData.salaryRange}
                        onChange={(e) =>
                          handleChange("salaryRange", e.target.value)
                        }
                        className="w-full pl-9 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g. $2k - $3k"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Section: Responsibilities */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="flex items-center gap-2 text-orange-600 font-medium">
                  <Target className="h-4 w-4" /> Key Responsibilities
                </div>
                <button
                  type="button"
                  onClick={() => addListItem("responsibilities")}
                  className="text-xs flex items-center gap-1 text-blue-600 hover:underline"
                >
                  <Plus className="h-3 w-3" /> Add Item
                </button>
              </div>
              <div className="space-y-2">
                {formData.responsibilities.map((resp, idx) => (
                  <div key={idx} className="flex gap-2">
                    <span className="text-gray-400 pt-2 text-xs">
                      {idx + 1}.
                    </span>
                    <textarea
                      rows={2}
                      value={resp}
                      onChange={(e) =>
                        handleListChange(
                          "responsibilities",
                          idx,
                          e.target.value
                        )
                      }
                      className="flex-1 p-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Describe a key duty..."
                    />
                    <button
                      type="button"
                      onClick={() => removeListItem("responsibilities", idx)}
                      className="text-gray-400 hover:text-red-500 pt-2"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Section: Qualifications */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="flex items-center gap-2 text-purple-600 font-medium">
                  <GraduationCap className="h-4 w-4" /> Qualifications
                </div>
                <button
                  type="button"
                  onClick={() => addListItem("qualifications")}
                  className="text-xs flex items-center gap-1 text-blue-600 hover:underline"
                >
                  <Plus className="h-3 w-3" /> Add Item
                </button>
              </div>
              <div className="space-y-2">
                {formData.qualifications.map((qual, idx) => (
                  <div key={idx} className="flex gap-2 items-center">
                    <div className="h-1.5 w-1.5 rounded-full bg-purple-400 shrink-0" />
                    <input
                      type="text"
                      value={qual}
                      onChange={(e) =>
                        handleListChange("qualifications", idx, e.target.value)
                      }
                      className="flex-1 p-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. Bachelor's Degree..."
                    />
                    <button
                      type="button"
                      onClick={() => removeListItem("qualifications", idx)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Section: Application */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
              <div className="flex items-center gap-2 text-cyan-600 font-medium border-b pb-2">
                <Mail className="h-4 w-4" /> Application Details
              </div>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contact Email
                  </label>
                  <input
                    type="email"
                    value={formData.contactEmail}
                    onChange={(e) =>
                      handleChange("contactEmail", e.target.value)
                    }
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Instructions
                  </label>
                  <textarea
                    rows={3}
                    value={formData.applicationProcess}
                    onChange={(e) =>
                      handleChange("applicationProcess", e.target.value)
                    }
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="How should candidates apply?"
                  />
                </div>
              </div>
            </div>
          </form>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t bg-white flex justify-end gap-3 sticky bottom-0">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-700 font-medium hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="jobForm"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-md transition-all flex items-center gap-2 disabled:opacity-70"
          >
            {loading && <Loader className="h-4 w-4 animate-spin" />}
            {job ? "Update Listing" : "Publish Job"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PostJobModal;
