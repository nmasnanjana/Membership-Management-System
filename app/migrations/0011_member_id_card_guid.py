from django.db import migrations, models
import uuid


def populate_member_guid(apps, schema_editor):
    Member = apps.get_model("app", "Member")
    for m in Member.objects.filter(member_id_card_guid__isnull=True):
        m.member_id_card_guid = uuid.uuid4()
        m.save(update_fields=["member_id_card_guid"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0010_make_member_initials_last_name_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="member_id_card_guid",
            field=models.UUIDField(
                blank=True,
                editable=False,
                help_text="Server-generated authenticity GUID printed on member ID card",
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(populate_member_guid, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="member",
            name="member_id_card_guid",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                help_text="Server-generated authenticity GUID printed on member ID card",
                unique=True,
            ),
        ),
    ]

