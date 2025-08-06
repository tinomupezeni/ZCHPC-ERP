import { useState, useEffect } from "react";
import {
  Search,
  Plus,
  MoreVertical,
  Loader,
  ChevronDown,
  Filter,
  Download,
  User,
  Briefcase,
  Calendar,
  Mail,
  Phone,
  X,
} from "lucide-react";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";

// Define interfaces for your data structures
interface JobListing {
  id: number;
  title: string;
  department: string;
  status: "Open" | "Closed";
  postedDate: string;
  applicants: number;
  description: string;
  requirements: string;
  location: string;
  salaryRange: string;
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

// PostJobModal Component
const PostJobModal = ({ isOpen, onClose, onSave }: { isOpen: boolean; onClose: () => void; onSave: (job: Omit<JobListing, 'id' | 'applicants' | 'postedDate' | 'status'>) => void }) => {
  const [jobTitle, setJobTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [location, setLocation] = useState("");
  const [salaryRange, setSalaryRange] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      title: jobTitle,
      department,
      description,
      requirements,
      location,
      salaryRange,
    });
    setJobTitle("");
    setDepartment("");
    setDescription("");
    setRequirements("");
    setLocation("");
    setSalaryRange("");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-5 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">Post a New Job</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-5">
          <div className="mb-4">
            <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-700 mb-1">
              Job Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="jobTitle"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
            <label htmlFor="department" className="block text-sm font-medium text-gray-700 mb-1">
              Department <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="department"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <input
              type="text"
              id="location"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>

          <div className="mb-4">
            <label htmlFor="salaryRange" className="block text-sm font-medium text-gray-700 mb-1">
              Salary Range (e.g., $50,000 - $70,000)
            </label>
            <input
              type="text"
              id="salaryRange"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              value={salaryRange}
              onChange={(e) => setSalaryRange(e.target.value)}
            />
          </div>

          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Job Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="description"
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            ></textarea>
          </div>

          <div className="mb-6">
            <label htmlFor="requirements" className="block text-sm font-medium text-gray-700 mb-1">
              Specific Job Requirements (e.g., skills, experience, qualifications)
              <span className="text-red-500">*</span>
            </label>
            <textarea
              id="requirements"
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              required
            ></textarea>
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Post Job
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// JobDetailsModal Component
const JobDetailsModal = ({ isOpen, job, onClose }: {
  isOpen: boolean;
  job: JobListing | null;
  onClose: () => void;
}) => {
  if (!isOpen || !job) return null;

  const detailRow = (label: string, value: string | number) => (
    <div className="flex justify-between py-1">
      <span className="font-medium text-gray-700">{label}</span>
      <span className="text-gray-900 text-right max-w-[60%]">{value}</span>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
        <div className="flex justify-between items-center p-5 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">Job Details</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>
        <div className="p-5 space-y-2 text-sm">
          {detailRow('Title', job.title)}
          {detailRow('Department', job.department)}
          {detailRow('Status', job.status)}
          {detailRow('Posted Date', job.postedDate)}
          {detailRow('Applicants', job.applicants)}
          {detailRow('Location', job.location)}
          {detailRow('Salary Range', job.salaryRange)}
          <div>
            <h3 className="font-medium text-gray-700">Description</h3>
            <p className="text-gray-900 whitespace-pre-line mt-1">{job.description}</p>
          </div>
          <div>
            <h3 className="font-medium text-gray-700">Requirements</h3>
            <p className="text-gray-900 whitespace-pre-line mt-1">{job.requirements}</p>
          </div>
        </div>
        <div className="flex justify-end p-4 border-t">
          <button onClick={onClose} className="px-4 py-2 border rounded">Close</button>
        </div>
      </div>
    </div>
  );
};

// EditJobModal Component
const EditJobModal = ({ isOpen, job, onClose, onSave }: {
  isOpen: boolean;
  job: JobListing | null;
  onClose: () => void;
  onSave: (updated: JobListing) => void;
}) => {
  const [formData, setFormData] = useState<JobListing | null>(job);

  // keep form data in sync when a different job is selected
  useEffect(() => setFormData(job), [job]);

  if (!isOpen || !formData) return null;

  const handleChange = (field: keyof JobListing, value: string) => {
    setFormData(prev => prev ? { ...prev, [field]: value } : prev);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData) onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-5 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">Edit Job</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <input type="text" value={formData.title} onChange={e=>handleChange('title',e.target.value)}
           className="w-full px-3 py-2 border rounded" required />
          <input type="text" value={formData.department} onChange={e=>handleChange('department',e.target.value)}
           className="w-full px-3 py-2 border rounded" required />
          <textarea rows={4} value={formData.description} onChange={e=>handleChange('description',e.target.value)}
            className="w-full px-3 py-2 border rounded" required />
          <textarea rows={4} value={formData.requirements} onChange={e=>handleChange('requirements',e.target.value)}
            className="w-full px-3 py-2 border rounded" required />
          <input type="text" value={formData.location} onChange={e=>handleChange('location',e.target.value)}
           className="w-full px-3 py-2 border rounded" />
          <input type="text" value={formData.salaryRange} onChange={e=>handleChange('salaryRange',e.target.value)}
           className="w-full px-3 py-2 border rounded" />
          <div className="flex justify-end space-x-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
};

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
  const [departments, setDepartments] = useState<string[]>(["All Departments"]);
  const [selectedDepartment, setSelectedDepartment] = useState("All Departments");
  const [selectedStatus, setSelectedStatus] = useState("All Statuses");
  const [showPostJobModal, setShowPostJobModal] = useState(false);
  // Local notification message (e.g., "Job closed")
  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  useEffect(() => {
    fetchJobListings();
    fetchCandidates();
    fetchDepartments();
  }, []);

