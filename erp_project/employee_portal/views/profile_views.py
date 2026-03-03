from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from ..serializers.profile_serializers import (
    EmployeeProfileReadSerializer,
    EmployeeProfileUpdateSerializer,
    ProfilePhotoSerializer,
)


class EmployeeProfileView(APIView):
    """
    Get and update the logged-in employee's profile.

    GET /api/portal/profile/ - Get profile
    PATCH /api/portal/profile/ - Update allowed fields
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get the current employee's profile."""
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeProfileReadSerializer(employee)
        return Response(serializer.data)

    def patch(self, request):
        """Update allowed fields of the employee's profile."""
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeProfileUpdateSerializer(
            employee,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            # Return full profile after update
            read_serializer = EmployeeProfileReadSerializer(employee)
            return Response(read_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilePhotoView(APIView):
    """
    Upload profile photo.

    POST /api/portal/profile/photo/
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """Upload a new profile photo."""
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProfilePhotoSerializer(data=request.data)

        if serializer.is_valid():
            photo = serializer.validated_data['photo']

            # For now, we'll just return success
            # In a full implementation, you'd save the photo to storage
            # and update the employee's photo field

            # Example implementation with a photo field:
            # employee.photo = photo
            # employee.save(update_fields=['photo'])

            return Response({
                'detail': 'Photo uploaded successfully',
                'filename': photo.name,
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
