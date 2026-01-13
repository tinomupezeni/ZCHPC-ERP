// components/recruitment/ViewJobModal.tsx
import React from "react";
import {
  X,
  Building,
  MapPin,
  DollarSign,
  Mail,
  Target,
  GraduationCap,
  ShieldCheck,
  Users,
  Calendar,
  FileText,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { PostJobModalProps } from "@/types/postJob";

const ViewJobModal: React.FC<PostJobModalProps> = ({ isOpen, job, onClose }) => {
  if (!isOpen || !job) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Open":
        return "bg-green-100 text-green-800 border-green-300";
      case "Closed":
        return "bg-red-100 text-red-800 border-red-300";
      case "Draft":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "Pending":
        return "bg-blue-100 text-blue-800 border-blue-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col animate-in zoom-in duration-300">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center bg-gradient-to-r from-blue-600 to-blue-700 text-white sticky top-0 z-10 rounded-t-2xl">
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">{job.title}</h2>
                <div className="flex items-center gap-4 mt-2">
                  <div className="flex items-center gap-1 text-blue-100">
                    <Building className="h-4 w-4" />
                    <span className="text-sm">{job.department}</span>
                  </div>
                  {job.position && (
                    <div className="flex items-center gap-1 text-blue-100">
                      <FileText className="h-4 w-4" />
                      <span className="text-sm">{job.position}</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                    job.status
                  )}`}
                >
                  {job.status}
                </span>
                {job.isInternal && (
                  <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium border border-purple-300 flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    Internal
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="ml-4 p-2 hover:bg-blue-500 rounded-full text-blue-100 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <div className="text-2xl font-bold text-blue-600">
                  {job.applicants || 0}
                </div>
                <div className="text-sm text-gray-500">Applicants</div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <div className="text-2xl font-bold text-green-600">
                  {job.closingDate
                    ? new Date(job.closingDate).toLocaleDateString()
                    : "No date"}
                </div>
                <div className="text-sm text-gray-500">Closing Date</div>
              </div>
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <div className="text-2xl font-bold text-purple-600">
                  {job.postedDate
                    ? new Date(job.postedDate).toLocaleDateString()
                    : "N/A"}
                </div>
                <div className="text-sm text-gray-500">Posted Date</div>
              </div>
            </div>

            {/* Job Details Grid */}
            <div className="grid grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-6">
                {/* Location & Salary */}
                <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
                  <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-blue-600" />
                    Location & Compensation
                  </h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-700">{job.location}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-700">{job.salaryRange}</span>
                    </div>
                  </div>
                </div>

                {/* Reports To */}
                {job.reportsTo && (
                  <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
                    <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <Users className="h-4 w-4 text-blue-600" />
                      Reporting Line
                    </h3>
                    <div className="flex items-center gap-2">
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-700">{job.reportsTo}</span>
                    </div>
                  </div>
                )}

                {/* Competencies */}
                {job.competencies && job.competencies.length > 0 && (
                  <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
                    <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 text-green-600" />
                      Core Competencies
                    </h3>
                    <div className="space-y-2">
                      {job.competencies.map((competency, index) => (
                        <div
                          key={index}
                          className="flex items-start gap-2 text-sm"
                        >
                          <div className="h-1.5 w-1.5 rounded-full bg-green-400 mt-2 flex-shrink-0" />
                          <span className="text-gray-700">{competency}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column */}
              <div className="space-y-6">
                {/* Responsibilities */}
                {job.responsibilities && job.responsibilities.length > 0 && (
                  <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
                    <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <Target className="h-4 w-4 text-orange-600" />
                      Key Responsibilities
                    </h3>
                    <div className="space-y-3">
                      {job.responsibilities.map((responsibility, index) => (
                        <div
                          key={index}
                          className="flex gap-3 text-sm bg-orange-50 p-3 rounded-lg border border-orange-100"
                        >
                          <span className="text-orange-600 font-medium min-w-6">
                            {index + 1}.
                          </span>
                          <span className="text-gray-700">
                            {responsibility}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Qualifications */}
                {job.qualifications && job.qualifications.length > 0 && (
                  <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
                    <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <GraduationCap className="h-4 w-4 text-purple-600" />
                      Qualifications & Requirements
                    </h3>
                    <div className="space-y-2">
                      {job.qualifications.map((qualification, index) => (
                        <div
                          key={index}
                          className="flex items-start gap-2 text-sm"
                        >
                          <div className="h-1.5 w-1.5 rounded-full bg-purple-400 mt-2 flex-shrink-0" />
                          <span className="text-gray-700">{qualification}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Application Details - Full Width */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 mt-6">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Mail className="h-4 w-4 text-cyan-600" />
                Application Details
              </h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Contact Information
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-gray-500" />
                      <a
                        href={`mailto:${job.contactEmail}`}
                        className="text-blue-600 hover:underline"
                      >
                        {job.contactEmail}
                      </a>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Application Instructions
                  </h4>
                  <p className="text-gray-700 text-sm bg-gray-50 p-3 rounded-lg border">
                    {job.applicationProcess || "No specific instructions provided."}
                  </p>
                </div>
              </div>
            </div>

            {/* Timeline/Status */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Calendar className="h-4 w-4 text-indigo-600" />
                Timeline
              </h3>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-500">Posted</div>
                  <div className="font-medium">
                    {new Date(job.postedDate).toLocaleDateString()}
                  </div>
                </div>
                <div className="h-px flex-1 bg-gray-300 mx-4" />
                <div>
                  <div className="text-sm text-gray-500">Closes</div>
                  <div className="font-medium">
                    {job.closingDate
                      ? new Date(job.closingDate).toLocaleDateString()
                      : "Open until filled"}
                  </div>
                </div>
                <div className="h-px flex-1 bg-gray-300 mx-4" />
                <div>
                  <div className="text-sm text-gray-500">Status</div>
                  <div
                    className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                      job.status
                    )}`}
                  >
                    {job.status}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-white flex justify-between items-center sticky bottom-0 rounded-b-2xl">
          <div className="text-sm text-gray-500">
            Job ID: <span className="font-medium">{job.id}</span>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 font-medium hover:bg-gray-100 rounded-lg transition-colors"
            >
              Close
            </button>
            {job.status === "Open" && (
              <button
                type="button"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                View Applicants
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ViewJobModal;