  const fetchJobListings = async () => {
    setLoading(true);
    try {
      const response = await new Promise<{ data: JobListing[] }>((resolve) =>
        setTimeout(
          () =>
            resolve({
              data: [
                {
                  id: 1,
                  title: "Software Engineer",
                  department: "IT",
                  status: "Open",
                  postedDate: "2023-05-15",
                  applicants: 12,
                  description: "Develop and maintain software applications. This includes designing, coding, testing, and debugging.",
                  requirements: "Proficiency in React, Node.js, and databases (e.g., PostgreSQL). Strong problem-solving skills and 3+ years of experience.",
                  location: "Harare, Zimbabwe",
                  salaryRange: "$30,000 - $50,000",
                },
                {
                  id: 2,
                  title: "HR Manager",
                  department: "HR",
                  status: "Closed",
                  postedDate: "2023-04-10",
                  applicants: 8,
                  description: "Manage human resources operations, including recruitment, onboarding, employee relations, and compliance.",
                  requirements: "5+ years of HR experience, strong communication skills, knowledge of labor laws.",
                  location: "Bulawayo, Zimbabwe",
                  salaryRange: "$40,000 - $60,000",
                },
                {
                  id: 3,
                  title: "Marketing Specialist",
                  department: "Marketing",
                  status: "Open",
                  postedDate: "2023-06-01",
                  applicants: 5,
                  description: "Plan and execute marketing campaigns across various channels, analyze market trends, and report on campaign performance.",
                  requirements: "Experience with digital marketing, creative thinking, excellent written and verbal communication.",
                  location: "Harare, Zimbabwe",
                  salaryRange: "$25,000 - $40,000",
                },
                {
                  id: 4,
                  title: "Finance Analyst",
                  department: "Finance",
                  status: "Open",
                  postedDate: "2023-06-15",
                  applicants: 7,
                  description: "Analyze financial data, prepare reports, develop financial models, and assist with budgeting and forecasting.",
                  requirements: "CFA or ACCA qualification, strong analytical skills, proficiency in Excel and financial software.",
                  location: "Harare, Zimbabwe",
                  salaryRange: "$35,000 - $55,000",
                },
                {
                  id: 5,
                  title: "Customer Support",
                  department: "Operations",
                  status: "Open",
                  postedDate: "2023-06-20",
                  applicants: 15,
                  description: "Provide excellent customer service through various channels, resolve customer inquiries and complaints.",
                  requirements: "Good communication skills, problem-solving abilities, patience, and a positive attitude.",
                  location: "Harare, Zimbabwe",
                  salaryRange: "$18,000 - $25,000",
                },
              ],
            }),
          1000
        )
      );
      setJobListings(response.data);
    } catch (error) {
      console.error("Error fetching job listings:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const response = await new Promise<{ data: Candidate[] }>((resolve) =>
        setTimeout(
          () =>
            resolve({
              data: [
                {
                  id: 1,
                  name: "Tendai Moyo",
                  job: "Software Engineer",
                  status: "Interview",
                  email: "tendai@example.com",
                  phone: "+263771234567",
                  appliedDate: "2023-06-10",
                },
                {
                  id: 2,
                  name: "Rufaro Chikosha",
                  job: "HR Manager",
                  status: "Hired",
                  email: "rufaro@example.com",
                  phone: "+263772345678",
                  appliedDate: "2023-05-20",
                },
                {
                  id: 3,
                  name: "Tatenda Ncube",
                  job: "Marketing Specialist",
                  status: "Pending",
                  email: "tatenda@example.com",
                  phone: "+263773456789",
                  appliedDate: "2023-06-05",
                },
                {
                  id: 4,
                  name: "Farai Mutizwa",
                  job: "Finance Analyst",
                  status: "Rejected",
                  email: "farai@example.com",
                  phone: "+263774567890",
                  appliedDate: "2023-06-18",
                },
                {
                  id: 5,
                  name: "Chiedza Mhike",
                  job: "Customer Support",
                  status: "Shortlisted",
                  email: "chiedza@example.com",
                  phone: "+263775678901",
                  appliedDate: "2023-06-22",
                },
              ],
            }),
          1000
        )
      );
      setCandidates(response.data);
    } catch (error) {
      console.error("Error fetching candidates:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    setDepartments([
      "All Departments",
      "IT",
      "HR",
      "Marketing",
      "Finance",
      "Operations",
    ]);
  };

