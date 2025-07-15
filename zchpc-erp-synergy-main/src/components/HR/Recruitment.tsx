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
  X, // Added for close icon in modal
} from "lucide-react";
import { Menu, MenuButton, MenuItem } from "@headlessui/react";

// PostJobModal Component
const PostJobModal = ({ isOpen, onClose, onSave }) => {
  const [jobTitle, setJobTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [location, setLocation] = useState("");
  const [salaryRange, setSalaryRange] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      id: Date.now(), // Simple unique ID generation
      title: jobTitle,
      department,
      description,
      requirements,
      location,
      salaryRange,
      status: "Open",
      postedDate: new Date().toISOString().slice(0, 10),
      applicants: 0,
    });
    // Clear form fields
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
              rows="4"
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
              rows="4"
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

const Recruitment = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [jobListings, setJobListings] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [activeTab, setActiveTab] = useState("jobs");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);
  const [departments, setDepartments] = useState(["All Departments"]);
  const [selectedDepartment, setSelectedDepartment] = useState("All Departments");
  const [selectedStatus, setSelectedStatus] = useState("All Statuses");
  const [showJobEditOptions, setShowJobEditOptions] = useState(false);
  const [showPostJobModal, setShowPostJobModal] = useState(false); // New state for modal

  useEffect(() => {
    fetchJobListings();
    fetchCandidates();
    fetchDepartments();
  }, []);

  const fetchJobListings = async () => {
    setLoading(true);
    try {
      // Simulated API call with more realistic data
      const response = await new Promise((resolve) =>
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
                  description: "Develop and maintain software applications.",
                  requirements: "Proficiency in React, Node.js, and databases.",
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
                  description: "Manage human resources operations.",
                  requirements: "5+ years of HR experience, strong communication skills.",
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
                  description: "Plan and execute marketing campaigns.",
                  requirements: "Experience with digital marketing, creative thinking.",
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
                  description: "Analyze financial data and prepare reports.",
                  requirements: "CFA or ACCA qualification, strong analytical skills.",
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
                  description: "Provide excellent customer service.",
                  requirements: "Good communication skills, problem-solving abilities.",
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
      // Simulated API call with more realistic data
      const response = await new Promise((resolve) =>
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
    // Simulated department fetch
    setDepartments([
      "All Departments",
      "IT",
      "HR",
      "Marketing",
      "Finance",
      "Operations",
    ]);
  };

  const handleSaveNewJob = (newJob) => {
    setJobListings((prevJobs) => [newJob, ...prevJobs]);
    // Also update departments if the new job's department is not already in the list
    if (!departments.includes(newJob.department)) {
      setDepartments((prevDepartments) => [...prevDepartments, newJob.department]);
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

  const filteredCandidates = candidates.filter((candidate) => {
    const matchesSearch =
      candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      candidate.job.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      selectedStatus === "All Statuses" || candidate.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  // Pagination logic
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

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

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
      ...data.map((item) =>
        activeTab === "jobs"
          ? `"${item.title}","${item.department}","${item.status}","${item.postedDate}","${item.applicants}","${item.description}","${item.requirements}","${item.location}","${item.salaryRange}"`
          : `"${item.name}","${item.job}","${item.status}","${item.email}","${item.phone}","${item.appliedDate}"`
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
  };

  const getStatusBadge = (status) => {
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
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            Recruitment Dashboard
          </h1>
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
                setShowPostJobModal(true); // Open the modal for posting a job
              } else {
                console.log("Add Candidate functionality goes here."); // Placeholder for adding candidate
              }
            }}
          >
            <Plus className="h-5 w-5" />
            {activeTab === "jobs" ? "Post a Job" : "Add Candidate"}
          </button>
        </div>
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
                    <td colSpan="6" className="px-6 py-8 text-center">
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
                          <Menu.Items
                            as="div"
                            className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                          >
                            <MenuItem>
                              {({ active }) => (
                                <button
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
                          </Menu.Items>
                        </Menu>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-6 py-8 text-center">
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
                    Candidate
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
                    Contact
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    Applied Date
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
                    <td colSpan="6" className="px-6 py-8 text-center">
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
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                            {candidate.name
                              .split(" ")
                              .map((n) => n[0])
                              .join("")}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {candidate.name}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {candidate.job}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 flex items-center gap-1">
                          <Mail className="h-4 w-4" /> {candidate.email}
                        </div>
                        <div className="text-sm text-gray-500 flex items-center gap-1">
                          <Phone className="h-4 w-4" /> {candidate.phone}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(candidate.appliedDate).toLocaleDateString(
                          "en-US",
                          {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          }
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(candidate.status)}
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
                          <Menu.Items
                            as="div"
                            className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                          >
                            <MenuItem>
                              {({ active }) => (
                                <button
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
                          </Menu.Items>
                        </Menu>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-6 py-8 text-center">
                      <div className="flex flex-col items-center justify-center">
                        <User className="h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">
                          No candidates found
                        </h3>
                        <p className="mt-1 text-sm text-gray-500">
                          {searchTerm
                            ? "Try adjusting your search or filter"
                            : "Add new candidates or wait for applications"}
                        </p>
                        {!searchTerm && (
                          <button
                            type="button"
                            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none"
                            onClick={() => console.log("Add Candidate")}
                          >
                            <Plus className="-ml-1 mr-2 h-5 w-5" />
                            Add Candidate
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
          {filteredCandidates.length > itemsPerPage && (
            <div className="px-6 py-4 border-t flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Showing{" "}
                <span className="font-medium">{indexOfFirstItem + 1}</span> to{" "}
                <span className="font-medium">
                  {Math.min(indexOfLastItem, filteredCandidates.length)}
                </span>{" "}
                of{" "}
                <span className="font-medium">{filteredCandidates.length}</span>{" "}
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