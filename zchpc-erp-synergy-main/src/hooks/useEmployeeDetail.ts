import { useState, useEffect } from "react";
import { toast } from "sonner";
import { getOneEmployee, updateEmployee } from "@/services/employees.services";
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
        const response = await getOneEmployee(initialEmployee.id);
        const data = response.data;
        setEmployee(data);
        setFormData(data);
        
        const depts = await getDepartment();
        setDepartments(depts);
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
    setFormData((prev) => ({
      ...prev,
      [name]: type === "number" ? parseFloat(value) : value,
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateEmployee(employee.id, formData);
      toast.success("Profile updated successfully");
      
      const updated = await getOneEmployee(employee.id);
      setEmployee(updated.data);
      setFormData(updated.data);
      
      onUpdate();
      setIsEditing(false);
    } catch (error) {
      toast.error("Update failed. Check your inputs.");
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