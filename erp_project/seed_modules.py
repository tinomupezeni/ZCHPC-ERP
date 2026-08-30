import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_root.settings')
os.environ['USE_SQLITE'] = 'True'
django.setup()

from modules.identity.infrastructure.persistence.models import SystemModule

modules = [
    {
        'identifier': 'hr',
        'name': 'Human Resources',
        'description': 'Manage employees, departments, and positions.',
        'is_active': True,
        'dependencies': []
    },
    {
        'identifier': 'payroll',
        'name': 'Payroll',
        'description': 'Process salaries, taxes, and payslips.',
        'is_active': True,
        'dependencies': ['hr']
    },
    {
        'identifier': 'attendance',
        'name': 'Attendance',
        'description': 'Time tracking and attendance monitoring.',
        'is_active': True,
        'dependencies': ['hr']
    },
    {
        'identifier': 'leave',
        'name': 'Leave Management',
        'description': 'Request and approve leave, track balances.',
        'is_active': True,
        'dependencies': ['hr']
    },
    {
        'identifier': 'recruitment',
        'name': 'Recruitment',
        'description': 'Job postings, applicant tracking, and hiring.',
        'is_active': True,
        'dependencies': ['hr']
    },
    {
        'identifier': 'accounts',
        'name': 'Accounts',
        'description': 'Financial accounting and reporting.',
        'is_active': True,
        'dependencies': []
    },
    {
        'identifier': 'procurement',
        'name': 'Procurement',
        'description': 'Purchasing and vendor management.',
        'is_active': True,
        'dependencies': ['accounts']
    },
    {
        'identifier': 'portal',
        'name': 'Employee Portal',
        'description': 'Self-service for employees.',
        'is_active': True,
        'dependencies': ['hr']
    },
]

for m_data in modules:
    module, created = SystemModule.objects.get_or_create(
        identifier=m_data['identifier'],
        defaults=m_data
    )
    if not created:
        for key, value in m_data.items():
            setattr(module, key, value)
        module.save()
    print(f"Seeded module: {m_data['name']}")
