def create_default_roles(sender, **kwargs):
    """
    Automatically populates the Role table with standard ERP roles
    after the database migration finishes.
    """
    from .hr_models import Role  # Lazy import

    DEFAULT_ROLES = [
        {'name': 'ADMIN', 'display_name': 'System Administrator'},
        {'name': 'HR', 'display_name': 'Human Resources Manager'},
        {'name': 'ACCOUNTANT', 'display_name': 'Accountant'},
        {'name': 'PROCUREMENT', 'display_name': 'Procurement Officer'},
        {'name': 'SALES', 'display_name': 'Sales Representative'},
        {'name': 'MANAGER', 'display_name': 'Department Manager'},
        {'name': 'STAFF', 'display_name': 'Regular Staff'},
    ]

    for role_data in DEFAULT_ROLES:
        Role.objects.get_or_create(
            name=role_data['name'],
            defaults={'display_name': role_data['display_name']}
        )