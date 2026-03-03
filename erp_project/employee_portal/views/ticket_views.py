from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from ..models import SupportTicket, TicketMessage
from ..serializers.ticket_serializers import (
    TicketListSerializer,
    TicketDetailSerializer,
    CreateTicketSerializer,
    CreateTicketMessageSerializer,
    TicketMessageSerializer,
    TicketSummarySerializer,
)


class TicketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing support tickets"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTicketSerializer
        if self.action == 'retrieve':
            return TicketDetailSerializer
        return TicketListSerializer

    def get_queryset(self):
        """Filter to only the employee's own tickets"""
        employee = getattr(self.request.user, 'employee_profile', None)
        if not employee:
            return SupportTicket.objects.none()
        queryset = SupportTicket.objects.filter(
            employee=employee
        ).prefetch_related('messages')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by category
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category=category_filter)

        # Filter by priority
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create a new support ticket"""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()

        # Create initial message from description
        TicketMessage.objects.create(
            ticket=ticket,
            sender=employee,
            message=ticket.description
        )

        response_serializer = TicketDetailSerializer(
            ticket, context={'request': request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def message(self, request, pk=None):
        """Add a message to a ticket"""
        ticket = self.get_object()

        # Cannot add messages to closed tickets
        if ticket.status == 'Closed':
            return Response(
                {'detail': 'Cannot add messages to closed tickets.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CreateTicketMessageSerializer(
            data=request.data,
            context={'request': request, 'ticket': ticket}
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        # Update ticket status to "Waiting" if it was "Resolved"
        if ticket.status == 'Resolved':
            ticket.status = 'Open'
            ticket.resolved_at = None
            ticket.save()

        # Update ticket's updated_at
        ticket.save()

        return Response(
            TicketMessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a ticket"""
        ticket = self.get_object()

        if not ticket.can_close:
            return Response(
                {'detail': 'This ticket cannot be closed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.status = 'Closed'
        ticket.closed_at = timezone.now()
        ticket.save()

        return Response({
            'detail': 'Ticket closed successfully.',
            'ticket': TicketDetailSerializer(ticket, context={'request': request}).data
        })

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen a closed ticket"""
        ticket = self.get_object()

        if not ticket.can_reopen:
            return Response(
                {'detail': 'This ticket cannot be reopened.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.status = 'Open'
        ticket.closed_at = None
        ticket.resolved_at = None
        ticket.save()

        return Response({
            'detail': 'Ticket reopened successfully.',
            'ticket': TicketDetailSerializer(ticket, context={'request': request}).data
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of employee's tickets"""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )
        tickets = SupportTicket.objects.filter(employee=employee)

        data = {
            'total_tickets': tickets.count(),
            'open_tickets': tickets.filter(status='Open').count(),
            'in_progress_tickets': tickets.filter(status='In Progress').count(),
            'resolved_tickets': tickets.filter(status='Resolved').count(),
            'closed_tickets': tickets.filter(status='Closed').count(),
        }

        serializer = TicketSummarySerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available ticket categories"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in SupportTicket.CATEGORY_CHOICES
        ])

    @action(detail=False, methods=['get'])
    def priorities(self, request):
        """Get available ticket priorities"""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in SupportTicket.PRIORITY_CHOICES
        ])
