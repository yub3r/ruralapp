from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from ruralapp.models import Membership
from ruralapp.signals import ROLE_TO_GROUP, _apply_membership_groups  # reuse logic


class Command(BaseCommand):
    help = "Sincroniza todas las Membership existentes con los grupos Django según ROLE_TO_GROUP"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra lo que se haría sin aplicar cambios",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        self.stdout.write(self.style.MIGRATE_HEADING("== Sincronizando Membership → Groups =="))

        # Validar existencia de grupos necesarios
        missing = [g for g in set(ROLE_TO_GROUP.values()) if g and not Group.objects.filter(name=g).exists()]
        if missing:
            self.stdout.write(self.style.WARNING(f"Creando grupos faltantes: {', '.join(missing)}"))
            if not dry:
                for g in missing:
                    Group.objects.create(name=g)

        total = 0
        for membership in Membership.objects.select_related("user", "organization"):
            total += 1
            before = set(membership.user.groups.values_list("name", flat=True))
            if dry:
                # Simulación: qué grupo se añadiría / removería
                target = ROLE_TO_GROUP.get(membership.role)
                note = []
                if target and membership.is_active and target not in before:
                    note.append(f"ADD:{target}")
                if (not membership.is_active) and target in before:
                    note.append(f"REMOVE:{target}")
                self.stdout.write(f"Membership {membership.id} {membership} -> {','.join(note) if note else 'OK'}")
            else:
                _apply_membership_groups(membership)

        self.stdout.write(self.style.SUCCESS(f"Procesadas {total} memberships."))
        if dry:
            self.stdout.write(self.style.WARNING("Dry-run: no se aplicaron cambios."))