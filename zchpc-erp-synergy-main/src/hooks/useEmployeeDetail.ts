import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { getEmployeeById, updateEmployee } from "@/services/employees.services";
import { isAtLeastAge, MIN_EMPLOYEE_AGE } from "@/lib/dateOfBirth";
import { getDepartment, getPositions } from "@/services/hr.services";
import { Employee, DropdownOption } from "../types/employee";

// The fields this form edits that PATCH /hr/employees/<id>/ accepts
// (UpdateEmployeeRequestSerializer). Anything else in the form is display-only.
const EDITABLE_FIELDS = [
  "first_name",
  "surname",
  "email",
  "phone",
  "date_of_birth",
  "gender",
  "marital_status",
  "department_id",
  "position_id",
  "employee_type",
  "usd_salary",
  "zig_salary",
] as const;
const NUMERIC_FIELDS = new Set(["department_id", "position_id", "usd_salary", "zig_salary"]);

const isEmpty = (value: unknown) =>
  value === undefined || value === null || value === "" ||
  (typeof value === "number" && Number.isNaN(value));

/**
 * The fields the user actually changed, compared with the loaded record. The
 * backend authorizes every field it receives (AUD-02: role/department need
 * the assignment capability, salary the payroll ones), so unchanged fields
 * must not be sent. An emptied field is not sent either: the API reads an
 * omitted field as "unchanged" and has no clearing operation.
 */
const changedFields = (original: Partial<Employee>, edited: Partial<Employee>) => {
  const changes: Record<string, unknown> = {};
  for (const field of EDITABLE_FIELDS) {
    const value = edited[field];
    if (isEmpty(value)) continue;
    const before = original[field];
    const same = NUMERIC_FIELDS.has(field)
      ? !isEmpty(before) && Number(before) === Number(value)
      : String(before ?? "") === String(value);
    if (!same) changes[field] = value;
  }
  return changes;
};

// The HR API's {"error"}, the gate's {"detail"}, or the first field error.
const errorMessage = (error: unknown) => {
  const data = (error as { response?: { data?: unknown } })?.response?.data;
  if (data && typeof data === "object") {
    const body = data as Record<string, unknown>;
    if (typeof body.error === "string") return body.error;
    if (typeof body.detail === "string") return body.detail;
    const fieldError = Object.values(body).find(
      (v) => Array.isArray(v) && typeof v[0] === "string"
    ) as string[] | undefined;
    if (fieldError) return fieldError[0];
  }
  return "Update failed. Check your inputs.";
};

export const useEmployeeDetail = (initialEmployee: Employee, onUpdate: () => void) => {
  const [employee, setEmployee] = useState<Employee>(initialEmployee);
  const [formData, setFormData] = useState<Partial<Employee>>({});
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false); // one save at a time, even within one render
  const [activeTab, setActiveTab] = useState("overview");

  const [departments, setDepartments] = useState<DropdownOption[]>([]);
  const [positions, setPositions] = useState<DropdownOption[]>([]);

  // 1. Initial Load
  useEffect(() => {
    const fetchFullDetails = async () => {
      try {
        const response = await getEmployeeById(initialEmployee.id);
        const data = response.data;
        setEmployee(data);
        setFormData(data);
        
        const depts = await getDepartment();
        setDepartments(depts.data);
      } catch (error) {
        toast.error("Could not load full employee details");
      } finally {
        setLoading(false);
      }
    };
    fetchFullDetails();
  }, [initialEmployee.id]);

  // 2. Cascading Dropdowns for Positions
  useEffect(() => {
    if (isEditing && formData.department_id && !isNaN(formData.department_id)) {
      getPositions(formData.department_id).then(setPositions);
    }
  }, [isEditing, formData.department_id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;

    // If department changes, clear position and reload positions
    if (name === "department_id") {
      setFormData((prev) => ({
        ...prev,
        department_id: value ? parseInt(value, 10) : undefined,
        position_id: undefined, // Clear position when department changes
      }));
      return;
    }

    // If position changes, ensure it's stored as a number
    if (name === "position_id") {
      setFormData((prev) => ({
        ...prev,
        position_id: value ? parseInt(value, 10) : undefined,
      }));
      return;
    }

    setFormData((prev) => ({
      ...prev,
      [name]: type === "number" ? parseFloat(value) : value,
    }));
  };

  const handleSave = async () => {
    if (savingRef.current) return;
    if (!isAtLeastAge(formData.date_of_birth)) {
      toast.error(`Employee must be at least ${MIN_EMPLOYEE_AGE} years old.`);
      return;
    }

    const payload = changedFields(employee, formData);
    if (Object.keys(payload).length === 0) {
      toast.info("No changes to save.");
      setIsEditing(false);
      return;
    }

    savingRef.current = true;
    setSaving(true);
    try {
      await updateEmployee(employee.id, payload);
      toast.success("Profile updated successfully");

      const updated = await getEmployeeById(employee.id);
      setEmployee(updated.data);
      setFormData(updated.data);

      onUpdate();
      setIsEditing(false);
    } catch (error: any) {
      toast.error(errorMessage(error));
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  };

  return {
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
  };
};