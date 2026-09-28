from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("follower", "0002_friendship"),
    ]

    operations = [
        migrations.DeleteModel(name="Friendship"),
    ]
