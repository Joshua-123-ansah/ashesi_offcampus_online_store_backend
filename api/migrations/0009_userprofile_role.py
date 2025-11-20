from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_payment"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="role",
            field=models.CharField(
                choices=[
                    ("super_admin", "Super Admin"),
                    ("employee", "Employee"),
                    ("cook", "Cook"),
                    ("student", "Student"),
                ],
                default="student",
                max_length=20,
            ),
        ),
    ]
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_payment"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="role",
            field=models.CharField(
                choices=[
                    ("super_admin", "Super Admin"),
                    ("employee", "Employee"),
                    ("cook", "Cook"),
                    ("student", "Student"),
                ],
                default="student",
                max_length=20,
            ),
        ),
    ]

