# addresses/serializers.py
from rest_framework import serializers
from ..hr_models import Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__' # Includes all fields: id, label, street, city, etc.