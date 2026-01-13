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
  ShieldCheck,
  Users,
} from "lucide-react";

import { PostJobModalProps } from "@/types/postJob";
import { usePostJob } from "@/hooks/usePostJob";
import { Input } from "@/components/ui/input";

const STATUS_OPTIONS = ["Open", "Closed", "Draft", "Pending"];

const PostJobModal: React.FC<PostJobModalProps> = ({
  isOpen,
  job,
  onClose,
  onSave,
}) => {
  const {
    formData,
    loading,
    departments,
    positions,
    miniLoading,
    isAddingDept,
    setIsAddingDept,
    newDeptName,
    setNewDeptName,
    isAddingPos,
    setIsAddingPos,
    newPosTitle,
    setNewPosTitle,
    handleChange,
    handleListChange,
    handleCreateDept,
    handleCreatePos,
    handleSubmit,
    addListItem,
    removeListItem,
  } = usePostJob(isOpen, job, onClose);

  // Enhanced add item handler that ensures the array exists
  const handleAddItem = (field: keyof typeof formData) => {
    if (!formData) return;

    const currentList = (formData[field] as string[]) || [];
    const updatedList = [...currentList, ""];

    handleChange(field, updatedList);
  };

  // Enhanced remove item handler
  const handleRemoveItem = (field: keyof typeof formData, index: number) => {
    if (!formData) return;

    const currentList = (formData[field] as string[]) || [];
    const updatedList = currentList.filter((_, i) => i !== index);

    handleChange(field, updatedList);
  };

  // Enhanced list change handler
  const handleLocalListChange = (
    field: keyof typeof formData,
    index: number,
    value: string
  ) => {
    if (!formData) return;

    const currentList = (formData[field] as string[]) || [];
    const updatedList = [...currentList];
    updatedList[index] = value;

    handleChange(field, updatedList);
  };

  if (!isOpen) return null;

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
                        className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
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
                        className="p-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <select
                        required
                        value={formData?.department_id || ""}
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
                        className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg border transition-colors"
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
                        className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
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
                        className="p-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <select
                        required
                        value={formData?.position_id || ""}
                        onChange={(e) => {
                          handleChange("position_id", e.target.value);
                          // Auto-fill Title for display
                          const p = positions.find(
                            (pos) => pos.id == e.target.value
                          );
                          if (p) handleChange("title", p.title);
                        }}
                        disabled={!formData?.department_id}
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
                        disabled={!formData?.department_id}
                        className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg border disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <Plus className="h-4 w-4 text-gray-600" />
                      </button>
                    </div>
                  )}
                  {!formData?.department_id && (
                    <p className="text-xs text-gray-500 mt-1">
                      Select a department first
                    </p>
                  )}
                </div>

                {/* Internal Staff Toggle - FIXED */}
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-gray-600" />
                    <span className="text-sm font-medium text-gray-700">
                      Internal Staff Only
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleChange("isInternal", !formData?.isInternal);
                    }}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      formData?.isInternal ? "bg-blue-600" : "bg-gray-300"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        formData?.isInternal ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                  <span className="text-sm text-gray-500">
                    {formData?.isInternal
                      ? "Visible only to internal staff"
                      : "Public posting"}
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-700">
                  Reports To
                </span>
                <Input
                  label="Reports To"
                  value={formData?.reportsTo || ""}
                  onChange={(v) => handleChange("reportsTo", v)}
                  placeholder="e.g.  Director"
                />

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <select
                      value={formData?.status || "Open"}
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
                      Closing Date
                    </label>
                    <input
                      type="date"
                      value={formData?.postedDate || ""}
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
                        value={formData?.location || ""}
                        onChange={(e) =>
                          handleChange("location", e.target.value)
                        }
                        className="w-full pl-9 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g. Harare, Zimbabwe"
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
                        value={formData?.salaryRange || ""}
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

            {/* Section: Competencies - FIXED */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="flex items-center gap-2 text-green-600 font-medium">
                  <ShieldCheck className="h-4 w-4" /> Competencies
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleAddItem("competencies");
                  }}
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1 hover:text-blue-700 transition-colors"
                >
                  <Plus className="h-3 w-3" /> Add Item
                </button>
              </div>
              <div className="space-y-2">
                {formData?.competencies?.map((item, idx) => (
                  <div key={idx} className="flex gap-2 items-start">
                    <input
                      type="text"
                      value={item}
                      onChange={(e) =>
                        handleLocalListChange(
                          "competencies",
                          idx,
                          e.target.value
                        )
                      }
                      className="flex-1 p-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. Excellent communication skills"
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleRemoveItem("competencies", idx);
                      }}
                      className="text-gray-400 hover:text-red-500 pt-2 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                {(!formData?.competencies ||
                  formData.competencies.length === 0) && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No competencies added yet. Click "Add Item" to start.
                  </p>
                )}
              </div>
            </div>

            {/* Section: Responsibilities - FIXED */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="flex items-center gap-2 text-orange-600 font-medium">
                  <Target className="h-4 w-4" /> Key Responsibilities
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleAddItem("responsibilities");
                  }}
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1 hover:text-blue-700 transition-colors"
                >
                  <Plus className="h-3 w-3" /> Add Item
                </button>
              </div>
              <div className="space-y-2">
                {formData?.responsibilities?.map((item, idx) => (
                  <div key={idx} className="flex gap-2">
                    <span className="text-gray-400 pt-2 text-xs">
                      {idx + 1}.
                    </span>
                    <textarea
                      rows={2}
                      value={item}
                      onChange={(e) =>
                        handleLocalListChange(
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
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleRemoveItem("responsibilities", idx);
                      }}
                      className="text-gray-400 hover:text-red-500 pt-2 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                {(!formData?.responsibilities ||
                  formData.responsibilities.length === 0) && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No responsibilities added yet. Click "Add Item" to start.
                  </p>
                )}
              </div>
            </div>

            {/* Section: Qualifications - FIXED */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="flex items-center gap-2 text-purple-600 font-medium">
                  <GraduationCap className="h-4 w-4" /> Qualifications
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleAddItem("qualifications");
                  }}
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1 hover:text-blue-700 transition-colors"
                >
                  <Plus className="h-3 w-3" /> Add Item
                </button>
              </div>
              <div className="space-y-2">
                {formData?.qualifications?.map((item, idx) => (
                  <div key={idx} className="flex gap-2 items-center">
                    <div className="h-1.5 w-1.5 rounded-full bg-purple-400 shrink-0" />
                    <input
                      type="text"
                      value={item}
                      onChange={(e) =>
                        handleLocalListChange(
                          "qualifications",
                          idx,
                          e.target.value
                        )
                      }
                      className="flex-1 p-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. Bachelor's Degree..."
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleRemoveItem("qualifications", idx);
                      }}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                {(!formData?.qualifications ||
                  formData.qualifications.length === 0) && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No qualifications added yet. Click "Add Item" to start.
                  </p>
                )}
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
                    value={formData?.contactEmail || ""}
                    onChange={(e) =>
                      handleChange("contactEmail", e.target.value)
                    }
                    className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="hr@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Instructions
                  </label>
                  <textarea
                    rows={3}
                    value={formData?.applicationProcess || ""}
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
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-md transition-all flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
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
