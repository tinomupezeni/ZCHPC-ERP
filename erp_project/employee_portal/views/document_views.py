from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import FileResponse, Http404
from django.db.models import Q
from ..models import DocumentCategory, Document, DocumentAcknowledgement
from ..serializers.document_serializers import (
    DocumentCategorySerializer,
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentAcknowledgementSerializer,
    DocumentSummarySerializer,
)


class DocumentCategoryListView(APIView):
    """List all active document categories"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = DocumentCategory.objects.filter(is_active=True)
        serializer = DocumentCategorySerializer(
            categories, many=True, context={'request': request}
        )
        return Response(serializer.data)


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing documents"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DocumentDetailSerializer
        return DocumentListSerializer

    def get_queryset(self):
        """Filter documents accessible to the employee"""
        employee = getattr(self.request.user, 'employee_profile', None)
        if not employee:
            return Document.objects.none()
        queryset = Document.objects.filter(is_active=True, is_latest=True)

        # Filter by access permissions
        accessible_docs = []
        for doc in queryset:
            if doc.can_access(employee):
                accessible_docs.append(doc.id)

        queryset = queryset.filter(id__in=accessible_docs)

        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by file type
        file_type = self.request.query_params.get('file_type')
        if file_type:
            queryset = queryset.filter(file_type=file_type)

        # Search by title or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset.select_related('category', 'uploaded_by')

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a document file"""
        document = self.get_object()
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not document.can_access(employee):
            return Response(
                {'detail': 'You do not have permission to access this document.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Increment download count
        document.download_count += 1
        document.save(update_fields=['download_count'])

        try:
            response = FileResponse(
                document.file.open('rb'),
                as_attachment=True,
                filename=f"{document.title}.{document.file_type}"
            )
            return response
        except FileNotFoundError:
            raise Http404("Document file not found")

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge reading a document"""
        document = self.get_object()
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not document.can_access(employee):
            return Response(
                {'detail': 'You do not have permission to access this document.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not document.requires_acknowledgement:
            return Response(
                {'detail': 'This document does not require acknowledgement.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already acknowledged
        existing = DocumentAcknowledgement.objects.filter(
            document=document, employee=employee
        ).first()

        if existing:
            return Response(
                {'detail': 'Document already acknowledged.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        acknowledgement = DocumentAcknowledgement.objects.create(
            document=document,
            employee=employee,
            ip_address=ip_address
        )

        serializer = DocumentAcknowledgementSerializer(acknowledgement)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of documents for the employee"""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get accessible documents
        all_docs = Document.objects.filter(is_active=True, is_latest=True)
        accessible_docs = [doc for doc in all_docs if doc.can_access(employee)]
        accessible_ids = [doc.id for doc in accessible_docs]

        # Count documents requiring acknowledgement that haven't been acknowledged
        acknowledged_ids = DocumentAcknowledgement.objects.filter(
            employee=employee
        ).values_list('document_id', flat=True)

        pending_ack = Document.objects.filter(
            id__in=accessible_ids,
            requires_acknowledgement=True
        ).exclude(id__in=acknowledged_ids).count()

        # Get recent documents
        recent_docs = Document.objects.filter(
            id__in=accessible_ids
        ).order_by('-created_at')[:5]

        data = {
            'total_documents': len(accessible_ids),
            'total_categories': DocumentCategory.objects.filter(is_active=True).count(),
            'pending_acknowledgements': pending_ack,
            'recent_documents': DocumentListSerializer(
                recent_docs, many=True, context={'request': request}
            ).data,
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def pending_acknowledgements(self, request):
        """Get documents that require acknowledgement but haven't been acknowledged"""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response([])

        # Get accessible documents that require acknowledgement
        all_docs = Document.objects.filter(
            is_active=True, is_latest=True, requires_acknowledgement=True
        )
        accessible_docs = [doc for doc in all_docs if doc.can_access(employee)]
        accessible_ids = [doc.id for doc in accessible_docs]

        # Get already acknowledged documents
        acknowledged_ids = DocumentAcknowledgement.objects.filter(
            employee=employee
        ).values_list('document_id', flat=True)

        # Get pending documents
        pending_docs = Document.objects.filter(
            id__in=accessible_ids
        ).exclude(id__in=acknowledged_ids)

        serializer = DocumentListSerializer(
            pending_docs, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def file_types(self, request):
        """Get available file types for filtering"""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response([])

        # Get accessible documents
        all_docs = Document.objects.filter(is_active=True, is_latest=True)
        accessible_docs = [doc for doc in all_docs if doc.can_access(employee)]
        accessible_ids = [doc.id for doc in accessible_docs]

        file_types = Document.objects.filter(
            id__in=accessible_ids
        ).values_list('file_type', flat=True).distinct()

        return Response(list(file_types))