  const handleSaveNewJob = (newJobData: Omit<JobListing, 'id' | 'applicants' | 'postedDate' | 'status'>) => {
    const newJob: JobListing = {
      ...newJobData,
      id: Date.now(),
      applicants: 0,
      postedDate: new Date().toISOString().slice(0, 10),
      status: "Open",
    };
    setJobListings((prevJobs) => [newJob, ...prevJobs]);
    if (!departments.includes(newJob.department)) {
      setDepartments((prevDepartments) => [...prevDepartments, newJob.department]);
    }
  };

  // Save edited job
  const handleSaveEditedJob = (updatedJob: JobListing) => {
    setJobListings(prev => prev.map(j => j.id === updatedJob.id ? updatedJob : j));
    setShowEditJobModal(false);
    setJobBeingEdited(null);
  };

  const handleEditJob = (jobId: number) => {
  const job = jobListings.find(j => j.id === jobId);
  if (job) {
    setJobBeingEdited(job);
    setShowEditJobModal(true);
  } else {
    alert(`Job with ID ${jobId} not found.`);
  }
};

  const handleViewJobDetails = (jobId: number) => {
    const job = jobListings.find(j => j.id === jobId);
    if (job) {
      setJobDetails(job);
      setShowDetailsModal(true);
    } else {
      alert(`Job with ID ${jobId} not found.`);
    }
  };



  const handleViewApplicants = (jobId: number) => {
    const job = jobListings.find(job => job.id === jobId);
    if (job) {
      setActiveTab("candidates");
      setSearchTerm(job.title); // Auto-filter candidates by job title
      setCurrentPage(1); // Reset pagination
    } else {
      alert(`Job with ID ${jobId} not found.`);
    }
  };

  const handleToggleJobStatus = (jobId: number, currentStatus: JobListing['status']) => {
    setJobListings((prevJobs) =>
      prevJobs.map((job) =>
        job.id === jobId
          ? { ...job, status: currentStatus === "Open" ? "Closed" : "Open" }
          : job
      )
    );
    setNotification(`Job ${currentStatus === "Open" ? "closed" : "opened"}`);
  };

  // --- End of activated functions ---

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

