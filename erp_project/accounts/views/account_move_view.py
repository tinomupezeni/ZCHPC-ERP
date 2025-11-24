# views/account_move_view.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..accounts_models import AccountMove
from accounts.serializers.account_move_serializer import AccountMoveSerializer
from accounts.services.account_move_service import AccountMoveService

class AccountMoveViewSet(viewsets.ViewSet):

    def list(self, request):
        moves = AccountMove.objects.all()
        serializer = AccountMoveSerializer(moves, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        move = AccountMove.objects.get(id=pk)
        serializer = AccountMoveSerializer(move)
        return Response(serializer.data)

    def create(self, request):
        serializer = AccountMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        move = AccountMoveService.create_move(serializer.validated_data)
        serializer = AccountMoveSerializer(move)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def post_move(self, request, pk=None):
        move = AccountMoveService.post_move(pk)
        serializer = AccountMoveSerializer(move)
        return Response(serializer.data)
