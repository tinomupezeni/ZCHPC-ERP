# repositories/account_move_repository.py
from ..accounts_models import AccountMove, AccountMoveLine

class AccountMoveRepository:
    @staticmethod
    def get_all():
        return AccountMove.objects.all()

    @staticmethod
    def get_by_id(move_id):
        return AccountMove.objects.get(id=move_id)

    @staticmethod
    def create(**kwargs):
        return AccountMove.objects.create(**kwargs)

    @staticmethod
    def update(move_id, **kwargs):
        move = AccountMove.objects.get(id=move_id)
        for key, value in kwargs.items():
            setattr(move, key, value)
        move.save()
        return move

    @staticmethod
    def delete(move_id):
        move = AccountMove.objects.get(id=move_id)
        move.delete()

    @staticmethod
    def add_line(move_id, **line_data):
        move = AccountMove.objects.get(id=move_id)
        line = AccountMoveLine.objects.create(move=move, **line_data)
        return line
