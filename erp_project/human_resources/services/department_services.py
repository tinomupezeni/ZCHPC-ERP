from ..hr_models import Department
from django.shortcuts import get_object_or_404

class DepartmentService:
    @staticmethod
    def get_all_departments():
        return Department.objects.all()

    @staticmethod
    def get_department(dept_id):
        return get_object_or_404(Department, id=dept_id)

    @staticmethod
    def create_department(data):
        return Department.objects.create(**data)

    @staticmethod
    def update_department(dept_id, data):
        dept = get_object_or_404(Department, id=dept_id)
        for attr, value in data.items():
            setattr(dept, attr, value)
        dept.save()
        return dept

    @staticmethod
    def delete_department(dept_id):
        dept = get_object_or_404(Department, id=dept_id)
        dept.delete()
        return
