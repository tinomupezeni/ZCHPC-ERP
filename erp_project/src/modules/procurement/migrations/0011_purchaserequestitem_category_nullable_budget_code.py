import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    F25 Slice 1, step 1/3: add the employee-facing category (nullable for now,
    backfilled in 0012, enforced in 0013) and let budget_code be NULL until
    Accounts assigns it.
    """

    dependencies = [
        ('accounts', '0002_accountchart_external_account_type'),
        ('procurement', '0010_purchaserequest_purchase_order_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaserequestitem',
            name='category',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='items',
                to='procurement.purchaserequestcategory',
                help_text='Employee-facing category chosen by the requester (descriptive only)',
            ),
        ),
        migrations.AlterField(
            model_name='purchaserequestitem',
            name='budget_code',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='accounts.accountchart',
                help_text='Authoritative Chart of Accounts entry; assigned by Accounts, NULL until then',
            ),
        ),
    ]
