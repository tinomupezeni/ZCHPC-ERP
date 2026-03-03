import { useState, useEffect } from "react";
import PostJobModal from "./recruitment/PostJobModal";
import ApplicantsModal from "./recruitment/ApplicantsModal";
import * as jobService from "../../services/jobs.services";
import { getDepartment } from "@/services/hr.services";

import { Search, Plus, Loader, ChevronDown, Download } from "lucide-react";
import { toast } from "sonner";
import ListedJobs from "./recruitment/ListedJobs";
import Candidates from "./recruitment/Candidates";
import AddressManager from "./recruitment/AddressManager";

// Define interfaces for your data structures
interface JobListing {
  id: number;
  title: string;
  department: string;
  department_id?: string | number;
  position_id?: string | number;
  status: "Open" | "Closed" | "Draft" | "Pending";
  postedDate: string;
  applicants: number;
  description: string;
  requirements: string;
  location: string;
  salaryRange?: string;
  // Multi-currency salary fields
  salaryUsdMin?: number | null;
  salaryUsdMax?: number | null;
  salaryZigMin?: number | null;
  salaryZigMax?: number | null;
  // Array fields for editing
  competencies?: string[];
  responsibilities?: string[];
  qualifications?: string[];
  // Other fields
  contactEmail?: string;
  applicationProcess?: string;
  reportsTo?: string;
  isInternal?: boolean;
  notes?: string;
}

interface Candidate {
  id: number;
  name: string;
  job: string;
  status: "Interview" | "Hired" | "Pending" | "Rejected" | "Shortlisted";
  email: string;
  phone: string;
  appliedDate: string;
}

