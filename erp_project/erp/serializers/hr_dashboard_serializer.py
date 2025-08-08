from rest_framework import serializers
from ..models import Employees, Department, TrainingProgram, TrainingSession, TrainingEnrollment

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employees
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class TrainingProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProgram
        fields = '__all__'

class TrainingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingSession
        fields = '__all__'

class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.firstname')
    program_title = serializers.CharField(source='program.title')

    class Meta:
        model = TrainingEnrollment
        fields = ['id', 'employee_name', 'program_title', 'session_date', 'status']