import { Loader, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner"; 


interface JobListing {
  id: number;
  title: string;
  department: string;
  status: "Open" | "Closed";
  postedDate: string; // YYYY-MM-DD format
  applicants: number;
  description: string;
  requirements: string;
  location: string;
  salaryRange: string;
}

export default function JobDetails({ job, setShowModal }: { job: JobListing; setShowModal: (show: boolean) => void }) {

    console.log(job);
    
  const [loading, setLoading] = useState(false);
  const [selectedDeductions, setSelectedDeductions] = useState([]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl w-full max-w-2xl shadow-xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 p-4 flex justify-between items-center flex-shrink-0">
          <h2 className="text-xl font-semibold text-white">Job Details</h2>
          <button
            onClick={() => setShowModal(false)}
            className="text-white hover:text-blue-200 transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Area */}
        <div className="p-6 overflow-y-auto flex-grow">
          {/* Job Title */}
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              {job.title}
            </h3>
            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <span className="font-medium">Department:</span> {job.department}
              </span>
              <span className="flex items-center gap-1">
                <span className="font-medium">Status:</span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    job.status === 'Open' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}
                >
                  {job.status}
                </span>
              </span>
              <span className="flex items-center gap-1">
                <span className="font-medium">Posted:</span> {new Date(job.postedDate).toLocaleDateString()}
              </span>
              <span className="flex items-center gap-1">
                <span className="font-medium">Applicants:</span> {job.applicants}
              </span>
            </div>
          </div>

          {/* Description Section */}
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-800 mb-2 pb-1 border-b border-gray-200">
              Job Description
            </h4>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {job.description}
            </p>
          </div>

          {/* Requirements Section */}
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-800 mb-2 pb-1 border-b border-gray-200">
              Requirements
            </h4>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {job.requirements}
            </p>
          </div>

          {/* Location and Salary Section */}
          <div>
            <h4 className="text-lg font-semibold text-gray-800 mb-2 pb-1 border-b border-gray-200">
              Location & Salary
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Location:</p>
                <p className="text-gray-900">{job.location}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Salary Range:</p>
                <p className="text-gray-900">{job.salaryRange}</p>
              </div>
            </div>
          </div>
        </div>

       
      </div>
    </div>
  );
}