  const filteredCandidates = candidates.filter((candidate) => {
    const matchesSearch =
      candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      candidate.job.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      selectedStatus === "All Statuses" || candidate.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentJobs = filteredJobs.slice(indexOfFirstItem, indexOfLastItem);
  const currentCandidates = filteredCandidates.slice(
    indexOfFirstItem,
    indexOfLastItem
  );
  const totalPages = Math.ceil(
    activeTab === "jobs"
      ? filteredJobs.length / itemsPerPage
      : filteredCandidates.length / itemsPerPage
  );

  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  const exportToCSV = () => {
    const headers =
      activeTab === "jobs"
        ? ["Job Title", "Department", "Status", "Posted Date", "Applicants", "Description", "Requirements", "Location", "Salary Range"]
        : [
            "Candidate Name",
            "Applied Job",
            "Status",
            "Email",
            "Phone",
            "Applied Date",
          ];

    const data = activeTab === "jobs" ? filteredJobs : filteredCandidates;

    const csvContent = [
      headers.join(","),
      ...data.map((item) => {
        if (activeTab === "jobs") {
          const job = item as JobListing;
          return `"${job.title}","${job.department}","${job.status}","${job.postedDate}","${job.applicants}","${job.description.replace(/"/g, '""')}","${job.requirements.replace(/"/g, '""')}","${job.location}","${job.salaryRange}"`;
        } else {
          const candidate = item as Candidate;
          return `"${candidate.name}","${candidate.job}","${candidate.status}","${candidate.email}","${candidate.phone}","${candidate.appliedDate}"`;
        }
      }
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      `recruitment_${activeTab}_${new Date().toISOString().slice(0, 10)}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getStatusBadge = (status: JobListing['status'] | Candidate['status']) => {
    switch (status) {
      case "Open":
      case "Hired":
      case "Shortlisted":
        return (
          <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
            {status}
          </span>
        );
      case "Interview":
        return (
          <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
            {status}
          </span>
        );
      case "Pending":
        return (
          <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
            {status}
          </span>
        );
      case "Closed":
      case "Rejected":
        return (
          <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
            {status}
          </span>
        );
      default:
        return (
          <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="p-6">
      {notification && (
        <div className="mb-4 rounded-md bg-green-100 px-4 py-2 text-sm text-green-800 shadow">
          {notification}
          <p className="text-sm text-gray-500">
            {activeTab === "jobs"
              ? `${filteredJobs.length} ${
                  filteredJobs.length === 1 ? "job" : "jobs"
                } found`
              : `${filteredCandidates.length} ${
                  filteredCandidates.length === 1 ? "candidate" : "candidates"
                } found`}
          </p>
        </div>
      )}

      <div className="flex gap-3">
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition-colors"
            onClick={() => {
              if (activeTab === "jobs") {
                setShowPostJobModal(true);
              } else {
                alert("Add Candidate functionality goes here."); // Activated placeholder
              }
            }}
          >
            <Plus className="h-5 w-5" />
            {activeTab === "jobs" ? "Post a Job" : "Add Candidate"}
          </button>
        </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          className={`py-2 px-4 font-medium text-sm ${
            activeTab === "jobs"
              ? "text-blue-600 border-b-2 border-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => {
            setActiveTab("jobs");
            setCurrentPage(1);
          }}
        >
          Job Listings
        </button>
        <button
          className={`py-2 px-4 font-medium text-sm ${
            activeTab === "candidates"
              ? "text-blue-600 border-b-2 border-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => {
            setActiveTab("candidates");
            setCurrentPage(1);
          }}
        >
          Candidates
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 p-4">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder={
                activeTab === "jobs" ? "Search jobs..." : "Search candidates..."
              }
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
          {activeTab === "jobs" && (
            <div className="relative">
              <select
                className="appearance-none border rounded-lg px-4 py-2 pr-8 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={selectedDepartment}
                onChange={(e) => {
                  setSelectedDepartment(e.target.value);
                  setCurrentPage(1);
                }}
              >
                {departments.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            </div>
          )}
          <div className="relative">
            <select
              className="appearance-none border rounded-lg px-4 py-2 pr-8 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option>All Statuses</option>
              {activeTab === "jobs" ? (
                <>
                  <option>Open</option>
                  <option>Closed</option>
                </>
              ) : (
                <>
                  <option>Pending</option>
                  <option>Shortlisted</option>
                  <option>Interview</option>
                  <option>Hired</option>
                  <option>Rejected</option>
                </>
              )}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Content based on active tab */}
      {activeTab === "jobs" ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Job Title
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Department
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Posted Date
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Applicants
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Status
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
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
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className="font-medium">{job.applicants}</span>{" "}
                        applicants
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(job.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Menu
                          as="div"
                          className="relative inline-block text-left"
                        >
                          <div>
                            <MenuButton className="inline-flex justify-center w-full rounded-md px-2 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 focus:outline-none">
                              <MoreVertical className="h-5 w-5 text-gray-400" />
                            </MenuButton>
                          </div>
                          <MenuItems
                            as="div"
                            className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                          >
                            <MenuItem>
                              {({ active }) => (
                                <button
                                  onClick={() => handleViewJobDetails(job.id)}
                                  className={`${
                                    active
                                      ? "bg-gray-100 text-gray-900"
                                      : "text-gray-700"
                                  } group flex items-center w-full px-4 py-2 text-sm`}
                                >
                                  View Details
                                </button>
                              )}
                            </MenuItem>
                            <MenuItem>
                              {({ active }) => (
                                <button
                                  onClick={() => handleEditJob(job.id)}
                                  className={`${
                                    active
                                      ? "bg-gray-100 text-gray-900"
                                      : "text-gray-700"
                                  } group flex items-center w-full px-4 py-2 text-sm`}
                                >
                                  Edit Job
                                </button>
                              )}
                            </MenuItem>
                            <MenuItem>
                              {({ active }) => (
                                <button
                                  onClick={() => handleViewApplicants(job.id)}
                                  className={`${
                                    active
                                      ? "bg-gray-100 text-gray-900"
                                      : "text-gray-700"
                                  } group flex items-center w-full px-4 py-2 text-sm`}
                                >
                                  View Applicants
                                </button>
                              )}
                            </MenuItem>
                            <MenuItem>
                              {({ active }) => (
                                <button
                                  onClick={() => handleToggleJobStatus(job.id, job.status)}
                                  className={`${
                                    active
                                      ? "bg-gray-100 text-gray-900"
                                      : "text-gray-700"
                                  } group flex items-center w-full px-4 py-2 text-sm`}
                                >
                                  {job.status === "Open"
                                    ? "Close Job"
                                    : "Reopen Job"}
                                </button>
                              )}
                            </MenuItem>
                          </MenuItems>
                        </Menu>
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
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Candidate Name
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Applied Job
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Status
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Email
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Phone
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Applied Date
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center">
                      <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600" />
                      <p className="mt-2 text-sm text-gray-500">
                        Loading candidates...
                      </p>
                    </td>
                  </tr>
                ) : currentCandidates.length > 0 ? (
                  currentCandidates.map((candidate) => (
                    <tr key={candidate.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {candidate.name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {candidate.job}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(candidate.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {candidate.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {candidate.phone}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(candidate.appliedDate).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Menu
                          as="div"
                          className="relative inline-block text-left"
                        >
                          <div>
                            <MenuButton className="inline-flex justify-center w-full rounded-md px-2 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 focus:outline-none">
                              <MoreVertical className="h-5 w-5 text-gray-400" />
                            </MenuButton>
                          </div>
                          <MenuItems
                            as="div"
                            className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                          >
                            <MenuItem>
                              {({ active }) => (
                                <button
                                  onClick={() => alert(`Viewing profile for candidate: ${candidate.name} (ID: ${candidate.id})`)}
                                  className={`${
                                    active
                                      ? "bg-gray-100 text-gray-900"
                                      : "text-gray-700"
                                  } group flex items-center w-full px-4 py-2 text-sm`}
                                >
                                  View Profile
                                </button>
                              )}
                            </MenuItem>
                            <MenuItem>
                              {({ active }) => (
                                <button
                                  onClick={() => alert(`Updating status for candidate: ${candidate.name} (ID: ${candidate.id})`)}
                                  className={`${
                                    active
                                      ? "bg-gray-100 text-gray-900"
                                      : "text-gray-700"
                                  } group flex items-center w-full px-4 py-2 text-sm`}
                                >
                                  Update Status
                                </button>
                              )}
                            </MenuItem>
                            <MenuItem>
                              {({ active }) => (
                                <button
                                  onClick={() => alert(`Scheduling interview for candidate: ${candidate.name} (ID: ${candidate.id})`)}
                                  className={`${
                                    active
                                      ? "bg-gray-100 text-gray-900"
                                      : "text-gray-700"
                                  } group flex items-center w-full px-4 py-2 text-sm`}
                                >
                                  Schedule Interview
                                </button>
                              )}
                            </MenuItem>
                          </MenuItems>
                        </Menu>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center">
                      <div className="flex flex-col items-center justify-center">
                        <User className="h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">
                          No candidates found
                        </h3>
                        <p className="mt-1 text-sm text-gray-500">
                          {searchTerm
                            ? "Try adjusting your search or filter"
                            : "Add new candidates or they will appear after applying for jobs"}
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {filteredCandidates.length > itemsPerPage && (
            <div className="px-6 py-4 border-t flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Showing{" "}
                <span className="font-medium">{indexOfFirstItem + 1}</span> to{" "}
                <span className="font-medium">
                  {Math.min(indexOfLastItem, filteredCandidates.length)}
                </span>{" "}
                of <span className="font-medium">{filteredCandidates.length}</span>{" "}
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
      )}

      {/* Job Details Modal */}
      <JobDetailsModal
        isOpen={showDetailsModal}
        job={jobDetails}
        onClose={() => setShowDetailsModal(false)}
      />

      {/* Edit Job Modal */}
      <EditJobModal
        isOpen={showEditJobModal}
        job={jobBeingEdited}
        onClose={() => {
          setShowEditJobModal(false);
          setJobBeingEdited(null);
        }}
        onSave={handleSaveEditedJob}
      />

      {/* Post Job Modal */}
      <PostJobModal
        isOpen={showPostJobModal}
        onClose={() => setShowPostJobModal(false)}
        onSave={handleSaveNewJob}
      />
    </div>
  );
};

export default Recruitment;