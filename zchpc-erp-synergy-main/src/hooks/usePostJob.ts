import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  getDepartment,
  getPositions,
  addDepartment,
  addPosition,
} from "@/services/hr.services";
import { createJob, updateJob } from "@/services/jobs.services";
import { JobListing, Option } from "@/types/postJob";

// Helper: safe date (yyyy-mm-dd)
const todayISO = () => new Date().toISOString().split("T")[0];

// Helper: normalize/ensure arrays exist
const ensureList = (v: any) => (Array.isArray(v) ? v : []);

// Helper: robust string compare
const norm = (s: any) => String(s ?? "").trim().toLowerCase();

// Helper: fresh empty form for "Create"
const makeEmptyForm = (): JobListing =>
  ({
    title: "",
    department_id: "",
    position_id: "",
    status: "Open",
    postedDate: todayISO(),
    description: "",
    qualifications: [],
    applicationProcess: "",
    location: "Harare",
    salaryRange: "",
    salaryUsdMin: null,
    salaryUsdMax: null,
    salaryZigMin: null,
    salaryZigMax: null,
    contactEmail: "hroffice@zchpc.ac.zw",
    responsibilities: [],
    reportsTo: "ZCHPC Director",
    competencies: [],
    isInternal: false,
  } as unknown as JobListing);

