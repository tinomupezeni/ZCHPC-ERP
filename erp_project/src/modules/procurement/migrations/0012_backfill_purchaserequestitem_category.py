from django.db import migrations


def backfill_category(apps, schema_editor):
    """
    Historical items only ever recorded the budget code their category
    resolved to. PurchaseRequestCategory.account_chart is a OneToOneField, so
    the reverse mapping budget_code -> category is unambiguous. Any item that
    cannot be mapped aborts the migration rather than being guessed at.
    """
    Item = apps.get_model('procurement', 'PurchaseRequestItem')
    Category = apps.get_model('procurement', 'PurchaseRequestCategory')

    for category in Category.objects.all():
        Item.objects.filter(
            category__isnull=True, budget_code_id=category.account_chart_id
        ).update(category_id=category.id)

    unmapped = list(
        Item.objects.filter(category__isnull=True).values_list('id', flat=True)
    )
    if unmapped:
        raise RuntimeError(
            f'Cannot backfill PurchaseRequestItem.category: {len(unmapped)} '
            f'item(s) have no category mapped to their budget code '
            f'(ids: {unmapped[:20]}). Resolve these manually and re-run.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0011_purchaserequestitem_category_nullable_budget_code'),
    ]

    operations = [
        # Reverse is a no-op: category is simply dropped when 0011 is reversed.
        migrations.RunPython(backfill_category, migrations.RunPython.noop),
    ]
