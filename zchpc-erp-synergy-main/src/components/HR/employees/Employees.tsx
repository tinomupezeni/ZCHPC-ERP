import { useEffect, useState } from "react";
import { Plus, Download, Search, Filter } from "lucide-react";
import AddEmployee from "./AddEmployee";
import EmployeeList from "./EmployeeList";
import EmployeeDetailModal from "./EmployeeDetailModal";
import { getEmployees } from "@/server/employees.services";

const Employees = () => {
  // Data States
  const [allEmployees, setAllEmployees] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [loading, setLoading] = useState(false);

  // Modal States
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null); // Stores the employee object to view/edit

  // Filter States
  const [searchTerm, setSearchTerm] = useState("");
  const [deptFilter, setDeptFilter] = useState("");

  const fetchEmployees = () => {
    setLoading(true);
    getEmployees()
      .then((response) => {
        setAllEmployees(response.data);
        setFilteredEmployees(response.data);
      })
      .catch((error) => console.error("Fetch error:", error))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  // Filter Logic
  useEffect(() => {
    let result = allEmployees;

    if (searchTerm) {
      const lowerTerm = searchTerm.toLowerCase();
      result = result.filter(emp => 
        emp.first_name?.toLowerCase().includes(lowerTerm) ||
        emp.surname?.toLowerCase().includes(lowerTerm) ||
        emp.email?.toLowerCase().includes(lowerTerm)
      );
    }

    if (deptFilter) {
      result = result.filter(emp => emp.department === deptFilter);
    }

    setFilteredEmployees(result);
  }, [searchTerm, deptFilter, allEmployees]);

  return (
    <div className="p-6 bg-gray-50 min-h-screen space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Employee Management</h1>
          <p className="text-sm text-gray-500">{filteredEmployees.length} active records</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 border bg-white rounded-lg text-gray-700 hover:bg-gray-50">
            <Download className="h-4 w-4" /> Export
          </button>
          <button 
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" /> Add Employee
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input 
            type="text" 
            placeholder="Search employees..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="relative w-full md:w-auto">
           <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
           <select 
             className="pl-10 pr-8 py-2 border rounded-lg appearance-none bg-white focus:ring-2 focus:ring-blue-500 outline-none w-full"
             onChange={(e) => setDeptFilter(e.target.value)}
           >
             <option value="">All Departments</option>
             {/* Extract Unique Departments */}
             {[...new Set(allEmployees.map(e => e.department).filter(Boolean))].map(d => (
               <option key={d} value={d}>{d}</option>
             ))}
           </select>
        </div>
      </div>

      {/* Table */}
      <EmployeeList 
        employees={filteredEmployees} 
        loading={loading} 
        onView={(emp) => setSelectedEmployee(emp)} 
      />

      {/* Modals */}
      {showAddModal && (
        <AddEmployee 
          setShowModal={setShowAddModal} 
          fetchEmployees={fetchEmployees} 
        />
      )}

      {selectedEmployee && (
        <EmployeeDetailModal 
          employee={selectedEmployee}
          onClose={() => setSelectedEmployee(null)}
          onUpdate={fetchEmployees}
        />
      )}

    </div>
  );
};

export default Employees;