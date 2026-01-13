# In views/recruitment_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from ..hr_models import Job, JobApplication
from ..serializers.recruitment_serializers import JobSerializer, JobApplicationSerializer

class JobViewSet(viewsets.ModelViewSet):
    """
    CRUD for Job Postings.
    Supports filtering by status, department, and internal/external visibility.
    """
    serializer_class = JobSerializer

    def get_queryset(self):
        queryset = Job.objects.select_related('department', 'position').all()
        
        # Filter by status (e.g., ?status=Open)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by department (e.g., ?department=1)
        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Filter by internal flag (e.g., ?internal=true)
        is_internal = self.request.query_params.get('internal')
        if is_internal is not None:
            internal_bool = is_internal.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_internal=internal_bool)
        
        # Search by title (e.g., ?search=engineer)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Override create to provide better error handling
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED, 
                headers=headers
            )
        
        # Return detailed error messages
        return Response(
            {
                'error': 'Validation failed',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def update(self, request, *args, **kwargs):
        """
        Override update to provide better error handling
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        
        return Response(
            {
                'error': 'Validation failed',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """
        Custom endpoint to get only public (non-internal) jobs
        URL: /api/jobs/public/
        """
        public_jobs = self.get_queryset().filter(is_internal=False, status='Open')
        serializer = self.get_serializer(public_jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def internal(self, request):
        """
        Custom endpoint to get only internal jobs
        URL: /api/jobs/internal/
        Note: You should add authentication/permission checks here
        """
        internal_jobs = self.get_queryset().filter(is_internal=True, status='Open')
        serializer = self.get_serializer(internal_jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """
        Get all applications for a specific job
        URL: /api/jobs/{id}/applications/
        """
        job = self.get_object()
        applications = job.applications.all()
        from ..serializers.recruitment_serializers import JobApplicationSerializer
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data)


class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.select_related('job', 'candidate').all()
    serializer_class = JobApplicationSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by job (e.g., ?job=1)
        job_id = self.request.query_params.get('job')
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        
        # Filter by status (e.g., ?status=Pending)
        app_status = self.request.query_params.get('status')
        if app_status:
            queryset = queryset.filter(status=app_status)
        
        return queryset