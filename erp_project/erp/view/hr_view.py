from ..serializers import employee_serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import Employees

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