const Recruitment = () => {
  // Modal state
  const [showEditJobModal, setShowEditJobModal] = useState(false);
  const [jobBeingEdited, setJobBeingEdited] = useState<JobListing | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [jobDetails, setJobDetails] = useState<JobListing | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [jobListings, setJobListings] = useState<JobListing[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [activeTab, setActiveTab] = useState("jobs");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);

  // Filter State
  const [departments, setDepartments] = useState<string[]>(["All Departments"]);
  const [selectedDepartment, setSelectedDepartment] =
    useState("All Departments");
  const [selectedStatus, setSelectedStatus] = useState("All Statuses");

  const [showPostJobModal, setShowPostJobModal] = useState(false);
  const [showApplicantsModal, setShowApplicantsModal] = useState(false);
  const [selectedJobForApplicants, setSelectedJobForApplicants] = useState<JobListing | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  // Removed unused applicants modal state as it's handled inside ListedJobs usually,
  // or needs a separate ApplicantsModal component

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  useEffect(() => {
    fetchJobListings();
    fetchDepartmentFilter(); // Renamed to be clear
  }, []);

  // Fetch real departments for the filter
  const fetchDepartmentFilter = async () => {
    try {
      const data = await getDepartment();
      // Map to strings for the filter dropdown
      const deptNames = data.map((d: any) => d.name);
      setDepartments(["All Departments", ...deptNames]);
    } catch (e) {
      console.error("Failed to load departments for filter");
    }
  };

  const handleToggleJobStatus = async (
    jobId: number,
    currentStatus: string
  ) => {
    try {
      // Simple toggle logic
      const newStatus = currentStatus === "Open" ? "Closed" : "Open";
      await jobService.updateJob(jobId, { status: newStatus });

      setJobListings((prevJobs) =>
        prevJobs.map((job) =>
          job.id === jobId ? { ...job, status: newStatus } : job
        )
      );
      toast.success(`Job status changed to ${newStatus}.`);
    } catch (error) {
      toast.error("Error changing job status.");
    }
  };

  const handleEditJob = (jobId: number) => {
    const job = jobListings.find((j) => j.id === jobId);
    if (job) {
      setJobBeingEdited(job);
      setShowPostJobModal(true); // Re-use PostJobModal for editing!
    }
  };

  const handleViewApplicants = (job: JobListing) => {
    setSelectedJobForApplicants(job);
    setShowApplicantsModal(true);
  };

  const formatBackendJob = (job: any): JobListing => ({
    id: job.id,
    title: job.title,
    department: job.department, // This comes as string "IT" from serializer
    department_id: job.department_id,
    position_id: job.position_id,
    status: job.status, // "Open", "Closed", etc.
    postedDate: job.postedDate,
    applicants: job.applicants || 0,
    description: job.description,
    requirements: (job.qualifications || []).join("\n"), // Convert list to string for simple view if needed
    location: job.location,
    salaryRange: job.salaryRange,
    // Multi-currency salary fields
    salaryUsdMin: job.salaryUsdMin,
    salaryUsdMax: job.salaryUsdMax,
    salaryZigMin: job.salaryZigMin,
    salaryZigMax: job.salaryZigMax,
    // Include array fields for editing
    competencies: job.competencies || [],
    responsibilities: job.responsibilities || [],
    qualifications: job.qualifications || [],
    // Include other fields needed for editing
    contactEmail: job.contactEmail,
    applicationProcess: job.applicationProcess,
    reportsTo: job.reportsTo,
    isInternal: job.isInternal,
    notes: job.notes,
  });

  const fetchJobListings = async () => {
    setLoading(true);
    try {
      const data = await jobService.getJobs();

      console.log(data);
      
      const formatted = data.map(formatBackendJob);
      setJobListings(formatted);
    } catch (err) {
      console.error("Error fetching job listings:", err);
      setNotification("Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = jobListings.filter((job) => {
    const matchesSearch = job.title
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    const matchesDepartment =
      selectedDepartment === "All Departments" ||
      job.department === selectedDepartment;
    const matchesStatus =
      selectedStatus === "All Statuses" || job.status === selectedStatus;
    return matchesSearch && matchesDepartment && matchesStatus;
  });

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentJobs = filteredJobs.slice(indexOfFirstItem, indexOfLastItem);
  const currentCandidates = candidates.slice(indexOfFirstItem, indexOfLastItem); // Ensure filteredCandidates is defined if used
  const totalPages = Math.ceil(
    (activeTab === "jobs" ? filteredJobs.length : candidates.length) /
      itemsPerPage
  );

  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  // Helper for Action Menu
  const handleActionSelect = (action: string, job: JobListing) => {
    switch (action) {
      case "view":
      case "edit":
        handleEditJob(job.id);
        break;
      case "toggle":
        handleToggleJobStatus(job.id, job.status);
        break;
      case "applicants":
        handleViewApplicants(job);
        break;
    }
  };

  let activeComponent;

  if (activeTab === "jobs") {
    activeComponent = (
      <ListedJobs
        loading={loading}
        filteredJobs={filteredJobs}
        currentJobs={currentJobs}
        indexOfFirstItem={indexOfFirstItem}
        indexOfLastItem={indexOfLastItem}
        totalPages={totalPages}
        currentPage={currentPage}
        itemsPerPage={itemsPerPage}
        paginate={paginate}
        searchTerm={searchTerm}
        getStatusBadge={(status) => (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            status === 'Open' ? 'bg-green-100 text-green-700' :
            status === 'Closed' ? 'bg-red-100 text-red-700' :
            status === 'Draft' ? 'bg-gray-100 text-gray-700' :
            'bg-yellow-100 text-yellow-700'
          }`}>
            {status}
          </span>
        )}
        handleActionSelect={handleActionSelect}
        setShowPostJobModal={setShowPostJobModal}
        onViewApplicants={handleViewApplicants}
      />
    );
  } else if (activeTab === "candidates") {
    activeComponent = (
      <Candidates
        // ... pass props ...
        filteredCandidates={candidates} // Use actual filtered list
        currentCandidates={currentCandidates}
        loading={loading}
      />
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Notification Toast */}
      {notification && (
        <div className="fixed top-4 right-4 z-50 bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded shadow-lg animate-in slide-in-from-right">
          <p>{notification}</p>
        </div>
      )}

      <div className="flex gap-3 mb-4 items-start justify-between">
        <div className="flex gap-4">
          {["jobs"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium border-b-2 capitalize transition-colors ${
                activeTab === tab
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "jobs" && (
          <button
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition-colors shadow-sm"
            onClick={() => {
              setJobBeingEdited(null); // Ensure we are in "Create" mode
              setShowPostJobModal(true);
            }}
          >
            <Plus className="h-5 w-5" /> Post a Job
          </button>
        )}
      </div>

      {/* Filters (Only show for Jobs/Candidates) */}
      {activeTab !== "addresses" && (
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6 flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          {activeTab === "jobs" && (
            <div className="relative">
              <select
                className="pl-3 pr-8 py-2 border rounded-lg appearance-none bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
              >
                {departments.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            </div>
          )}
        </div>
      )}

      {/* Content */}
      {activeComponent}

      {/* Modals */}
      <PostJobModal
        isOpen={showPostJobModal}
        onClose={() => {
          setShowPostJobModal(false);
          setJobBeingEdited(null);
        }}
        onSave={() => {
          fetchJobListings(); // Refresh list after save
          setShowPostJobModal(false);
        }}
        job={jobBeingEdited} // Pass the job to edit if exists
      />

      <ApplicantsModal
        isOpen={showApplicantsModal}
        job={selectedJobForApplicants}
        onClose={() => {
          setShowApplicantsModal(false);
          setSelectedJobForApplicants(null);
        }}
      />
    </div>
  );
};

export default Recruitment;
