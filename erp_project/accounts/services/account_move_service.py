# services/account_move_service.py
from accounts.repositories.account_move_repository import AccountMoveRepository

class AccountMoveService:
    @staticmethod
    def create_move(move_data):
        # Validate debit == credit
        total_debit = sum(line.get('debit', 0) for line in move_data.get('lines', []))
        total_credit = sum(line.get('credit', 0) for line in move_data.get('lines', []))
        if total_debit != total_credit:
            raise ValueError("Total debit must equal total credit")
        return AccountMoveRepository.create(**move_data)

    @staticmethod
    def post_move(move_id):
        move = AccountMoveRepository.get_by_id(move_id)
        if move.posted:
            raise ValueError("Move is already posted")
        # Additional business logic (e.g., checking accounts are reconcilable)
        move.posted = True
        move.save()
        return move
