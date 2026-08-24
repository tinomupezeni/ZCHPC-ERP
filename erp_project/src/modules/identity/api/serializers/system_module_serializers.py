from rest_framework import serializers
from modules.identity.infrastructure.persistence.models import SystemModule

class SystemModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemModule
        fields = ['id', 'identifier', 'name', 'description', 'is_active', 'dependencies']
        read_only_fields = ['id', 'identifier', 'dependencies']
