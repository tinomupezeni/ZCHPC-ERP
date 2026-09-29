import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """F25 Slice 1, step 3/3: every item now has a category; enforce it."""

    dependencies = [
        ('procurement', '0012_backfill_purchaserequestitem_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaserequestitem',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='items',
                to='procurement.purchaserequestcategory',
                help_text='Employee-facing category chosen by the requester (descriptive only)',
            ),
        ),
    ]
