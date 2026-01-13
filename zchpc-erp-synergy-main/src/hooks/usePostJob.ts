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

export const usePostJob = (
  isOpen: boolean,
  job: JobListing | null,
  onClose: () => void
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

  useEffect(() => {
    if (isOpen) {
      getDepartment()
        .then((res) => setDepartments(res.data))
        .catch(console.error);

      if (job) {
        setFormData({
          ...job,
          responsibilities: job.responsibilities || [],
          qualifications: job.qualifications || [],
          competencies: job.competencies || [],
          reportsTo: job.reportsTo || "ZCHPC Director",
          isInternal: job.isInternal || false,
        });
        if (job.department_id) {
          getPositions(job.department_id)
            .then((res) => setPositions(res))
            .catch(() => setPositions([]));
        }
      } else {
        setFormData({
          title: "",
          department_id: "",
          position_id: "",
          status: "Open",
          postedDate: new Date().toISOString().split("T")[0],
          description: "",
          qualifications: [],
          applicationProcess: "",
          location: "Harare",
          salaryRange: "",
          contactEmail: "hroffice@zchpc.ac.zw",
          responsibilities: [],
          reportsTo: "ZCHPC Director",
          competencies: [],
          isInternal: false,
        });
      }
    }
  }, [isOpen, job]);

  useEffect(() => {
    if (formData?.department_id) {
      getPositions(formData.department_id)
        .then((res) => setPositions(res))
        .catch(() => setPositions([]));
    } else {
      setPositions([]);
    }
  }, [formData?.department_id]);

  const handleChange = (field: keyof JobListing, value: any) => {
    setFormData((prev) => (prev ? { ...prev, [field]: value } : null));
  };

  const handleListChange = (
    field: "responsibilities" | "qualifications" | "competencies",
    index: number,
    value: string
  ) => {
    setFormData((prev) => {
      if (!prev) return null;
      const list = [...(prev[field] || [])];
      list[index] = value;
      return { ...prev, [field]: list };
    });
  };

  const handleCreateDept = async () => {
    if (!newDeptName.trim()) return;
    setMiniLoading(true);
    try {
      const newDept = await addDepartment({ name: newDeptName });
      setDepartments((prev) => [...prev, newDept]);
      handleChange("department_id", newDept.id);
      setIsAddingDept(false);
      setNewDeptName("");
      toast.success("Department added");
    } catch (e) {
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
      handleChange("position_id", newPos.id);
      handleChange("title", newPos.title);
      setIsAddingPos(false);
      setNewPosTitle("");
      toast.success("Position added");
    } catch (e) {
      toast.error("Failed to add position");
    } finally {
      setMiniLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData) return;

    setLoading(true);
    try {
      const selectedPos = positions.find((p) => p.id == formData.position_id);

      // Clean and prepare data for submission
      const cleanData = {
        ...formData,
        title: selectedPos ? selectedPos.title : formData.title,
        department_id: formData.department_id || formData.department,
        // Filter out empty strings from arrays
        responsibilities: (formData.responsibilities || []).filter((r) =>
          r.trim()
        ),
        qualifications: (formData.qualifications || []).filter((q) => q.trim()),
        competencies: (formData.competencies || []).filter((c) => c.trim()),
        // Ensure boolean is properly set
        isInternal: formData.isInternal || false,
        // Ensure other fields are included
        reportsTo: formData.reportsTo || "ZCHPC Director",
        location: formData.location || "Harare",
        contactEmail: formData.contactEmail || "hroffice@zchpc.ac.zw",
        applicationProcess: formData.applicationProcess || "",
        description: formData.description || "",
        salaryRange: formData.salaryRange || "",
        status: formData.status || "Open",
        postedDate:
          formData.postedDate || new Date().toISOString().split("T")[0],
      };

      if (job?.id) {
        await updateJob(job.id, cleanData);
      } else {
        await createJob(cleanData);
      }

      toast.success(
        job ? "Job updated successfully" : "Job posted successfully"
      );
      onClose();
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
      const currentList = (prev[field] as string[]) || [];
      return { ...prev, [field]: [...currentList, ""] };
    });
  };

  const removeListItem = (field: keyof JobListing, index: number) => {
    setFormData((prev) => {
      if (!prev) return null;
      const currentList = (prev[field] as string[]) || [];
      const filteredList = currentList.filter((_, i) => i !== index);
      // Keep empty array instead of adding empty string back
      return { ...prev, [field]: filteredList };
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
