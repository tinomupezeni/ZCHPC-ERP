"""
Company calendar event API views.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


def _serialize_event(event) -> dict:
    """Convert a CompanyEvent model instance to a plain dict."""
    created_by_name = None
    if event.created_by_id and event.created_by:
        created_by_name = f"{event.created_by.first_name} {event.created_by.surname}".strip()

    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type,
        "start_date": event.start_date,
        "end_date": event.end_date,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "is_all_day": event.is_all_day,
        "location": event.location,
        "created_by_name": created_by_name,
    }


def _get_employee_id(user):
    """Get the Employees.id linked to a user, if any."""
    from modules.hr.infrastructure.persistence.models import Employees

    try:
        return Employees.objects.get(user=user).id
    except Employees.DoesNotExist:
        return None


class EventListCreateView(APIView):
    """
    List all company calendar events or create a new one.

    GET: List all events
    POST: Create a new event
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all events, earliest start date first."""
        from modules.leave.infrastructure.persistence.models import CompanyEvent

        events = CompanyEvent.objects.select_related("created_by").order_by("start_date")
        return Response([_serialize_event(e) for e in events])

    def post(self, request):
        """Create a new event."""
        from modules.leave.infrastructure.persistence.models import CompanyEvent

        title = request.data.get("title")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        if not title or not start_date or not end_date:
            return Response(
                {"error": "title, start_date, and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event = CompanyEvent.objects.create(
            title=title,
            description=request.data.get("description", ""),
            event_type=request.data.get("event_type", "Company"),
            start_date=start_date,
            end_date=end_date,
            start_time=request.data.get("start_time") or None,
            end_time=request.data.get("end_time") or None,
            is_all_day=request.data.get("is_all_day", True),
            location=request.data.get("location", ""),
            created_by_id=_get_employee_id(request.user),
        )
        return Response(_serialize_event(event), status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    """
    Retrieve, update, or delete a company calendar event.

    GET: Get event details
    PUT/PATCH: Update event
    DELETE: Delete event
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, event_id: int):
        """Get event details."""
        from modules.leave.infrastructure.persistence.models import CompanyEvent

        try:
            event = CompanyEvent.objects.select_related("created_by").get(id=event_id)
        except CompanyEvent.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_event(event))

    def put(self, request, event_id: int):
        """Update event (full update)."""
        return self._update(request, event_id)

    def patch(self, request, event_id: int):
        """Update event (partial update)."""
        return self._update(request, event_id)

    def _update(self, request, event_id: int):
        """Handle event update."""
        from modules.leave.infrastructure.persistence.models import CompanyEvent

        try:
            event = CompanyEvent.objects.get(id=event_id)
        except CompanyEvent.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        for field in ("title", "description", "event_type", "start_date", "end_date", "location"):
            if field in request.data:
                setattr(event, field, request.data[field])
        if "start_time" in request.data:
            event.start_time = request.data["start_time"] or None
        if "end_time" in request.data:
            event.end_time = request.data["end_time"] or None
        if "is_all_day" in request.data:
            event.is_all_day = request.data["is_all_day"]

        event.save()
        return Response(_serialize_event(event))

    def delete(self, request, event_id: int):
        """Delete an event."""
        from modules.leave.infrastructure.persistence.models import CompanyEvent

        deleted, _ = CompanyEvent.objects.filter(id=event_id).delete()
        if not deleted:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
