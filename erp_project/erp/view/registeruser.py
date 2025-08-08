from django.shortcuts import render, redirect
from django.contrib.auth import login
# from .forms import CustomUserCreationForm

# def register_user(request):
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             # Log the user in after registration
#             login(request, user)
#             return redirect('home')  # Redirect to the home page or another desired page
#     else:
#         form = CustomUserCreationForm()

    # return render(request, 'registration/register.html', {'form': form})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..serializers.user_serializer import CustomUserSerializer

class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
