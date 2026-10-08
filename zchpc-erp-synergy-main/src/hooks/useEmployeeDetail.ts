import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { getEmployeeById, updateEmployee } from "@/services/employees.services";
import { isAtLeastAge, MIN_EMPLOYEE_AGE } from "@/lib/dateOfBirth";
import { getDepartment, getPositions } from "@/services/hr.services";
import { Employee, DropdownOption } from "../types/employee";
import { NO_PERMISSION, readApiError } from "@/lib/apiErrors";

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

// What the user is told when a save is refused, by the backend's code. The
// backend's own messages are written for developers (they can name internal
// permissions or record ids), so they are never shown.
const SAVE_REFUSALS: Record<string, string> = {
  EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY: "You don't have permission to edit this employee.",
  EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED:
    "You don't have permission to change an employee's department or role.",
  PAYROLL_PERMISSION_DENIED: "You don't have permission to change salary details.",
  PAYROLL_TARGET_DENIED: "You don't have permission to change this employee's salary details.",
  POSITION_DEPARTMENT_MISMATCH:
    "The selected position doesn't belong to this department. Please choose a position from the selected department.",
  DUPLICATE_EMAIL: "This email address is already in use. Please enter a different email address.",
  INVALID_EMAIL_FORMAT: "Please enter a valid email address.",
  EMPTY_EMAIL: "Please enter a valid email address.",
  INVALID_PHONE_FORMAT: "Please enter a valid phone number (7 to 15 digits).",
  EMPTY_PHONE: "Please enter a valid phone number (7 to 15 digits).",
  EMPTY_FIRST_NAME: "First name can't be empty.",
  EMPTY_SURNAME: "Surname can't be empty.",
  EMPLOYEE_ARCHIVED: "This employee has been archived, so their record can't be changed.",
};

const FIELD_LABELS: Record<string, string> = {
  first_name: "First name",
  surname: "Surname",
  email: "Email",
  phone: "Phone",
  date_of_birth: "Date of birth",
  gender: "Gender",
  marital_status: "Marital status",
  department_id: "Department",
  position_id: "Position",
  employee_type: "Employment type",
  usd_salary: "Salary (USD)",
  zig_salary: "Salary (ZiG)",
};

const saveErrorMessage = (error: unknown) => {
  const { status, code, fieldErrors } = readApiError(error);
  if (code && SAVE_REFUSALS[code]) return SAVE_REFUSALS[code];
  if (status === undefined) {
    return "We couldn't reach the server, so your changes weren't saved. Please check your connection and try again.";
  }
  if (status === 404) {
    return "Some of this information is no longer available. Please refresh the page and try again.";
  }
  if (status === 403) return NO_PERMISSION;
  const [field, message] = Object.entries(fieldErrors)[0] ?? [];
  if (field && message) return `${FIELD_LABELS[field] ?? "This field"}: ${message}`;
  return "We couldn't save your changes. Please check the information and try again.";
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
        const { status } = readApiError(error);
        toast.error(
          status === 404
            ? "This employee record is no longer available. Please refresh the page."
            : status === 403
              ? "You don't have permission to view this employee's details."
              : "We couldn't load this employee's details. Please close the profile and try again."
        );
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
    } catch (error) {
      toast.error(saveErrorMessage(error));
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