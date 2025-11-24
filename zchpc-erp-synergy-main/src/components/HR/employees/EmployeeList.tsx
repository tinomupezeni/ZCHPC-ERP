import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { MoreVertical, Loader, Search } from "lucide-react";

// Sub-component for the Action Menu to isolate state
const EmployeeActions = ({ employee, onView, onEdit }) => {
  return (
    <Menu as="div" className="relative inline-block text-left">
      <MenuButton className="p-2 hover:bg-gray-100 rounded-full focus:outline-none">
        <MoreVertical className="h-5 w-5 text-gray-400" />
      </MenuButton>
      
      {/* Use anchor="bottom end" or traditional absolute positioning with z-index */}
      <MenuItems 
        className="absolute right-0 mt-2 w-40 origin-top-right bg-white divide-y divide-gray-100 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
      >
        <div className="px-1 py-1">
          <MenuItem>
            {({ active }) => (
              <button
                onClick={() => onView(employee)}
                className={`${
                  active ? 'bg-blue-500 text-white' : 'text-gray-900'
                } group flex w-full items-center rounded-md px-2 py-2 text-sm`}
              >
                View Profile
              </button>
            )}
          </MenuItem>
          <MenuItem>
            {({ active }) => (
              <button
                onClick={() => onView(employee)} // Or specific edit handler
                className={`${
                  active ? 'bg-blue-500 text-white' : 'text-gray-900'
                } group flex w-full items-center rounded-md px-2 py-2 text-sm`}
              >
                Edit Details
              </button>
            )}
          </MenuItem>
        </div>
      </MenuItems>
    </Menu>
  );
};

export default function EmployeeList({ employees, loading, onView }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader className="h-8 w-8 animate-spin text-blue-600" />
        <p className="mt-2 text-gray-500">Loading employee records...</p>
      </div>
    );
  }

  if (employees.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border">
        <Search className="h-12 w-12 text-gray-300 mx-auto" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No employees found</h3>
        <p className="mt-1 text-sm text-gray-500">Try adjusting your search filters.</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {["Employee", "Position", "Department", "Contact", "Status", ""].map((h) => (
                <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {employees.map((employee) => (
              <tr key={employee.id} className="hover:bg-gray-50 transition-colors">
                {/* Name Column */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                      {employee.first_name?.[0]}{employee.surname?.[0]}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {employee.first_name} {employee.surname}
                      </div>
                      <div className="text-xs text-gray-500">
                        {employee.employee_id}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Position Column */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{employee.position || "-"}</div>
                  <div className="text-xs text-gray-500">{employee.employee_type}</div>
                </td>

                {/* Department Column */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                    {employee.department || "Unassigned"}
                  </span>
                </td>

                {/* Contact Column */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{employee.email}</div>
                  <div className="text-xs text-gray-500">{employee.phone}</div>
                </td>

                {/* Status Column */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${employee.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}
                  >
                    {employee.is_active ? "Active" : "Inactive"}
                  </span>
                </td>

                {/* Actions Column (The Fix) */}
                {/* Use overflow-visible so the menu doesn't get clipped */}
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium overflow-visible">
                  <EmployeeActions employee={employee} onView={onView} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}