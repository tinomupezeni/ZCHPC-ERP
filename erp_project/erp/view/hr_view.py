from ..serializers import employee_serializers
from ..serializers.hr_serializers import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import Employees, TrainingProgram
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.parsers import JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q

# employee registration
@api_view(['POST'])
def register_employee(request):
    try:
        # Convert empty strings to None for optional fields
        data = request.data.copy()
        for field in ['bankName', 'bankAccount', 'pensionFund', 'nssaNumber', 
                     'zimraTaxNumber', 'payeNumber', 'aidsLevyNumber']:
            if field in data and data[field] == "":
                data[field] = None
        
        serializer = employee_serializers.EmployeeRegistrationSerializer(data=data)
        
        if serializer.is_valid():
            employee = serializer.save()
            return Response({
                "message": "Employee created successfully!",
                "employeeid": employee.employeeid
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_all_employees(request): 
    users = Employees.objects.all()
    # serializer = employee_serializers.EmployeeRegistrationSerializer(users, many=True)
    serializer = employee_serializers.EmployeePayslipSerializer(users, many=True)

    
    return Response(serializer.data, status=status.HTTP_200_OK)



#This view handles the registration of training programs
#this function also handles the filtering of training programs based on mandatory status and category
# get all training programs
@csrf_exempt
@require_http_methods(["GET", "POST"])
def training_program_list(request):
    if request.method == 'GET':
        # Filtering capability
        mandatory = request.GET.get('mandatory')
        category = request.GET.get('category')
        
        programs = TrainingProgram.objects.all()
        
        if mandatory in ['true', 'false']:
            programs = programs.filter(mandatory=mandatory.lower() == 'true')
        if category:
            programs = programs.filter(category__iexact=category)
            
        serializer = TrainingProgramSerializer(programs, many=True)
        return JsonResponse({
            'count': programs.count(),
            'results': serializer.data
        }, safe=False)

    elif request.method == 'POST':
        try:
            data = JSONParser().parse(request)
            
            # Custom validation
            if not data.get('title'):
                return JsonResponse(
                    {'error': 'Title is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            serializer = TrainingProgramSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(
                    serializer.data, 
                    status=status.HTTP_201_CREATED
                )
            return JsonResponse(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

#this function handles the retrieval, update, and deletion of a specific training program
# training program detail
@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def training_program_detail(request, pk):
    try:
        program = TrainingProgram.objects.get(pk=pk)
    except TrainingProgram.DoesNotExist:
        return JsonResponse(
            {'error': 'Training program not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = TrainingProgramSerializer(program)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        try:
            data = JSONParser().parse(request)
            serializer = TrainingProgramSerializer(program, data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data)
            return JsonResponse(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == 'DELETE':
        try:
            program.delete()
            return JsonResponse(
                {'message': 'Training program deleted successfully'}, 
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



#
@api_view(['GET', 'POST'])
def training_session_list(request):
    """
    List all sessions or create a new session
    """
    if request.method == 'GET':
        sessions = TrainingSession.objects.all()
        serializer = TrainingSessionSerializer(sessions, many=True)
        return JsonResponse(serializer.data, safe=False)
    
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = TrainingSessionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def training_session_detail(request, pk):
    """
    Retrieve, update or delete a session
    """
    try:
        session = TrainingSession.objects.get(pk=pk)
    except TrainingSession.DoesNotExist:
        return JsonResponse(
            {'error': 'Training session not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = TrainingSessionSerializer(session)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = TrainingSessionSerializer(session, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        session.delete()
        return JsonResponse(
            {'message': 'Training session deleted successfully'}, 
            status=status.HTTP_204_NO_CONTENT
        )
        
@api_view(['GET', 'POST'])
@csrf_exempt
def training_enrollment_list(request):
    if request.method == 'GET':
        enrollments = TrainingEnrollment.objects.all()
        serializer = TrainingEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        print("Received data:", request.data)  # Debugging line
        serializer = TrainingEnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@csrf_exempt
def training_enrollment_detail(request, pk):
    try:
        enrollment = TrainingEnrollment.objects.get(pk=pk)
    except TrainingEnrollment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TrainingEnrollmentSerializer(enrollment)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = TrainingEnrollmentSerializer(enrollment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['GET', 'POST'])
def certification_list(request):
    if request.method == 'GET':
        certifications = TrainingCertification.objects.all()
        serializer = CertificationSerializer(certifications, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CertificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def certification_detail(request, pk):
    certification = get_object_or_404(TrainingCertification, pk=pk)
    
    if request.method == 'GET':
        serializer = CertificationSerializer(certification)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = CertificationSerializer(certification, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        certification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def certification_search(request):
    search_term = request.query_params.get('search', '')
    certifications = TrainingCertification.objects.filter(
        Q(employee__icontains=search_term) | 
        Q(program__icontains=search_term))
    serializer = CertificationSerializer(certifications, many=True)
    return Response(serializer.data)