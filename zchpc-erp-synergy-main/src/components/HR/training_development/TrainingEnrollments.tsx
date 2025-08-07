import { useState, ChangeEvent, FormEvent, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ClipboardList, Plus, User, BookOpen, Calendar, Pencil, Trash2 } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import Modal from "@/components/ui/Modal";
import Server from "@/server/Server";
import { useToast } from "@/hooks/use-toast";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

interface Enrollment {
  id: number;
  employee: string;
  program: string;
  session_date: string;
  status: "Enrolled" | "In Progress" | "Completed";
}

const StatusBadge = ({ status }: { status: Enrollment["status"] }) => {
  const statusConfig = {
    Enrolled: { icon: <Calendar className="w-3 h-3 mr-1" />, color: "bg-blue-100 text-blue-800" },
    "In Progress": { icon: <Pencil className="w-3 h-3 mr-1 animate-spin" />, color: "bg-yellow-100 text-yellow-800" },
    Completed: { icon: <Plus className="w-3 h-3 mr-1" />, color: "bg-green-100 text-green-800" },
  };

  return (
    <Badge className={`${statusConfig[status].color} flex items-center`}>
      {statusConfig[status].icon}
      {status}
    </Badge>
  );
};

export default function TrainingEnrollmentsPage() {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit" | "delete" | null>(null);
  const [currentEnrollment, setCurrentEnrollment] = useState<Enrollment | null>(null);
  const [formValues, setFormValues] = useState<Omit<Enrollment, "id">>({
    employee: "",
    program: "",
    session_date: "",
    status: "Enrolled",
  });

  const { toast } = useToast();

  // Fetch enrollments from backend
  useEffect(() => {
    const fetchEnrollments = async () => {
      try {
        setIsLoading(true);
        const response = await Server.getTrainingEnrollments();
        setEnrollments(response.data);
      } catch (error) {
        toast({
          title: "Failed to load enrollments",
          description: "There was an error fetching the training enrollments.",
        });
        console.error("Error fetching enrollments:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEnrollments();
  }, []);

  // Modal handlers
  const openAddModal = () => {
    setFormValues({ employee: "", program: "", session_date: "", status: "Enrolled" });
    setCurrentEnrollment(null);
    setModalMode("add");
    setModalOpen(true);
  };

  const openEditModal = (id: number) => {
    const enrollment = enrollments.find((e) => e.id === id);
    if (!enrollment) return;
    setFormValues({
      employee: enrollment.employee,
      program: enrollment.program,
      session_date: enrollment.session_date,
      status: enrollment.status,
    });
    setCurrentEnrollment(enrollment);
    setModalMode("edit");
    setModalOpen(true);
  };

  const openDeleteModal = (id: number) => {
    const enrollment = enrollments.find((e) => e.id === id);
    if (!enrollment) return;
    setCurrentEnrollment(enrollment);
    setModalMode("delete");
    setModalOpen(true);
  };

  // Form input change handler
  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormValues((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Form submission handler
  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!formValues.employee.trim() || !formValues.program.trim() || !formValues.session_date.trim()) {
      toast({
        title: "Please fill in all required fields",
        description: "All fields are required to add or edit an enrollment.",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      if (modalMode === "add") {
        const response = await Server.addTrainingEnrollment(formValues);
        setEnrollments([...enrollments, response.data]);
        toast({
          title:"Enrollment added successfully",
          description: "The new enrollment has been created.",});
      } else if (modalMode === "edit" && currentEnrollment) {
        const response = await Server.updateTrainingEnrollment(currentEnrollment.id, formValues);
        setEnrollments(enrollments.map(e => e.id === currentEnrollment.id ? response.data : e));
        toast({
          title:"Enrollment updated successfully",
          description: "The enrollment has been updated.",});
      }
      setModalOpen(false);
    } catch (error) {
      toast({
        title:"Failed to save enrollment",
        description: "There was an error saving the enrollment.",});
      console.error("Error saving enrollment:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Confirm delete
  const confirmDelete = async () => {
    if (!currentEnrollment) return;

    setIsSubmitting(true);
    try {
      await Server.deleteTrainingEnrollment(currentEnrollment.id);
      setEnrollments(enrollments.filter(e => e.id !== currentEnrollment.id));
      toast({
        title:"Enrollment deleted successfully",
        description: "The enrollment has been deleted.",
      });
      setModalOpen(false);
    } catch (error) {
      toast({
        title:"Failed to delete enrollment",
        description: "There was an error deleting the enrollment.",
      });
      console.error("Error deleting enrollment:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Training Enrollments</h1>
          <div className="animate-pulse h-10 w-32 bg-gray-200 rounded-md"></div>
        </div>
        <Separator />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse h-16 bg-gray-200 rounded-md"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ClipboardList className="w-6 h-6 text-primary" />
          <h1 className="text-2xl font-bold">Training Enrollments</h1>
        </div>
        <Button onClick={openAddModal}>
          <Plus className="w-4 h-4 mr-2" /> Add Enrollment
        </Button>
      </div>

      <Separator />

      {enrollments.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 space-y-4 text-center">
          <ClipboardList className="w-12 h-12 text-gray-400" />
          <p className="text-lg font-medium text-gray-500">No enrollments found</p>
          <Button onClick={openAddModal}>
            <Plus className="w-4 h-4 mr-2" /> Create First Enrollment
          </Button>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader className="bg-gray-50">
              <TableRow>
                <TableHead className="w-[200px]">
                  <div className="flex items-center">
                    <User className="w-4 h-4 mr-2 text-gray-500" />
                    Employee
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center">
                    <BookOpen className="w-4 h-4 mr-2 text-gray-500" />
                    Program
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-2 text-gray-500" />
                    Session Date
                  </div>
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {enrollments.map((enrollment) => (
                <TableRow key={enrollment.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center">
                      <User className="w-4 h-4 mr-2 text-gray-400" />
                      {enrollment.employee}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      <BookOpen className="w-4 h-4 mr-2 text-gray-400" />
                      {enrollment.program}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                      {enrollment.session_date}
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={enrollment.status} />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openEditModal(enrollment.id)}
                        className="flex items-center"
                      >
                        <Pencil className="w-3 h-3 mr-1" /> Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => openDeleteModal(enrollment.id)}
                        className="flex items-center"
                      >
                        <Trash2 className="w-3 h-3 mr-1" /> Delete
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Add/Edit Modal */}
      {(modalMode === "add" || modalMode === "edit") && (
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={modalMode === "add" ? "Add Enrollment" : "Edit Enrollment"}
          footer={
            <>
              <Button variant="ghost" onClick={() => setModalOpen(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button form="enrollment-form" type="submit" loading={isSubmitting}>
                {modalMode === "add" ? "Add Enrollment" : "Save Changes"}
              </Button>
            </>
          }
        >
          <form id="enrollment-form" onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="employee">
                Employee <span className="text-red-500">*</span>
              </Label>
              <Input
                id="employee"
                name="employee"
                type="text"
                value={formValues.employee}
                onChange={onChange}
                placeholder="Enter employee name"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="program">
                Program <span className="text-red-500">*</span>
              </Label>
              <Input
                id="program"
                name="program"
                type="text"
                value={formValues.program}
                onChange={onChange}
                placeholder="Enter program name"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="session_date">
                Session Date <span className="text-red-500">*</span>
              </Label>
              <Input
                id="session_date"
                name="session_date"
                type="date"
                value={formValues.session_date}
                onChange={onChange}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">
                Status <span className="text-red-500">*</span>
              </Label>
              <Select
                value={formValues.status}
                onValueChange={(value) => setFormValues({...formValues, status: value as Enrollment["status"]})}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Enrolled">Enrolled</SelectItem>
                  <SelectItem value="In Progress">In Progress</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {modalMode === "delete" && currentEnrollment && (
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Delete Enrollment"
          footer={
            <>
              <Button variant="outline" onClick={() => setModalOpen(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={confirmDelete} loading={isSubmitting}>
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <div className="flex items-center gap-3 bg-red-50 p-3 rounded-lg">
              <Trash2 className="w-5 h-5 text-red-600" />
              <p className="font-medium">Warning: This action cannot be undone</p>
            </div>
            <p>
              Are you sure you want to delete the enrollment of{" "}
              <strong>{currentEnrollment.employee}</strong> for the program{" "}
              <strong>{currentEnrollment.program}</strong>?
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
}