import React, { useState, ChangeEvent, FormEvent, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { Award, Download, Search, BadgeCheck, Plus, Edit2, Trash2, RotateCw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { format, parseISO, isValid } from "date-fns";
import Modal from "@/components/ui/Modal";
import Server from "@/services/Server";
import { useToast } from "@/hooks/use-toast";

interface Certification {
  id: number;
  employee: string;
  program: string;
  issue_date: string; // Changed to match Django model
  expiry_date: string; // Changed to match Django model
  status: "Valid" | "Expired" | "Pending";
}

interface CertificationFormValues {
  employee: string;
  program: string;
  issue_date: string;
  expiry_date: string;
  status: "Valid" | "Expired" | "Pending";
}

const statusConfig = {
  Valid: {
    color: "bg-green-100 text-green-800 hover:bg-green-200",
    icon: <BadgeCheck className="w-4 h-4 mr-1" />,
  },
  Expired: {
    color: "bg-red-100 text-red-800 hover:bg-red-200",
    icon: <BadgeCheck className="w-4 h-4 mr-1 opacity-50" />,
  },
  Pending: {
    color: "bg-yellow-100 text-yellow-800 hover:bg-yellow-200",
    icon: <BadgeCheck className="w-4 h-4 mr-1 animate-pulse" />,
  },
};

export default function TrainingCertificationsPage() {
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit" | "delete" | null>(null);
  const [currentCertification, setCurrentCertification] = useState<Certification | null>(null);
  const [formValues, setFormValues] = useState<CertificationFormValues>({
    employee: "",
    program: "",
    issue_date: "",
    expiry_date: "",
    status: "Valid",
  });
  const { toast } = useToast();

  // Fetch certifications from backend
  useEffect(() => {
    const fetchCertifications = async () => {
      try {
        setIsLoading(true);
        const response = await Server.getTrainingCertifications();
        setCertifications(response.data);
      } catch (error) {
        toast({
          title:"Failed to load certifications",
          description: "There was an error fetching the certifications. Please try again later.",
        });
        console.error("Error fetching certifications:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCertifications();
  }, []);

  // Filter certifications based on search term
  const filteredCertifications = certifications.filter(cert =>
    cert.employee.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cert.program.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Modal handlers
  const openAddModal = () => {
    setFormValues({
      employee: "",
      program: "",
      issue_date: "",
      expiry_date: "",
      status: "Valid",
    });
    setCurrentCertification(null);
    setModalMode("add");
    setModalOpen(true);
  };

  const openEditModal = (id: number) => {
    const certification = certifications.find((c) => c.id === id);
    if (!certification) return;
    
    setFormValues({
      employee: certification.employee,
      program: certification.program,
      issue_date: certification.issue_date,
      expiry_date: certification.expiry_date,
      status: certification.status,
    });
    setCurrentCertification(certification);
    setModalMode("edit");
    setModalOpen(true);
  };

  const openDeleteModal = (id: number) => {
    const certification = certifications.find((c) => c.id === id);
    if (!certification) return;
    setCurrentCertification(certification);
    setModalMode("delete");
    setModalOpen(true);
  };

  // Form input change handler
  const onChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormValues((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Form submit handler
  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!formValues.employee.trim() || !formValues.program.trim() || 
        !formValues.issue_date.trim() || !formValues.expiry_date.trim()) {
      toast({
        title:"Please fill in all required fields",
        description: "All fields marked with * are required.",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      if (modalMode === "add") {
        const response = await Server.addTrainingCertification(formValues);
        setCertifications([...certifications, response.data]);
        toast({
          title:"Certificate issued successfully",
          description: "The training certificate has been issued successfully.",});
      } else if (modalMode === "edit" && currentCertification) {
        const response = await Server.updateTrainingCertification(currentCertification.id, formValues);
        setCertifications(certifications.map(c => 
          c.id === currentCertification.id ? response.data : c
        ));
        toast({
          title: "Certificate updated successfully",
          description: "The training certificate has been updated successfully.",
        });
      }
      setModalOpen(false);
    } catch (error) {
      toast({
        title:"Failed to save certificate",
        description: "There was an error saving the certificate. Please try again later.",
      });
      console.error("Error saving certificate:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Confirm delete certification
  const confirmDelete = async () => {
    if (!currentCertification) return;

    setIsSubmitting(true);
    try {
      await Server.deleteTrainingCertification(currentCertification.id);
      setCertifications(certifications.filter(c => c.id !== currentCertification.id));
      toast({
        title:"Certificate deleted successfully",
        description: "The training certificate has been deleted successfully.",
      });
      setModalOpen(false);
    } catch (error) {
      toast({
        title:"Failed to delete certificate",
        description: "There was an error deleting the certificate. Please try again later.",
      });
      console.error("Error deleting certificate:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = parseISO(dateStr);
    return isValid(date) ? format(date, "MMM dd, yyyy") : dateStr;
  };

  const handleDownloadCertificate = (id: number) => {
    console.log("Downloading certificate for ID:", id);
    // You would typically call a Server.downloadCertificate(id) method here
    toast({
      title:"Download functionality would be implemented here",
      description: "This is a placeholder for the download functionality.",
    });
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Award className="w-6 h-6 text-blue-600" />
            Training Certifications
          </h1>
          <div className="animate-pulse h-10 w-40 bg-gray-200 rounded-md"></div>
        </div>
        <Separator />
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse h-16 bg-gray-200 rounded-md"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Award className="w-6 h-6 text-blue-600" />
          Training Certifications
        </h1>
        
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="search"
              placeholder="Search Employee or Program"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <Button 
            onClick={openAddModal} 
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>Issue Certificate</span>
          </Button>
        </div>
      </div>

      <Separator />

      {filteredCertifications.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 space-y-4 text-center">
          <Award className="w-12 h-12 text-gray-400" />
          <p className="text-lg font-medium text-gray-500">
            {searchTerm ? "No matching certifications found" : "No certifications issued yet"}
          </p>
          {!searchTerm && (
            <Button onClick={openAddModal} className="mt-4">
              <Plus className="w-4 h-4 mr-2" />
              Issue Your First Certificate
            </Button>
          )}
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader className="bg-gray-50">
              <TableRow>
                <TableHead className="w-[200px]">Employee</TableHead>
                <TableHead>Program</TableHead>
                <TableHead>Issue Date</TableHead>
                <TableHead>Expiry Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCertifications.map((cert) => (
                <TableRow key={cert.id}>
                  <TableCell className="font-medium flex items-center gap-2">
                    <Award className="w-5 h-5 text-blue-500" />
                    {cert.employee}
                  </TableCell>
                  <TableCell>{cert.program}</TableCell>
                  <TableCell>{formatDate(cert.issue_date)}</TableCell>
                  <TableCell>{formatDate(cert.expiry_date)}</TableCell>
                  <TableCell>
                    <Badge className={`${statusConfig[cert.status].color} flex items-center`}>
                      {statusConfig[cert.status].icon}
                      {cert.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditModal(cert.id)}
                      className="h-8"
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openDeleteModal(cert.id)}
                      className="h-8"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadCertificate(cert.id)}
                      className="h-8 flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Add/Edit Certification Modal */}
      <Modal
        isOpen={modalOpen && (modalMode === "add" || modalMode === "edit")}
        onClose={() => setModalOpen(false)}
        title={
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-blue-600" />
            <span>{modalMode === "add" ? "Issue New Certificate" : "Edit Certificate"}</span>
          </div>
        }
        footer={
          <div className="flex justify-end gap-3">
            <Button 
              variant="outline" 
              onClick={() => setModalOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button 
              form="certification-form" 
              type="submit"
              className="bg-blue-600 hover:bg-blue-700"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <RotateCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <BadgeCheck className="w-4 h-4 mr-2" />
              )}
              {modalMode === "add" ? "Issue Certificate" : "Update Certificate"}
            </Button>
          </div>
        }
      >
        <form id="certification-form" onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="employee" className="block font-medium">
              Employee <span className="text-red-500">*</span>
            </label>
            <Input
              id="employee"
              name="employee"
              value={formValues.employee}
              onChange={onChange}
              placeholder="Enter employee name"
              required
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="program" className="block font-medium">
              Program <span className="text-red-500">*</span>
            </label>
            <Input
              id="program"
              name="program"
              value={formValues.program}
              onChange={onChange}
              placeholder="Enter program name"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="issue_date" className="block font-medium">
                Issue Date <span className="text-red-500">*</span>
              </label>
              <Input
                id="issue_date"
                name="issue_date"
                type="date"
                value={formValues.issue_date}
                onChange={onChange}
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="expiry_date" className="block font-medium">
                Expiry Date <span className="text-red-500">*</span>
              </label>
              <Input
                id="expiry_date"
                name="expiry_date"
                type="date"
                value={formValues.expiry_date}
                onChange={onChange}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="status" className="block font-medium">
              Status <span className="text-red-500">*</span>
            </label>
            <select
              id="status"
              name="status"
              value={formValues.status}
              onChange={onChange}
              className="w-full border rounded-md px-3 py-2 text-sm"
              required
            >
              <option value="Valid">Valid</option>
              <option value="Expired">Expired</option>
              <option value="Pending">Pending</option>
            </select>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={modalOpen && modalMode === "delete"}
        onClose={() => setModalOpen(false)}
        title="Confirm Deletion"
        footer={
          <div className="flex justify-end gap-3">
            <Button 
              variant="outline" 
              onClick={() => setModalOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive"
              onClick={confirmDelete}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <RotateCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Delete
            </Button>
          </div>
        }
      >
        {currentCertification && (
          <div className="space-y-4">
            <p>Are you sure you want to delete the certificate for <strong>{currentCertification.employee}</strong>?</p>
            <p className="text-sm text-gray-600">
              Program: {currentCertification.program} (Issued: {formatDate(currentCertification.issue_date)})
            </p>
            <p className="text-red-500">This action cannot be undone.</p>
          </div>
        )}
      </Modal>
    </div>
  );
}