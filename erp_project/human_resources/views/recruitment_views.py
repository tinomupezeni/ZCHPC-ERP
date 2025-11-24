from rest_framework import viewsets
from ..hr_models import Job, JobApplication
from ..serializers.recruitment_serializers import JobSerializer, JobApplicationSerializer

class JobViewSet(viewsets.ModelViewSet):
    """
    CRUD for Job Postings.
    Supports filtering by status or department.
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def get_queryset(self):
        queryset = Job.objects.all()
        # Optional: Filter by status ?status=Open
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer