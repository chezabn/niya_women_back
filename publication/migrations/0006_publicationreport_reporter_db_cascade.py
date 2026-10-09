from django.conf import settings
from django.db import migrations


def set_reporter_fk_cascade(apps, schema_editor, on_delete):
    """Make MySQL enforce the reporter's Django CASCADE at the database level."""
    connection = schema_editor.connection
    if connection.vendor != "mysql":
        return

    PublicationReport = apps.get_model("publication", "PublicationReport")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    table = PublicationReport._meta.db_table
    user_table = User._meta.db_table
    reporter_column = PublicationReport._meta.get_field("reporter").column
    user_pk_column = User._meta.pk.column
    quote = connection.ops.quote_name

    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, table)
        reporter_fk_names = [
            name
            for name, details in constraints.items()
            if details.get("foreign_key")
            and details["foreign_key"][0] == user_table
            and details["columns"] == [reporter_column]
        ]

        for name in reporter_fk_names:
            cursor.execute(
                f"ALTER TABLE {quote(table)} DROP FOREIGN KEY {quote(name)}"
            )

        cursor.execute(
            f"ALTER TABLE {quote(table)} "
            f"ADD CONSTRAINT {quote('publication_report_reporter_fk')} "
            f"FOREIGN KEY ({quote(reporter_column)}) "
            f"REFERENCES {quote(user_table)} ({quote(user_pk_column)}) "
            f"ON DELETE {on_delete}"
        )


def forwards(apps, schema_editor):
    set_reporter_fk_cascade(apps, schema_editor, "CASCADE")


def backwards(apps, schema_editor):
    set_reporter_fk_cascade(apps, schema_editor, "RESTRICT")


class Migration(migrations.Migration):
    dependencies = [
        ("publication", "0005_publicationreport"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
