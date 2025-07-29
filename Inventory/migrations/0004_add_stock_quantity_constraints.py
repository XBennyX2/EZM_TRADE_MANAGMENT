# Generated manually for stock quantity constraints

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0003_notificationcategory_productcategory_purchaserequest_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplierproduct',
            name='stock_quantity',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Current stock quantity available from this supplier',
                validators=[django.core.validators.MinValueValidator(0)]
            ),
        ),
        # Note: SQLite doesn't support adding CHECK constraints to existing tables
        # The PositiveIntegerField already enforces non-negative values at the Django level
    ]
