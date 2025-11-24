# addresses/services.py
from ..hr_models import Address
from typing import Dict, Any

def create_address(address_data: Dict[str, Any]) -> Address:
    """
    Creates a new Address instance from validated serializer data.
    """
    address = Address.objects.create(**address_data)
    return address

def update_address(address_instance: Address, address_data: Dict[str, Any]) -> Address:
    """
    Updates an existing Address instance.
    Handles both PUT and PATCH data.
    """
    for attr, value in address_data.items():
        setattr(address_instance, attr, value)
    
    address_instance.save()
    return address_instance

def delete_address(address_instance: Address):
    """
    Deletes an existing Address instance.
    """
    address_instance.delete()