from rest_framework import serializers
from ..models import SupportTicket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    """Serializer for ticket messages"""
    sender_name = serializers.SerializerMethodField()
    is_own_message = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessage
        fields = [
            'id', 'message', 'attachment', 'sender_name',
            'is_own_message', 'created_at'
        ]

    def get_sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.surname}"

    def get_is_own_message(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'employee_profile'):
            return obj.sender_id == request.user.employee_profile.id
        return False


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer for listing tickets"""
    message_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    can_close = serializers.BooleanField(read_only=True)
    can_reopen = serializers.BooleanField(read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'category', 'priority', 'subject',
            'status', 'message_count', 'last_message_at',
            'created_at', 'updated_at', 'can_close', 'can_reopen'
        ]

    def get_message_count(self, obj):
        return obj.messages.filter(is_internal=False).count()

    def get_last_message_at(self, obj):
        last_message = obj.messages.filter(is_internal=False).last()
        if last_message:
            return last_message.created_at
        return None


class TicketDetailSerializer(serializers.ModelSerializer):
    """Serializer for ticket details with messages"""
    messages = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    can_close = serializers.BooleanField(read_only=True)
    can_reopen = serializers.BooleanField(read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'category', 'priority', 'subject',
            'description', 'status', 'assigned_to_name',
            'created_at', 'updated_at', 'resolved_at', 'closed_at',
            'messages', 'can_close', 'can_reopen'
        ]

    def get_messages(self, obj):
        # Only show non-internal messages to employees
        messages = obj.messages.filter(is_internal=False)
        return TicketMessageSerializer(
            messages, many=True, context=self.context
        ).data

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.surname}"
        return None


class CreateTicketSerializer(serializers.ModelSerializer):
    """Serializer for creating a new ticket"""
    class Meta:
        model = SupportTicket
        fields = ['category', 'priority', 'subject', 'description']

    def create(self, validated_data):
        validated_data['employee'] = self.context['request'].user.employee_profile
        return super().create(validated_data)


class CreateTicketMessageSerializer(serializers.ModelSerializer):
    """Serializer for adding a message to a ticket"""
    class Meta:
        model = TicketMessage
        fields = ['message', 'attachment']

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user.employee_profile
        validated_data['ticket'] = self.context['ticket']
        return super().create(validated_data)


class TicketSummarySerializer(serializers.Serializer):
    """Serializer for ticket summary statistics"""
    total_tickets = serializers.IntegerField()
    open_tickets = serializers.IntegerField()
    in_progress_tickets = serializers.IntegerField()
    resolved_tickets = serializers.IntegerField()
    closed_tickets = serializers.IntegerField()
