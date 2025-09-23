
# from django.contrib.auth import get_user_model

from erp.dependencies import *

User = get_user_model()

# ---- system users

@api_view(['POST'])
def register_user(request):
    serializer = employee_serializers.UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()  
        return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_all_user(request): 
    users = User.objects.all()
    serializer = employee_serializers.UserRegistrationSerializer(users, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
def delete_user(request, id):  # Add the `id` parameter
    try:
        user = User.objects.get(employeeid=id)
        user.delete()
        return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    
@api_view(['GET'])
def get_user(request, id):  # Add the `id` parameter
    try:
        user = User.objects.get(employeeid=id)
        user_data = {
            "employeeid": user.employeeid,
            "firstname": user.firstname,
            "surname": user.surname,
            "role": user.role,
            "department": user.department,
            "email": user.email,
            "salary": user.salary,
            "contractFrom": user.contractFrom,
            "contractTo": user.contractTo,
            "isActive": user.isActive,
        }
        
        return Response(user_data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

# hr module