export const usePostJob = (
  isOpen: boolean,
  job: JobListing | null,
  onClose: () => void,
  onSave?: () => void
) => {
  const [formData, setFormData] = useState<JobListing | null>(null);
  const [loading, setLoading] = useState(false);
  const [departments, setDepartments] = useState<Option[]>([]);
  const [positions, setPositions] = useState<Option[]>([]);

  // Inline Add States
  const [isAddingDept, setIsAddingDept] = useState(false);
  const [newDeptName, setNewDeptName] = useState("");
  const [isAddingPos, setIsAddingPos] = useState(false);
  const [newPosTitle, setNewPosTitle] = useState("");
  const [miniLoading, setMiniLoading] = useState(false);

  /**
   * 1) When modal opens: load departments + initialize formData
   *    - If editing: hydrate fields, ensure arrays, set sane defaults.
   *    - IMPORTANT: your incoming job sometimes has `department` (name) but no `department_id`.
   *      We resolve ids later once departments/positions are fetched.
   */
  useEffect(() => {
    if (!isOpen) return;

    // reset inline add state every open (prevents weird UI leftovers)
    setIsAddingDept(false);
    setNewDeptName("");
    setIsAddingPos(false);
    setNewPosTitle("");

    // Always fetch departments on open
    getDepartment()
      .then((res) => setDepartments(res.data))
      .catch((e) => {
        console.error(e);
        setDepartments([]);
      });

    if (job) {
      setFormData({
        ...job,
        // guarantee lists
        responsibilities: ensureList(job.responsibilities),
        qualifications: ensureList(job.qualifications),
        competencies: ensureList(job.competencies),

        // defaults
        reportsTo: job.reportsTo || "ZCHPC Director",
        isInternal: !!job.isInternal,
        location: job.location || "Harare",
        contactEmail: job.contactEmail || "hroffice@zchpc.ac.zw",
        applicationProcess: job.applicationProcess || "",
        description: job.description || "",
        salaryRange: job.salaryRange || "",
        // Multi-currency salary fields
        salaryUsdMin: job.salaryUsdMin ?? null,
        salaryUsdMax: job.salaryUsdMax ?? null,
        salaryZigMin: job.salaryZigMin ?? null,
        salaryZigMax: job.salaryZigMax ?? null,
        status: job.status || "Open",
        postedDate: job.postedDate || todayISO(),

        // IDs: if missing, keep empty for now (we'll resolve below)
        department_id: (job as any).department_id || "",
        position_id: (job as any).position_id || "",
      });
    } else {
      setFormData(makeEmptyForm());
    }
  }, [isOpen, job]);

  /**
   * 2) Resolve department_id when editing and we have departments loaded
   *    If backend provided department name string (job.department) but not id,
   *    we map it here.
   */
  useEffect(() => {
    if (!isOpen || !job || !formData) return;
    if (formData.department_id) return; // already resolved

    const deptName = (job as any).department; // your job array has `department: "Administration"`
    if (!deptName || !departments.length) return;

    const match = departments.find((d) => norm(d.name) === norm(deptName));
    if (!match) return;

    setFormData((prev) => (prev ? { ...prev, department_id: match.id } : prev));
  }, [isOpen, job, formData, departments]);

  /**
   * 3) Whenever department_id changes, fetch positions for that dept.
   *    Also, if dept changes (user edit), clear position_id & title to prevent stale selections.
   */
  useEffect(() => {
    if (!isOpen) return;

    const deptId = formData?.department_id;
    if (!deptId) {
      setPositions([]);
      return;
    }

    getPositions(deptId)
      .then((res) => setPositions(res))
      .catch(() => setPositions([]));
  }, [isOpen, formData?.department_id]);

  /**
   * 4) Resolve position_id when editing after positions load
   *    If backend didn’t supply position_id, try to match by title string.
   */
  useEffect(() => {
    if (!isOpen || !job || !formData) return;
    if (formData.position_id) return; // already set
    if (!positions.length) return;

    const title = (job as any).title;
    if (!title) return;

    const match = positions.find((p) => norm(p.title) === norm(title));
    if (!match) return;

    setFormData((prev) =>
      prev
        ? {
            ...prev,
            position_id: match.id,
            // keep title consistent with the matched position
            title: match.title,
          }
        : prev
    );
  }, [isOpen, job, formData, positions]);

  const handleChange = (field: keyof JobListing, value: any) => {
    setFormData((prev) => {
      if (!prev) return null;

      // If user changes department manually, prevent stale position selection
      if (field === "department_id") {
        return {
          ...prev,
          department_id: value,
          position_id: "",
          // optional: clear title so it refills from position selection
          // title: "",
        };
      }

      return { ...prev, [field]: value };
    });
  };

  const handleListChange = (
    field: "responsibilities" | "qualifications" | "competencies",
    index: number,
    value: string
  ) => {
    setFormData((prev) => {
      if (!prev) return null;
      const list = [...ensureList((prev as any)[field])];
      list[index] = value;
      return { ...prev, [field]: list } as JobListing;
    });
  };

  const handleCreateDept = async () => {
    if (!newDeptName.trim()) return;
    setMiniLoading(true);
    try {
      const newDept = await addDepartment({ name: newDeptName });
      setDepartments((prev) => [...prev, newDept]);

      // select it + reset dependent fields
      setFormData((prev) =>
        prev
          ? {
              ...prev,
              department_id: newDept.id,
              position_id: "",
            }
          : prev
      );

      setIsAddingDept(false);
      setNewDeptName("");
      toast.success("Department added");
    } catch (e) {
      console.error(e);
      toast.error("Failed to add department");
    } finally {
      setMiniLoading(false);
    }
  };

  const handleCreatePos = async () => {
    if (!newPosTitle.trim() || !formData?.department_id) return;
    setMiniLoading(true);
    try {
      const newPos = await addPosition({
        title: newPosTitle,
        department_id: formData.department_id,
      });

      setPositions((prev) => [...prev, newPos]);

      setFormData((prev) =>
        prev
          ? {
              ...prev,
              position_id: newPos.id,
              title: newPos.title,
            }
          : prev
      );

      setIsAddingPos(false);
      setNewPosTitle("");
      toast.success("Position added");
    } catch (e) {
      console.error(e);
      toast.error("Failed to add position");
    } finally {
      setMiniLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData) return;

    // basic validation (because your backend expects ids)
    if (!formData.department_id) {
      toast.error("Please select a department");
      return;
    }
    if (!formData.position_id) {
      toast.error("Please select a position");
      return;
    }

    setLoading(true);
    try {
      const selectedPos = positions.find((p) => p.id == formData.position_id);

      const cleanData: Partial<JobListing> = {
        ...formData,
        // Always keep title in sync with selected position if possible
        title: selectedPos ? selectedPos.title : formData.title,

        // IMPORTANT: keep department_id as ID only (don’t fall back to name)
        department_id: formData.department_id,

        responsibilities: ensureList(formData.responsibilities)
          .map((r) => String(r).trim())
          .filter(Boolean),
        qualifications: ensureList(formData.qualifications)
          .map((q) => String(q).trim())
          .filter(Boolean),
        competencies: ensureList(formData.competencies)
          .map((c) => String(c).trim())
          .filter(Boolean),

        isInternal: !!formData.isInternal,
        reportsTo: formData.reportsTo || "ZCHPC Director",
        location: formData.location || "Harare",
        contactEmail: formData.contactEmail || "hroffice@zchpc.ac.zw",
        applicationProcess: formData.applicationProcess || "",
        description: formData.description || "",
        salaryRange: formData.salaryRange || "",
        status: formData.status || "Open",
        postedDate: formData.postedDate || todayISO(),
      };

      // Explicitly remove the 'department' object if it exists to avoid sending unexpected nested data
      if (cleanData.department && typeof cleanData.department === 'object') {
          delete cleanData.department;
      }

      if (job?.id) {
        await updateJob(job.id, cleanData);
      } else {
        await createJob(cleanData);
      }

      toast.success(job ? "Job updated successfully" : "Job posted successfully");
      if (onSave) {
        onSave(); // This triggers the refresh and closes the modal
      } else {
        onClose();
      }
    } catch (error) {
      console.error("Error saving job:", error);
      toast.error("Failed to save job. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const addListItem = (field: keyof JobListing) => {
    setFormData((prev) => {
      if (!prev) return null;
      const currentList = ensureList((prev as any)[field]);
      return { ...prev, [field]: [...currentList, ""] } as JobListing;
    });
  };

  const removeListItem = (field: keyof JobListing, index: number) => {
    setFormData((prev) => {
      if (!prev) return null;
      const currentList = ensureList((prev as any)[field]);
      const filteredList = currentList.filter((_: any, i: number) => i !== index);
      return { ...prev, [field]: filteredList } as JobListing;
    });
  };

  return {
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
  };
};
