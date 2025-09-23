# repositories/journal_repository.py
from ..accounts_models import Journal

class JournalRepository:
    @staticmethod
    def get_all():
        return Journal.objects.all()

    @staticmethod
    def get_by_id(journal_id):
        return Journal.objects.get(id=journal_id)

    @staticmethod
    def create(**kwargs):
        return Journal.objects.create(**kwargs)

    @staticmethod
    def update(journal_id, **kwargs):
        journal = Journal.objects.get(id=journal_id)
        for key, value in kwargs.items():
            setattr(journal, key, value)
        journal.save()
        return journal

    @staticmethod
    def delete(journal_id):
        journal = Journal.objects.get(id=journal_id)
        journal.delete()
