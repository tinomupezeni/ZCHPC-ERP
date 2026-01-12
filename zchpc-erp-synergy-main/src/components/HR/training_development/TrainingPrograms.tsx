import React, { useState, ChangeEvent, FormEvent, useEffect } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import Modal from "@/components/ui/Modal";
import { TrainingProgramCard, TrainingProgram } from "@/components/ui/training-program-card";
import { SearchFilterBar } from "@/components/ui/search-filter";
import Server from "@/services/Server";
import { useToast } from "@/hooks/use-toast";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

export default function TrainingProgramsPage() {
  const [programs, setPrograms] = useState<TrainingProgram[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit" | "delete" | null>(null);
  const [currentProgram, setCurrentProgram] = useState<TrainingProgram | null>(null);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("All");
  const { toast } = useToast();

  const [formValues, setFormValues] = useState<Omit<TrainingProgram, "id">>({
    title: "",
    category: "",
    duration: "",
    mandatory: false,
  });

  // Fetch programs on component mount
  useEffect(() => {
    fetchPrograms();
  }, []);

  const fetchPrograms = async () => {
    try {
      setIsLoading(true);
      const response = await Server.getTrainingPrograms();
      console.log("Fetched training programs:", response.data);
      setPrograms(response.data.results);
    } catch (error) {
      toast({
        title:"Failed to fetch training programs",
        description: "Please try again later.",});
      console.error("Error fetching programs:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const categories = ["All", ...Array.from(new Set(programs.map(p => p.category)))];

  const filteredPrograms = programs.filter(
    (p) =>
      (filterCategory === "All" || p.category === filterCategory) &&
      (p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.category.toLowerCase().includes(search.toLowerCase()))
  );

  // Modal handlers
  const openAddModal = () => {
    setFormValues({ title: "", category: "", duration: "", mandatory: false });
    setCurrentProgram(null);
    setModalMode("add");
    setModalOpen(true);
  };

  const openEditModal = (programId: number) => {
    const program = programs.find((p) => p.id === programId);
    if (!program) return;
    setFormValues({
      title: program.title,
      category: program.category,
      duration: program.duration,
      mandatory: program.mandatory,
    });
    setCurrentProgram(program);
    setModalMode("edit");
    setModalOpen(true);
  };

  const openDeleteModal = (programId: number) => {
    const program = programs.find((p) => p.id === programId);
    if (!program) return;
    setCurrentProgram(program);
    setModalMode("delete");
    setModalOpen(true);
  };

  const onChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormValues((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  // Handle form submission
  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!formValues.title.trim() || !formValues.category.trim() || !formValues.duration.trim()) {
      toast({
        title:"Please fill all required fields",
        description: "Title, category, and duration are required.",});
      return;
    }

    setIsSubmitting(true);
    try {
      if (modalMode === "add") {
        // Add new program
        const response = await Server.addTrainingProgram(formValues);
        setPrograms([...programs, response.data]);
        toast({
            title:"Training program added successfully",
            description: "You can now view and manage this program.",});
      } else if (modalMode === "edit" && currentProgram) {
        // Update existing program
        const response = await Server.updateTrainingProgram(currentProgram.id, formValues);
        setPrograms(programs.map(p => p.id === currentProgram.id ? response.data : p));
        toast({
            title:"Training program updated successfully",
            description: "Changes have been saved.",
        });
      }
      setModalOpen(false);
    } catch (error) {
      toast({
        title:"Failed to save training program",
        description: "Please try again later.",
    });
      console.error("Error saving program:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle delete confirmation
  const onDeleteConfirm = async () => {
    if (!currentProgram) return;

    setIsSubmitting(true);
    try {
      await Server.deleteTrainingProgram(currentProgram.id);
      setPrograms(programs.filter(p => p.id !== currentProgram.id));
      toast({
        title:"Training program deleted successfully",
        description: "The program has been removed.",});
      setModalOpen(false);
    } catch (error) {
      toast({
        title: "Failed to delete training program",
        description: "Please try again later.",});
      console.error("Error deleting program:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-pulse flex flex-col items-center justify-center h-64">
          <div className="w-12 h-12 bg-gray-200 rounded-full mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 relative">
      {/* Header and Search */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <h1 className="text-xl font-bold">Training Programs</h1>
        <div className="flex flex-col md:flex-row items-stretch md:items-center gap-2">
          <SearchFilterBar
            search={search}
            onSearchChange={setSearch}
            categories={categories}
            selectedCategory={filterCategory}
            onCategoryChange={setFilterCategory}
          />
          <Button onClick={openAddModal} className="flex items-center gap-2">
            <Plus className="w-5 h-5" /> Add Program
          </Button>
        </div>
      </div>

      <Separator className="my-4" />

      {/* Programs List */}
      {programs.length === 0 ? (
        <div className="text-center py-12 space-y-4">
          <p className="text-gray-500 text-lg">No training programs found.</p>
          <Button onClick={openAddModal}>
            <Plus className="w-5 h-5 mr-2" /> Create Your First Program
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPrograms.map((program) => (
            <TrainingProgramCard
              key={program.id}
              program={program}
              onEdit={openEditModal}
              onDelete={openDeleteModal}
            />
          ))}
        </div>
      )}

      {/* Add/Edit Program Modal */}
      {(modalMode === "add" || modalMode === "edit") && (
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={modalMode === "add" ? "Add Training Program" : "Edit Training Program"}
          footer={
            <>
              <Button variant="ghost" onClick={() => setModalOpen(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" form="program-form" loading={isSubmitting}>
                {modalMode === "add" ? "Add Program" : "Save Changes"}
              </Button>
            </>
          }
        >
          <form id="program-form" onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title <span className="text-red-500">*</span></Label>
              <Input
                id="title"
                name="title"
                type="text"
                value={formValues.title}
                onChange={onChange}
                placeholder="Enter program title"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category <span className="text-red-500">*</span></Label>
              <Input
                id="category"
                name="category"
                type="text"
                value={formValues.category}
                onChange={onChange}
                placeholder="Enter program category"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="duration">Duration <span className="text-red-500">*</span></Label>
              <Input
                id="duration"
                name="duration"
                type="text"
                value={formValues.duration}
                onChange={onChange}
                placeholder="e.g., 8 Hours"
                required
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="mandatory"
                name="mandatory"
                checked={formValues.mandatory}
                onCheckedChange={(checked) => 
                  setFormValues({...formValues, mandatory: Boolean(checked)})
                }
              />
              <Label htmlFor="mandatory">Mandatory Program</Label>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {modalMode === "delete" && currentProgram && (
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Delete Training Program"
          footer={
            <>
              <Button variant="ghost" onClick={() => setModalOpen(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button 
                variant="destructive" 
                onClick={onDeleteConfirm} 
                loading={isSubmitting}
              >
                Delete
              </Button>
            </>
          }
        >
          <p>
            Are you sure you want to delete the program <b>{currentProgram.title}</b>? This action cannot be undone.
          </p>
        </Modal>
      )}
    </div>
  );
}