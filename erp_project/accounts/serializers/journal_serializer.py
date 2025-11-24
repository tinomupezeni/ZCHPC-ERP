# serializers/journal_serializer.py
from rest_framework import serializers
from ..accounts_models import Journal

class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = '__all__'


