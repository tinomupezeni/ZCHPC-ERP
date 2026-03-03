from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from ..serializers.auth_serializers import (
    EmployeeLoginSerializer,
    EmployeeProfileSerializer,
    TokenRefreshSerializer,
)


class EmployeeLoginView(APIView):
    """
    Employee portal login endpoint.

    POST /api/portal/auth/login/
    Body: { "ec_number": "EMP0001", "password": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmployeeLoginSerializer(data=request.data)

        if serializer.is_valid():
            employee = serializer.validated_data['employee']
            tokens = serializer.validated_data['tokens']

            # Serialize employee profile
            employee_data = EmployeeProfileSerializer(employee).data

            return Response({
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'employee': employee_data,
            }, status=status.HTTP_200_OK)

        return Response(
            {'detail': serializer.errors.get('non_field_errors', ['Login failed'])[0]},
            status=status.HTTP_401_UNAUTHORIZED
        )


class EmployeeTokenRefreshView(APIView):
    """
    Refresh access token for employee portal.

    POST /api/portal/auth/refresh/
    Body: { "refresh": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)

        if serializer.is_valid():
            return Response({
                'access': serializer.validated_data['access'],
            }, status=status.HTTP_200_OK)

        return Response(
            {'detail': 'Invalid or expired refresh token'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class EmployeeLogoutView(APIView):
    """
    Logout endpoint - blacklists the refresh token.

    POST /api/portal/auth/logout/
    Body: { "refresh": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {'detail': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {'detail': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            # Blacklisting might not be enabled
            return Response(
                {'detail': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )


class EmployeeMeView(APIView):
    """
    Get current authenticated employee's profile.

    GET /api/portal/auth/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get linked employee profile
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found for this user'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeProfileSerializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)
