import { useState, useEffect } from "react";
import { toast } from "sonner";
import { getEmployeeById, updateEmployee } from "@/services/employees.services";
import { isAtLeastAge, MIN_EMPLOYEE_AGE } from "@/lib/dateOfBirth";
import { getDepartment, getPositions } from "@/services/hr.services";
import { Employee, DropdownOption } from "../types/employee";

export const useEmployeeDetail = (initialEmployee: Employee, onUpdate: () => void) => {
  const [employee, setEmployee] = useState<Employee>(initialEmployee);
  const [formData, setFormData] = useState<Partial<Employee>>({});
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
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
    if (!isAtLeastAge(formData.date_of_birth)) {
      toast.error(`Employee must be at least ${MIN_EMPLOYEE_AGE} years old.`);
      return;
    }

    setSaving(true);
    try {
      // Remove the read-only string fields from payload
      const payload = { ...formData };
      delete payload.department;
      delete payload.position;

      await updateEmployee(employee.id, payload);
      toast.success("Profile updated successfully");

      const updated = await getEmployeeById(employee.id);
      setEmployee(updated.data);
      setFormData(updated.data);

      onUpdate();
      setIsEditing(false);
    } catch (error: any) {
      const errorMsg = error.response?.data?.position_id ||
                       error.response?.data?.department_id ||
                       error.response?.data?.error ||
                       "Update failed. Check your inputs.";
      toast.error(typeof errorMsg === 'string' ? errorMsg : "Update failed.");
    } finally {
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