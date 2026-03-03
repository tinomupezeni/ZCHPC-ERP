from rest_framework import serializers
from ..models import DocumentCategory, Document, DocumentAcknowledgement


class DocumentCategorySerializer(serializers.ModelSerializer):
    """Serializer for document categories"""
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'description', 'icon', 'document_count']

    def get_document_count(self, obj):
        """Get count of active documents in this category accessible to the user"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        employee = request.user.employee_profile
        documents = obj.documents.filter(is_active=True, is_latest=True)

        # Filter by access
        count = 0
        for doc in documents:
            if doc.can_access(employee):
                count += 1
        return count


class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer for document list view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    file_url = serializers.SerializerMethodField()
    has_acknowledged = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'description',
            'category',
            'category_name',
            'file_type',
            'file_size',
            'file_size_display',
            'file_url',
            'version',
            'requires_acknowledgement',
            'has_acknowledged',
            'download_count',
            'created_at',
            'updated_at',
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_has_acknowledged(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        if not obj.requires_acknowledgement:
            return True

        employee = request.user.employee_profile
        return DocumentAcknowledgement.objects.filter(
            document=obj, employee=employee
        ).exists()

    def get_file_size_display(self, obj):
        """Return human-readable file size"""
        size = obj.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"


class DocumentDetailSerializer(DocumentListSerializer):
    """Serializer for document detail view"""
    uploaded_by_name = serializers.SerializerMethodField()
    acknowledgement_count = serializers.SerializerMethodField()

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + [
            'uploaded_by_name',
            'acknowledgement_count',
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}"
        return None

    def get_acknowledgement_count(self, obj):
        return obj.acknowledgements.count()


class DocumentAcknowledgementSerializer(serializers.ModelSerializer):
    """Serializer for document acknowledgement"""
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = DocumentAcknowledgement
        fields = ['id', 'document', 'employee_name', 'acknowledged_at']
        read_only_fields = ['id', 'acknowledged_at']

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"


class DocumentSummarySerializer(serializers.Serializer):
    """Serializer for documents summary"""
    total_documents = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    pending_acknowledgements = serializers.IntegerField()
    recent_documents = DocumentListSerializer(many=True)
