import React, { useState, ChangeEvent, FormEvent, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, CalendarCheck, Edit2, Trash2, User, MapPin, BookOpen, Clock, RotateCw, CheckCircle } from "lucide-react";
import Modal from "@/components/ui/Modal";
import { format, parseISO } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import Server from "@/server/Server";
import { toast } from "react-toastify";

interface TrainingSession {
  id: number;
  program: string;
  trainer: string;
  date: string; // ISO string
  venue: string;
  status: "Scheduled" | "Ongoing" | "Completed";
}

const StatusBadge = ({ status }: { status: TrainingSession["status"] }) => {
  const statusConfig = {
    Scheduled: { icon: <Clock className="w-3 h-3 mr-1" />, color: "bg-blue-100 text-blue-800" },
    Ongoing: { icon: <RotateCw className="w-3 h-3 mr-1 animate-spin" />, color: "bg-yellow-100 text-yellow-800" },
    Completed: { icon: <CheckCircle className="w-3 h-3 mr-1" />, color: "bg-green-100 text-green-800" }
  };

  return (
    <Badge className={`${statusConfig[status].color} flex items-center`}>
      {statusConfig[status].icon}
      {status}
    </Badge>
  );
};

export default function TrainingSessionsPage() {
  const [sessions, setSessions] = useState<TrainingSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit" | "delete" | null>(null);
  const [currentSession, setCurrentSession] = useState<TrainingSession | null>(null);
  const [formValues, setFormValues] = useState<Omit<TrainingSession, "id">>({
    program: "",
    trainer: "",
    date: "",
    venue: "",
    status: "Scheduled",
  });

  // Fetch sessions from backend
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        setIsLoading(true);
        const response = await Server.getTrainingSessions();
        setSessions(response.data);
      } catch (error) {
        toast.error("Failed to load training sessions");
        console.error("Error fetching sessions:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
  }, []);

  // Filter sessions based on search term
  const filteredSessions = sessions.filter(session =>
    session.program.toLowerCase().includes(searchTerm.toLowerCase()) ||
    session.trainer.toLowerCase().includes(searchTerm.toLowerCase()) ||
    session.venue.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Modal handlers
  const openAddModal = () => {
    setFormValues({
      program: "",
      trainer: "",
      date: "",
      venue: "",
      status: "Scheduled",
    });
    setCurrentSession(null);
    setModalMode("add");
    setModalOpen(true);
  };

  const openEditModal = (id: number) => {
    const session = sessions.find((s) => s.id === id);
    if (!session) return;
    setFormValues({
      program: session.program,
      trainer: session.trainer,
      date: session.date,
      venue: session.venue,
      status: session.status,
    });
    setCurrentSession(session);
    setModalMode("edit");
    setModalOpen(true);
  };

  const openDeleteModal = (id: number) => {
    const session = sessions.find((s) => s.id === id);
    if (!session) return;
    setCurrentSession(session);
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

  // Form submit handler
  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!formValues.program.trim() || !formValues.trainer.trim() || !formValues.date.trim() || !formValues.venue.trim()) {
      toast.error("Please fill in all required fields");
      return;
    }

    setIsSubmitting(true);
    try {
      if (modalMode === "add") {
        const response = await Server.addTrainingSession(formValues);
        setSessions([...sessions, response.data]);
        toast.success("Session scheduled successfully");
      } else if (modalMode === "edit" && currentSession) {
        const response = await Server.updateTrainingSession(currentSession.id, formValues);
        setSessions(sessions.map(s => s.id === currentSession.id ? response.data : s));
        toast.success("Session updated successfully");
      }
      setModalOpen(false);
    } catch (error) {
      toast.error("Failed to save session");
      console.error("Error saving session:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Confirm delete session
  const confirmDelete = async () => {
    if (!currentSession) return;

    setIsSubmitting(true);
    try {
      await Server.deleteTrainingSession(currentSession.id);
      setSessions(sessions.filter(s => s.id !== currentSession.id));
      toast.success("Session deleted successfully");
      setModalOpen(false);
    } catch (error) {
      toast.error("Failed to delete session");
      console.error("Error deleting session:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Training Sessions</h1>
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <CalendarCheck className="w-6 h-6 text-primary" />
          <h1 className="text-2xl font-bold">Training Sessions</h1>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <Input
            placeholder="Search sessions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-md"
          />
          <Button onClick={openAddModal} className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Schedule Session
          </Button>
        </div>
      </div>

      <Separator />

      {filteredSessions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 space-y-4 text-center">
          <BookOpen className="w-12 h-12 text-gray-400" />
          <p className="text-lg font-medium text-gray-500">
            {searchTerm ? "No matching sessions found" : "No training sessions scheduled"}
          </p>
          {!searchTerm && (
            <Button onClick={openAddModal} className="mt-4">
              <Plus className="w-4 h-4 mr-2" />
              Schedule Your First Session
            </Button>
          )}
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader className="bg-gray-50">
              <TableRow>
                <TableHead className="w-[200px]">
                  <div className="flex items-center">
                    <BookOpen className="w-4 h-4 mr-2 text-gray-500" />
                    Program
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center">
                    <User className="w-4 h-4 mr-2 text-gray-500" />
                    Trainer
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center">
                    <CalendarCheck className="w-4 h-4 mr-2 text-gray-500" />
                    Date
                  </div>
                </TableHead>
                <TableHead>
                  <div className="flex items-center">
                    <MapPin className="w-4 h-4 mr-2 text-gray-500" />
                    Venue
                  </div>
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSessions.map((session) => (
                <TableRow key={session.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center">
                      <BookOpen className="w-4 h-4 mr-2 text-gray-400" />
                      {session.program}
                    </div>
                  </TableCell>
                  <TableCell>{session.trainer}</TableCell>
                  <TableCell>
                    {session.date ? format(parseISO(session.date), "MMM dd, yyyy") : "-"}
                  </TableCell>
                  <TableCell>{session.venue}</TableCell>
                  <TableCell>
                    <StatusBadge status={session.status} />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openEditModal(session.id)}
                        className="flex items-center gap-1"
                      >
                        <Edit2 className="w-3 h-3" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => openDeleteModal(session.id)}
                        className="flex items-center gap-1"
                      >
                        <Trash2 className="w-3 h-3" />
                        Delete
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
          title={modalMode === "add" ? "Schedule New Session" : "Edit Session"}
          footer={
            <>
              <Button variant="outline" onClick={() => setModalOpen(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button form="session-form" type="submit" loading={isSubmitting}>
                {modalMode === "add" ? "Schedule" : "Save Changes"}
              </Button>
            </>
          }
        >
          <form id="session-form" onSubmit={onSubmit} className="space-y-4">
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
              <Label htmlFor="trainer">
                Trainer <span className="text-red-500">*</span>
              </Label>
              <Input
                id="trainer"
                name="trainer"
                type="text"
                value={formValues.trainer}
                onChange={onChange}
                placeholder="Enter trainer name"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="date">
                Date <span className="text-red-500">*</span>
              </Label>
              <Input
                id="date"
                name="date"
                type="date"
                value={formValues.date}
                onChange={onChange}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="venue">
                Venue <span className="text-red-500">*</span>
              </Label>
              <Input
                id="venue"
                name="venue"
                type="text"
                value={formValues.venue}
                onChange={onChange}
                placeholder="Enter venue location"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">
                Status <span className="text-red-500">*</span>
              </Label>
              <Select
                value={formValues.status}
                onValueChange={(value) => setFormValues({...formValues, status: value as TrainingSession["status"]})}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Scheduled">Scheduled</SelectItem>
                  <SelectItem value="Ongoing">Ongoing</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {modalMode === "delete" && currentSession && (
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Confirm Deletion"
          footer={
            <>
              <Button variant="outline" onClick={() => setModalOpen(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={confirmDelete} loading={isSubmitting}>
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Session
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
              Are you sure you want to permanently delete the session for{" "}
              <strong>{currentSession.program}</strong> scheduled on{" "}
              <strong>{format(parseISO(currentSession.date), "MMM dd, yyyy")}</strong>?
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
}