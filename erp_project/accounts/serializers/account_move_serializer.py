# serializers/account_move_serializer.py
from rest_framework import serializers
from ..accounts_models import AccountMove, AccountMoveLine

class AccountMoveLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountMoveLine
        fields = '__all__'


class AccountMoveSerializer(serializers.ModelSerializer):
    lines = AccountMoveLineSerializer(many=True, required=False)

    class Meta:
        model = AccountMove
        fields = ['id', 'journal', 'date', 'ref', 'narration', 'posted', 'lines', 'created_at', 'updated_at']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        move = AccountMove.objects.create(**validated_data)
        for line in lines_data:
            AccountMoveLine.objects.create(move=move, **line)
        return move
