from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from ruralapp.models import Order


ROLE_NAMES = [
    "Developers",
    "Restaurant_Manager",
    "Restaurant_Kitchen",
    "Restaurant_Delivery",
    "Client_Admin",
    "Client_User",
]


class Command(BaseCommand):
    help = "Crea grupos base y permisos sugeridos para Ruralapp"

    def handle(self, *args, **options):
        groups = {name: Group.objects.get_or_create(name=name)[0] for name in ROLE_NAMES}
        self.stdout.write(self.style.SUCCESS(f"Grupos creados: {', '.join(groups.keys())}"))

        ct = ContentType.objects.get_for_model(Order)
        perms = {
            "view_kitchen_screen": Permission.objects.get_or_create(
                codename="view_kitchen_screen", name="Can view kitchen screen", content_type=ct
            )[0],
            "view_delivery_screen": Permission.objects.get_or_create(
                codename="view_delivery_screen", name="Can view delivery screen", content_type=ct
            )[0],
            "manage_menu": Permission.objects.get_or_create(
                codename="manage_menu", name="Can manage menu", content_type=ct
            )[0],
            "manage_org_users": Permission.objects.get_or_create(
                codename="manage_org_users", name="Can manage organization users", content_type=ct
            )[0],
        }

        groups["Restaurant_Kitchen"].permissions.add(perms["view_kitchen_screen"])
        groups["Restaurant_Delivery"].permissions.add(perms["view_delivery_screen"])
        groups["Restaurant_Manager"].permissions.add(
            perms["view_kitchen_screen"], perms["view_delivery_screen"], perms["manage_menu"]
        )
        groups["Client_Admin"].permissions.add(perms["manage_org_users"])

        self.stdout.write(self.style.SUCCESS("Permisos asignados a grupos base."))