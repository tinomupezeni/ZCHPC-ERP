# jobs/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Job
from ..serializers.jobs_serializer import JobSerializer
from rest_framework.generics import RetrieveUpdateAPIView

class JobListCreate(APIView):
    """List all jobs or create a new one"""
    def get(self, request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            # The serializer will automatically handle creating the new job
            # and setting the default values like posted_on
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class JobDetail(RetrieveUpdateAPIView):
    """Retrieve or update a single job by id"""
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    lookup_field = "pk"


class JobToggleStatus(APIView):
    """Toggle a job's open/closed status"""
    def patch(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        job.is_active = not job.is_active
        job.save(update_fields=["is_active"])
        return Response({"is_active": job.is_active})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)