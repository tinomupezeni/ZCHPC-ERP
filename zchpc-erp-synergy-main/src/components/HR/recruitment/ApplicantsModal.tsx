import React, { useState, useEffect } from "react";
import {
  X,
  Loader,
  User,
  Mail,
  Phone,
  FileText,
  Download,
  Calendar,
  ChevronDown,
  CheckCircle,
  XCircle,
  Clock,
  Users,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";
import { getApplications, updateApplicationStatus } from "@/services/jobs.services";

interface Candidate {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  resume: string | null;
  notes: string | null;
}

interface Application {
  id: number;
  job: number;
  job_title: string;
  candidate: Candidate;
  applied_on: string;
  status: string;
}

interface ApplicantsModalProps {
  isOpen: boolean;
  job: { id: number; title: string; department: string } | null;
  onClose: () => void;
}

const STATUS_OPTIONS = [
  { value: "Pending", label: "Pending", color: "bg-yellow-100 text-yellow-700", icon: Clock },
  { value: "Shortlisted", label: "Shortlisted", color: "bg-blue-100 text-blue-700", icon: CheckCircle },
  { value: "Interview", label: "Interview", color: "bg-purple-100 text-purple-700", icon: Users },
  { value: "Offered", label: "Offered", color: "bg-green-100 text-green-700", icon: CheckCircle },
  { value: "Hired", label: "Hired", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle },
  { value: "Rejected", label: "Rejected", color: "bg-red-100 text-red-700", icon: XCircle },
];

const ApplicantsModal: React.FC<ApplicantsModalProps> = ({ isOpen, job, onClose }) => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [selectedApplicant, setSelectedApplicant] = useState<Application | null>(null);

  useEffect(() => {
    if (isOpen && job) {
      fetchApplications();
    }
  }, [isOpen, job]);

  const fetchApplications = async () => {
    if (!job) return;
    setLoading(true);
    try {
      const data = await getApplications(job.id);
      setApplications(data);
    } catch (error) {
      console.error("Failed to fetch applications:", error);
      toast.error("Failed to load applicants");
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (applicationId: number, newStatus: string) => {
    setUpdatingId(applicationId);
    try {
      await updateApplicationStatus(applicationId, newStatus);
      setApplications((prev) =>
        prev.map((app) =>
          app.id === applicationId ? { ...app, status: newStatus } : app
        )
      );
      toast.success(`Status updated to ${newStatus}`);
    } catch (error) {
      toast.error("Failed to update status");
    } finally {
      setUpdatingId(null);
    }
  };

  const getStatusConfig = (status: string) => {
    return STATUS_OPTIONS.find((s) => s.value === status) || STATUS_OPTIONS[0];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative w-full max-w-4xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="px-6 py-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Users className="h-5 w-5" />
                Job Applicants
              </h2>
              <p className="text-blue-100 text-sm mt-1">
                {job?.title} - {job?.department}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-blue-500 rounded-full transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Applicants List */}
          <div className={`${selectedApplicant ? 'w-1/2' : 'w-full'} border-r overflow-y-auto`}>
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : applications.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <Users className="h-12 w-12 mb-3 text-gray-300" />
                <p className="text-lg font-medium">No applicants yet</p>
                <p className="text-sm">Applications will appear here when candidates apply</p>
              </div>
            ) : (
              <div className="divide-y">
                {applications.map((app) => {
                  const statusConfig = getStatusConfig(app.status);
                  const StatusIcon = statusConfig.icon;

                  return (
                    <div
                      key={app.id}
                      onClick={() => setSelectedApplicant(app)}
                      className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                        selectedApplicant?.id === app.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold">
                            {app.candidate.first_name[0]}
                            {app.candidate.last_name[0]}
                          </div>
                          <div>
                            <h3 className="font-medium text-gray-900">
                              {app.candidate.first_name} {app.candidate.last_name}
                            </h3>
                            <p className="text-sm text-gray-500 flex items-center gap-1">
                              <Mail className="h-3 w-3" />
                              {app.candidate.email}
                            </p>
                            <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              Applied {formatDate(app.applied_on)}
                            </p>
                          </div>
                        </div>

                        <div className="flex flex-col items-end gap-2">
                          {/* Status Badge */}
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.color}`}>
                            <StatusIcon className="h-3 w-3" />
                            {app.status}
                          </span>

                          {/* Resume indicator */}
                          {app.candidate.resume && (
                            <span className="text-xs text-green-600 flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              Resume attached
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Selected Applicant Details */}
          {selectedApplicant && (
            <div className="w-1/2 overflow-y-auto bg-gray-50">
              <div className="p-6 space-y-6">
                {/* Applicant Header */}
                <div className="bg-white rounded-xl p-6 shadow-sm border">
                  <div className="flex items-center gap-4">
                    <div className="h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-2xl font-bold">
                      {selectedApplicant.candidate.first_name[0]}
                      {selectedApplicant.candidate.last_name[0]}
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">
                        {selectedApplicant.candidate.first_name} {selectedApplicant.candidate.last_name}
                      </h3>
                      <p className="text-gray-500">Applicant</p>
                    </div>
                  </div>
                </div>

                {/* Contact Info */}
                <div className="bg-white rounded-xl p-6 shadow-sm border space-y-4">
                  <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                    <User className="h-4 w-4 text-blue-600" />
                    Contact Information
                  </h4>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 text-sm">
                      <Mail className="h-4 w-4 text-gray-400" />
                      <a
                        href={`mailto:${selectedApplicant.candidate.email}`}
                        className="text-blue-600 hover:underline"
                      >
                        {selectedApplicant.candidate.email}
                      </a>
                    </div>
                    {selectedApplicant.candidate.phone && (
                      <div className="flex items-center gap-3 text-sm">
                        <Phone className="h-4 w-4 text-gray-400" />
                        <a
                          href={`tel:${selectedApplicant.candidate.phone}`}
                          className="text-gray-700 hover:text-blue-600"
                        >
                          {selectedApplicant.candidate.phone}
                        </a>
                      </div>
                    )}
                    <div className="flex items-center gap-3 text-sm">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-700">
                        Applied on {formatDate(selectedApplicant.applied_on)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Status Update */}
                <div className="bg-white rounded-xl p-6 shadow-sm border space-y-4">
                  <h4 className="font-semibold text-gray-800">Update Status</h4>
                  <div className="relative">
                    <select
                      value={selectedApplicant.status}
                      onChange={(e) => handleStatusChange(selectedApplicant.id, e.target.value)}
                      disabled={updatingId === selectedApplicant.id}
                      className="w-full p-3 border rounded-lg bg-white focus:ring-2 focus:ring-blue-500 appearance-none pr-10"
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <option key={status.value} value={status.value}>
                          {status.label}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
                    {updatingId === selectedApplicant.id && (
                      <Loader className="absolute right-10 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-blue-600" />
                    )}
                  </div>
                </div>

                {/* Resume/Documents */}
                <div className="bg-white rounded-xl p-6 shadow-sm border space-y-4">
                  <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                    <FileText className="h-4 w-4 text-blue-600" />
                    Documents
                  </h4>
                  {selectedApplicant.candidate.resume ? (
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-red-100 flex items-center justify-center">
                          <FileText className="h-5 w-5 text-red-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Resume</p>
                          <p className="text-xs text-gray-500">PDF Document</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <a
                          href={selectedApplicant.candidate.resume}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="View"
                        >
                          <ExternalLink className="h-5 w-5" />
                        </a>
                        <a
                          href={selectedApplicant.candidate.resume}
                          download
                          className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                          title="Download"
                        >
                          <Download className="h-5 w-5" />
                        </a>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <FileText className="h-10 w-10 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">No resume uploaded</p>
                    </div>
                  )}
                </div>

                {/* Notes */}
                {selectedApplicant.candidate.notes && (
                  <div className="bg-white rounded-xl p-6 shadow-sm border space-y-4">
                    <h4 className="font-semibold text-gray-800">Notes</h4>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {selectedApplicant.candidate.notes}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Stats */}
        <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-between">
          <div className="flex gap-6 text-sm">
            <span className="text-gray-600">
              Total: <span className="font-semibold">{applications.length}</span>
            </span>
            {STATUS_OPTIONS.slice(0, 4).map((status) => {
              const count = applications.filter((a) => a.status === status.value).length;
              return count > 0 ? (
                <span key={status.value} className={`${status.color} px-2 py-0.5 rounded-full`}>
                  {status.label}: {count}
                </span>
              ) : null;
            })}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApplicantsModal;
