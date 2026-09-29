# Generated manually – redesign PurchaseRequest to match paper PR form.
#
# This migration:
# 1. Breaks the PurchaseOrder -> PurchaseRequest FK dependency
# 2. Deletes all PurchaseOrder rows (they reference the old PurchaseRequest)
# 3. Drops old PurchaseRequestItem and PurchaseRequest tables
# 4. Creates new PurchaseRequest, PurchaseRequestItem, PurchaseRequestAttachment,
#    PurchaseRequestDecision
# 5. Re-adds PurchaseOrder.purchase_request FK
#
# DATA LOSS: Old PurchaseRequest, PurchaseRequestItem, and PurchaseOrder records
# are destroyed. Confirmed acceptable by stakeholder.

import django.db.models.deletion
from django.db import migrations, models


def delete_purchase_orders(apps, schema_editor):
    """Delete existing PurchaseOrder rows before dropping the PurchaseRequest table."""
    PurchaseOrder = apps.get_model('procurement', 'PurchaseOrder')
    PurchaseOrder.objects.all().delete()


def noop(apps, schema_editor):
    """No-op reverse for RunPython."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0007_comparativeschedule'),
        ('hr', '0015_employeeallowance_allowance_type_and_more'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        # ── Step 1: Break PurchaseOrder FK dependency ──────────────
        migrations.RemoveField(
            model_name='purchaseorder',
            name='purchase_request',
        ),

        # ── Step 2: Delete orphaned PurchaseOrder rows ────────────
        migrations.RunPython(delete_purchase_orders, noop),

        # ── Step 3: Drop old PurchaseRequestItem ──────────────────
        migrations.RemoveField(
            model_name='purchaserequestitem',
            name='item',
        ),
        migrations.RemoveField(
            model_name='purchaserequestitem',
            name='purchase_request',
        ),
        migrations.DeleteModel(
            name='PurchaseRequestItem',
        ),

        # ── Step 4: Drop old PurchaseRequest ──────────────────────
        migrations.RemoveField(
            model_name='purchaserequest',
            name='items',
        ),
        migrations.RemoveField(
            model_name='purchaserequest',
            name='vendor',
        ),
        migrations.RemoveField(
            model_name='purchaserequest',
            name='budget_center',
        ),
        migrations.DeleteModel(
            name='PurchaseRequest',
        ),

        # ── Step 5: Create new PurchaseRequest ────────────────────
        migrations.CreateModel(
            name='PurchaseRequest',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('requisition_number', models.CharField(
                    blank=True, help_text='Auto-generated in format PR-00001',
                    max_length=30, unique=True,
                )),
                ('requester', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='purchase_requests',
                    to='hr.employees',
                )),
                ('department', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='hr.department',
                )),
                ('designation', models.CharField(
                    help_text='Request-time snapshot of position/designation',
                    max_length=100,
                )),
                ('contact', models.CharField(
                    help_text='Request-time snapshot of contact details',
                    max_length=100,
                )),
                ('status', models.CharField(
                    choices=[
                        ('DRAFT', 'Draft'),
                        ('PENDING_DEPARTMENT_HEAD', 'Pending Department Head'),
                        ('PENDING_ACCOUNTS', 'Pending Accounts'),
                        ('PENDING_GM', 'Pending General Manager'),
                        ('PENDING_DIRECTOR', 'Pending Director'),
                        ('PENDING_PROCUREMENT', 'Pending Procurement'),
                        ('PROCESSED', 'Processed'),
                        ('REJECTED', 'Rejected'),
                    ],
                    default='DRAFT', max_length=30,
                )),
                ('total_estimated_cost', models.DecimalField(
                    decimal_places=2, default=0,
                    help_text='Sum of line-item estimated costs',
                    max_digits=12,
                )),
                ('processed_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='processed_purchase_requests',
                    to='hr.employees',
                )),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'procurement_purchaserequest',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='purchaserequest',
            constraint=models.CheckConstraint(
                condition=models.Q(total_estimated_cost__gte=0),
                name='pr_total_estimated_cost_non_negative',
            ),
        ),
        migrations.AddIndex(
            model_name='purchaserequest',
            index=models.Index(fields=['status'], name='pr_status_idx'),
        ),
        migrations.AddIndex(
            model_name='purchaserequest',
            index=models.Index(
                fields=['requisition_number'], name='pr_req_number_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='purchaserequest',
            index=models.Index(
                fields=['-created_at'], name='pr_created_at_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='purchaserequest',
            index=models.Index(
                fields=['requester'], name='pr_requester_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='purchaserequest',
            index=models.Index(
                fields=['department'], name='pr_department_idx',
            ),
        ),

        # ── Step 6: Create new PurchaseRequestItem ────────────────
        migrations.CreateModel(
            name='PurchaseRequestItem',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('purchase_request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='procurement.purchaserequest',
                )),
                ('description', models.TextField(
                    help_text='Description of the item or service required',
                )),
                ('quantity', models.PositiveIntegerField()),
                ('expected_delivery_period', models.CharField(
                    help_text='Expected delivery timeframe, e.g. "2 weeks"',
                    max_length=100,
                )),
                ('estimated_cost', models.DecimalField(
                    decimal_places=2,
                    help_text='Total estimated cost for this line (not unit cost)',
                    max_digits=12,
                )),
                ('budget_code', models.ForeignKey(
                    help_text='Chart of Accounts entry to charge',
                    on_delete=django.db.models.deletion.PROTECT,
                    to='accounts.accountchart',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'procurement_purchaserequestitem',
            },
        ),
        migrations.AddConstraint(
            model_name='purchaserequestitem',
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name='pri_quantity_gte_1',
            ),
        ),
        migrations.AddConstraint(
            model_name='purchaserequestitem',
            constraint=models.CheckConstraint(
                condition=models.Q(estimated_cost__gte=0),
                name='pri_estimated_cost_non_negative',
            ),
        ),
        migrations.AddIndex(
            model_name='purchaserequestitem',
            index=models.Index(
                fields=['purchase_request'], name='pri_purchase_request_idx',
            ),
        ),

        # ── Step 7: Create PurchaseRequestAttachment ──────────────
        migrations.CreateModel(
            name='PurchaseRequestAttachment',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('purchase_request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='procurement.purchaserequest',
                )),
                ('file', models.FileField(
                    upload_to='procurement/purchase-requests/attachments/',
                )),
                ('original_filename', models.CharField(max_length=255)),
                ('uploaded_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='pr_attachments',
                    to='hr.employees',
                )),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'procurement_purchaserequestattachment',
            },
        ),

        # ── Step 8: Create PurchaseRequestDecision ────────────────
        migrations.CreateModel(
            name='PurchaseRequestDecision',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('purchase_request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='decisions',
                    to='procurement.purchaserequest',
                )),
                ('stage', models.CharField(
                    choices=[
                        ('DEPARTMENT_HEAD', 'Department Head'),
                        ('ACCOUNTS', 'Accounts'),
                        ('GM', 'General Manager'),
                        ('DIRECTOR', 'Director'),
                    ],
                    max_length=20,
                )),
                ('decision', models.CharField(
                    choices=[
                        ('APPROVED', 'Approved'),
                        ('VERIFIED', 'Verified'),
                        ('RECOMMENDED', 'Recommended'),
                        ('REJECTED', 'Rejected'),
                    ],
                    max_length=20,
                )),
                ('actor', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='pr_decisions',
                    to='hr.employees',
                )),
                ('reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'procurement_purchaserequestdecision',
            },
        ),
        migrations.AddIndex(
            model_name='purchaserequestdecision',
            index=models.Index(
                fields=['purchase_request'], name='prd_purchase_request_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='purchaserequestdecision',
            index=models.Index(fields=['stage'], name='prd_stage_idx'),
        ),

        # ── Step 9: Re-add PurchaseOrder.purchase_request FK ──────
        migrations.AddField(
            model_name='purchaseorder',
            name='purchase_request',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='purchase_order',
                to='procurement.purchaserequest',
            ),
            preserve_default=False,
        ),
    ]

