from ..entities.budget_center import BudgetCenter

class BudgetRepository:

    @staticmethod
    def check_budget(budget_center_id, amount):
        budget_center = BudgetCenter.objects.get(id=budget_center_id)
        if budget_center.remaining_amount >= amount:
            return True
        return False

    @staticmethod
    def allocate_budget(budget_center_id, amount):
        budget_center = BudgetCenter.objects.get(id=budget_center_id)
        budget_center.used_amount += amount
        budget_center.save()
