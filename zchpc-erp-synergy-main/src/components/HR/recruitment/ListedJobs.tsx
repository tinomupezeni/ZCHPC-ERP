import { Briefcase, Loader, Plus } from "lucide-react";
import React from "react";

export default function ListedJobs({
  loading,
  filteredJobs,
  currentJobs,
  indexOfFirstItem,
  indexOfLastItem,
  totalPages,
  currentPage,
  itemsPerPage,
  paginate,
  searchTerm,
  getStatusBadge,
  handleActionSelect,
  setShowPostJobModal,
}) {
  return (
    <div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Job Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Closing Date
                </th>

                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center">
                    <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                    <p className="mt-2 text-sm text-gray-500">
                      Loading job listings...
                    </p>
                  </td>
                </tr>
              ) : currentJobs.length > 0 ? (
                currentJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {job.title}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.department}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(job.postedDate).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(job.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {/* DROPDOWN SELECT for actions */}
                      <div className="inline-block">
                        <select
                          defaultValue=""
                          onChange={(e) => {
                            const action = e.target.value;
                            // handleActionSelect will open Edit when action === "view"
                            handleActionSelect(action, job);
                            // reset the select to placeholder after a short tick so the user sees the selection briefly
                            setTimeout(() => {
                              (e.target as HTMLSelectElement).value = "";
                            }, 150);
                          }}
                          className="border rounded px-3 py-1 text-sm focus:outline-none"
                        >
                          <option value="" disabled>
                            Actions
                          </option>
                          <option value="view">View Details (Edit)</option>
                          <option value="applicants">View Applicants</option>
                          <option value="toggle">
                            {job.status === "Open" ? "Close Job" : "Reopen Job"}
                          </option>
                        </select>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center">
                    <div className="flex flex-col items-center justify-center">
                      <Briefcase className="h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">
                        No job listings found
                      </h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {searchTerm
                          ? "Try adjusting your search or filter"
                          : "Post a new job to get started"}
                      </p>
                      {!searchTerm && (
                        <button
                          type="button"
                          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none"
                          onClick={() => setShowPostJobModal(true)}
                        >
                          <Plus className="-ml-1 mr-2 h-5 w-5" />
                          Post a Job
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {filteredJobs.length > itemsPerPage && (
          <div className="px-6 py-4 border-t flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing{" "}
              <span className="font-medium">{indexOfFirstItem + 1}</span> to{" "}
              <span className="font-medium">
                {Math.min(indexOfLastItem, filteredJobs.length)}
              </span>{" "}
              of <span className="font-medium">{filteredJobs.length}</span>{" "}
              results
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => paginate(currentPage - 1)}
                disabled={currentPage === 1}
                className={`px-3 py-1 rounded-md border ${
                  currentPage === 1
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                    : "hover:bg-gray-100"
                }`}
              >
                Previous
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                (number) => (
                  <button
                    key={number}
                    onClick={() => paginate(number)}
                    className={`px-3 py-1 rounded-md border ${
                      currentPage === number
                        ? "bg-blue-600 text-white"
                        : "hover:bg-gray-100"
                    }`}
                  >
                    {number}
                  </button>
                )
              )}
              <button
                onClick={() => paginate(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={`px-3 py-1 rounded-md border ${
                  currentPage === totalPages
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                    : "hover:bg-gray-100"
                }`}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
