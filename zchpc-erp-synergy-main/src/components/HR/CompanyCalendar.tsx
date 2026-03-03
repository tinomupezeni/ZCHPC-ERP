import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Plus, Calendar as CalendarIcon, MapPin, Clock, Trash2, Edit } from "lucide-react";
import { toast } from "sonner";
import apiClient from "@/services/apiClient";
import { format } from "date-fns";

interface CompanyEvent {
  id: number;
  title: string;
  description: string;
  event_type: string;
  start_date: string;
  end_date: string;
  start_time: string | null;
  end_time: string | null;
  is_all_day: boolean;
  location: string;
  created_by_name: string | null;
}

const EVENT_TYPES = [
  { value: "Holiday", label: "Public Holiday", color: "bg-red-500" },
  { value: "Company", label: "Company Event", color: "bg-blue-500" },
  { value: "Meeting", label: "Meeting", color: "bg-green-500" },
  { value: "Training", label: "Training", color: "bg-purple-500" },
  { value: "Other", label: "Other", color: "bg-gray-500" },
];

const CompanyCalendar = () => {
  const [events, setEvents] = useState<CompanyEvent[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [editingEvent, setEditingEvent] = useState<CompanyEvent | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    event_type: "Company",
    start_date: "",
    end_date: "",
    start_time: "",
    end_time: "",
    is_all_day: true,
    location: "",
  });

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get("/hr/events/");
      setEvents(response.data);
    } catch (error) {
      console.error("Failed to fetch events:", error);
      toast.error("Failed to load calendar events");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenModal = (event?: CompanyEvent) => {
    if (event) {
      setEditingEvent(event);
      setFormData({
        title: event.title,
        description: event.description,
        event_type: event.event_type,
        start_date: event.start_date,
        end_date: event.end_date,
        start_time: event.start_time || "",
        end_time: event.end_time || "",
        is_all_day: event.is_all_day,
        location: event.location,
      });
    } else {
      setEditingEvent(null);
      const dateStr = selectedDate ? format(selectedDate, "yyyy-MM-dd") : "";
      setFormData({
        title: "",
        description: "",
        event_type: "Company",
        start_date: dateStr,
        end_date: dateStr,
        start_time: "",
        end_time: "",
        is_all_day: true,
        location: "",
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async () => {
    if (!formData.title || !formData.start_date || !formData.end_date) {
      toast.error("Please fill in required fields");
      return;
    }

    try {
      const payload = {
        ...formData,
        start_time: formData.is_all_day ? null : formData.start_time || null,
        end_time: formData.is_all_day ? null : formData.end_time || null,
      };

      if (editingEvent) {
        await apiClient.put(`/hr/events/${editingEvent.id}/`, payload);
        toast.success("Event updated successfully");
      } else {
        await apiClient.post("/hr/events/", payload);
        toast.success("Event created successfully");
      }

      setIsModalOpen(false);
      fetchEvents();
    } catch (error) {
      console.error("Failed to save event:", error);
      toast.error("Failed to save event");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this event?")) return;

    try {
      await apiClient.delete(`/hr/events/${id}/`);
      toast.success("Event deleted successfully");
      fetchEvents();
    } catch (error) {
      console.error("Failed to delete event:", error);
      toast.error("Failed to delete event");
    }
  };

  const getEventTypeColor = (type: string) => {
    return EVENT_TYPES.find((t) => t.value === type)?.color || "bg-gray-500";
  };

  const eventsForSelectedDate = selectedDate
    ? events.filter((event) => {
        const eventStart = new Date(event.start_date);
        const eventEnd = new Date(event.end_date);
        const selected = new Date(selectedDate);
        selected.setHours(0, 0, 0, 0);
        eventStart.setHours(0, 0, 0, 0);
        eventEnd.setHours(0, 0, 0, 0);
        return selected >= eventStart && selected <= eventEnd;
      })
    : [];

  const eventDates = events.map((e) => new Date(e.start_date));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Company Calendar</h2>
          <p className="text-muted-foreground">
            Manage company events, holidays, and meetings
          </p>
        </div>
        <Button onClick={() => handleOpenModal()}>
          <Plus className="mr-2 h-4 w-4" /> Add Event
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarIcon className="h-5 w-5" />
              Select Date
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={setSelectedDate}
              className="rounded-md border"
              modifiers={{
                hasEvent: eventDates,
              }}
              modifiersStyles={{
                hasEvent: {
                  fontWeight: "bold",
                  backgroundColor: "hsl(var(--primary) / 0.1)",
                  color: "hsl(var(--primary))",
                },
              }}
            />
          </CardContent>
        </Card>

        {/* Events List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              Events for{" "}
              {selectedDate ? format(selectedDate, "MMMM d, yyyy") : "Today"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading events...
              </div>
            ) : eventsForSelectedDate.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No events for this date
              </div>
            ) : (
              <div className="space-y-4">
                {eventsForSelectedDate.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-start justify-between p-4 border rounded-lg hover:bg-muted/50"
                  >
                    <div className="flex gap-4">
                      <div
                        className={`w-1 rounded-full ${getEventTypeColor(
                          event.event_type
                        )}`}
                      />
                      <div>
                        <h4 className="font-semibold">{event.title}</h4>
                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                          <Badge variant="outline">{event.event_type}</Badge>
                          {event.location && (
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {event.location}
                            </span>
                          )}
                          {!event.is_all_day && event.start_time && (
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {event.start_time} - {event.end_time}
                            </span>
                          )}
                        </div>
                        {event.description && (
                          <p className="mt-2 text-sm text-muted-foreground">
                            {event.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleOpenModal(event)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(event.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Events */}
      <Card>
        <CardHeader>
          <CardTitle>All Upcoming Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {events
              .filter((e) => new Date(e.start_date) >= new Date())
              .slice(0, 10)
              .map((event) => (
                <div
                  key={event.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-3 h-3 rounded-full ${getEventTypeColor(
                        event.event_type
                      )}`}
                    />
                    <div>
                      <span className="font-medium">{event.title}</span>
                      <span className="text-sm text-muted-foreground ml-2">
                        {format(new Date(event.start_date), "MMM d, yyyy")}
                        {event.start_date !== event.end_date &&
                          ` - ${format(new Date(event.end_date), "MMM d, yyyy")}`}
                      </span>
                    </div>
                  </div>
                  <Badge variant="outline">{event.event_type}</Badge>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Add/Edit Event Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingEvent ? "Edit Event" : "Add New Event"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Title *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                placeholder="Event title"
              />
            </div>

            <div>
              <Label htmlFor="event_type">Event Type</Label>
              <Select
                value={formData.event_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, event_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EVENT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start_date">Start Date *</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) =>
                    setFormData({ ...formData, start_date: e.target.value })
                  }
                />
              </div>
              <div>
                <Label htmlFor="end_date">End Date *</Label>
                <Input
                  id="end_date"
                  type="date"
                  value={formData.end_date}
                  onChange={(e) =>
                    setFormData({ ...formData, end_date: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="is_all_day"
                checked={formData.is_all_day}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_all_day: checked })
                }
              />
              <Label htmlFor="is_all_day">All Day Event</Label>
            </div>

            {!formData.is_all_day && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="start_time">Start Time</Label>
                  <Input
                    id="start_time"
                    type="time"
                    value={formData.start_time}
                    onChange={(e) =>
                      setFormData({ ...formData, start_time: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="end_time">End Time</Label>
                  <Input
                    id="end_time"
                    type="time"
                    value={formData.end_time}
                    onChange={(e) =>
                      setFormData({ ...formData, end_time: e.target.value })
                    }
                  />
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                value={formData.location}
                onChange={(e) =>
                  setFormData({ ...formData, location: e.target.value })
                }
                placeholder="Event location"
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Event description"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              {editingEvent ? "Update" : "Create"} Event
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CompanyCalendar;
