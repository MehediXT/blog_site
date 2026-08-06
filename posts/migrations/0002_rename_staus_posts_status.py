from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='posts',
            old_name='staus',
            new_name='status',
        ),
    ]
