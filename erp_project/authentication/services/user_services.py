# users/services.py
from typing import Dict, Any
from django.contrib.auth import get_user_model

User = get_user_model()

def create_user(data: Dict[str, Any]) -> User:
    """
    Creates a new user, ensuring the password is hashed.
    'data' is validated data from the serializer.
    """
    # Use create_user to handle password hashing
    password = data.pop('password', None)
    
    # Handle the 'username' field if you're using email as username
    if 'email' in data and 'username' not in data:
        data['username'] = data['email']
        
    user = User.objects.create_user(password=password, **data)
    return user

def update_user(instance: User, data: Dict[str, Any]) -> User:
    """
    Updates an existing user.
    If a password is provided, it will be hashed and updated.
    """
    # Pop the password to handle it separately
    password = data.pop('password', None)
    
    # Update all other fields from the serializer data
    for attr, value in data.items():
        setattr(instance, attr, value)
    
    # Set the new password if one was provided
    if password:
        instance.set_password(password)
        
    instance.save()
    return instance

def delete_user(instance: User):
    """
    Deletes a user.
    (You could change this to instance.is_active = False for a soft delete)
    """
    instance.delete()