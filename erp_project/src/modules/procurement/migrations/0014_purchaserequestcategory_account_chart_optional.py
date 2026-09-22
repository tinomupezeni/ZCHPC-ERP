import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    F25 category redesign: employee categories are descriptive only and carry
    no GL mapping, so account_chart becomes optional. Existing rows keep
    whatever mapping they have; nothing reads it any more.
    """

    dependencies = [
        ('procurement', '0013_purchaserequestitem_category_required'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaserequestcategory',
            name='account_chart',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='purchase_request_category',
                to='accounts.accountchart',
                help_text='Legacy (F11-A) mapping; unused. New categories have none - Accounts assigns budget codes per item',
            ),
        ),
    ]
