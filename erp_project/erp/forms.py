# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('general', 'General'),
    ('guest', 'Guest'),
)

DEPARTMENT_CHOICES = (
    ('hr', 'Human Resource'),
    ('account', 'Account'),
    ('inventory', 'Inventory'),
    ('project', 'Project Management'),
    ('sales', 'Sales & CRM'),
)

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, max_length=30)
    last_name = forms.CharField(required=True, max_length=30)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES, required=True)
    # Note: UserCreationForm by default provides password1 and password2 fields.
    # For this example, we assume you're using them; if not, adjust accordingly.

    class Meta:
        model = User
        # If you have extended the User model to include role and department,
        # include them here. Otherwise, you'll need to store these extra fields separately.
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'password1', 'password2')
