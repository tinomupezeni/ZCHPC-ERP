import { useState, useEffect } from "react";
import { toast } from "sonner";
import { addEmployee } from "@/services/employees.services";
import {
  addPosition,
  getPositions,
  addDepartment,
  getDepartment,
} from "@/services/hr.services";
import {
  EmployeeFormState,
  Department,
  Position,
  Deduction,
} from "@/types/addEmployee";

export const useAddEmployee = (
  setShowModal: (val: boolean) => void,
  fetchEmployees: () => void
) => {
  const [loading, setLoading] = useState(false);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);

  // Inline Add States
  const [isAddingDept, setIsAddingDept] = useState(false);
  const [newDeptName, setNewDeptName] = useState("");
  const [deptLoading, setDeptLoading] = useState(false);
  const [isAddingPos, setIsAddingPos] = useState(false);
  const [newPosTitle, setNewPosTitle] = useState("");
  const [posLoading, setPosLoading] = useState(false);

  const [selectedDeductions, setSelectedDeductions] = useState<Deduction[]>([]);
  const [employee, setEmployee] = useState<EmployeeFormState>({
    ecNumber: "",
    firstname: "",
    surname: "",
    nationalId: "",
    dob: "",
    gender: "",
    maritalStatus: "",
    email: "",
    phone: "",
    bankName: "",
    accountNumber: "",
    payFrequency: "Monthly",
    employeeType: "Full-time",
    leaveDays: 21,
    pensionScheme: "",
    position: "",
    department: "",
    usd_salary: "",
    zig_salary: "",
    contractFrom: "",
    contractTo: "",
    emergencyContactName: "",
    emergencyContactPhone: "",
    emergencyContactRelationship: "",
    selectedDeductions: [],
  });

  useEffect(() => {
    const loadDepartments = async () => {
      try {
        const data = await getDepartment();
        setDepartments(data.data || []);
      } catch (error) {
        toast.error("Failed to load departments");
      }
    };
    loadDepartments();
  }, []);

  useEffect(() => {
    const loadPositions = async () => {
      if (!employee.department) {
        setPositions([]);
        return;
      }
      try {
        const data = await getPositions(employee.department);
        setPositions(data || []);
      } catch (error) {
        toast.error("Failed to load positions");
      }
    };
    loadPositions();
  }, [employee.department]);

  useEffect(() => {
    setEmployee((prev) => ({ ...prev, selectedDeductions }));
  }, [selectedDeductions]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setEmployee({ ...employee, [e.target.name]: e.target.value });
  };

  const handleCreateDepartment = async () => {
    if (!newDeptName.trim()) return;
    setDeptLoading(true);
    try {
      const newDept = await addDepartment({ name: newDeptName });
      setDepartments([...departments, newDept]);
      setEmployee((prev) => ({ ...prev, department: newDept.id }));
      toast.success("Department created!");
      setIsAddingDept(false);
      setNewDeptName("");
    } finally {
      setDeptLoading(false);
    }
  };

  const handleCreatePosition = async () => {
    if (!newPosTitle.trim() || !employee.department) return;
    setPosLoading(true);
    try {
      const newPos = await addPosition({
        title: newPosTitle,
        department_id: employee.department,
      });
      setPositions([...positions, newPos]);
      setEmployee((prev) => ({ ...prev, position: newPos.id }));
      toast.success("Position created!");
      setIsAddingPos(false);
      setNewPosTitle("");
    } finally {
      setPosLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const payload: any = {
      first_name: employee.firstname,
      surname: employee.surname,
      national_id: employee.nationalId,
      date_of_birth: employee.dob || null,
      gender: employee.gender,
      marital_status: employee.maritalStatus,
      email: employee.email,
      phone: employee.phone,
      bank_name: employee.bankName,
      bank_account: employee.accountNumber,
      pay_frequency: employee.payFrequency,
      employee_type: employee.employeeType,
      leave_days_entitled: employee.leaveDays,
      contract_from: employee.contractFrom || null,
      contract_to: employee.contractTo || null,
      department_id: employee.department,
      position_id: employee.position,
      usd_salary: employee.usd_salary ? parseFloat(employee.usd_salary) : 0,
      zig_salary: employee.zig_salary ? parseFloat(employee.zig_salary) : 0,
      pension_fund: employee.pensionScheme,
      emergency_contact_name: employee.emergencyContactName,
      emergency_contact_number: employee.emergencyContactPhone,
      emergency_contact_relationship: employee.emergencyContactRelationship,
      deductions_data: selectedDeductions,
    };

    // Only include employee_id if provided (otherwise backend auto-generates)
    if (employee.ecNumber.trim()) {
      payload.employee_id = employee.ecNumber.trim();
    }

    try {
      await addEmployee(payload);
      toast.success("Employee added successfully");
      setShowModal(false);
      fetchEmployees();
    } catch (error: any) {
      const errData = error.response?.data;
      const msg = errData?.employee_id
        ? "EC Number already exists."
        : errData?.email
        ? "Email already exists."
        : errData?.national_id
        ? "National ID already exists."
        : errData?.position_id
        ? errData.position_id
        : "Check inputs.";
      toast.error(typeof msg === 'string' ? msg : "Check inputs.");
    } finally {
      setLoading(false);
    }
  };

  return {
    employee,
    departments,
    positions,
    loading,
    isAddingDept,
    setIsAddingDept,
    newDeptName,
    setNewDeptName,
    deptLoading,
    isAddingPos,
    setIsAddingPos,
    newPosTitle,
    setNewPosTitle,
    posLoading,
    selectedDeductions,
    setSelectedDeductions,
    handleChange,
    handleCreateDepartment,
    handleCreatePosition,
    handleSubmit,
  };
};
