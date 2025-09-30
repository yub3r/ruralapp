from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import Membership


# Mapeo de roles de Membership a nombres de grupos Django
ROLE_TO_GROUP = {
    Membership.Role.GESTION: "Restaurant_Manager",  # Por ahora usamos Manager para gestión restaurante
    Membership.Role.COCINA: "Restaurant_Kitchen",
    Membership.Role.DELIVERY: "Restaurant_Delivery",
    Membership.Role.CLIENT_ADMIN: "Client_Admin",
    Membership.Role.CLIENT_USER: "Client_User",
}


def _get_group(role: str):
    name = ROLE_TO_GROUP.get(role)
    if not name:
        return None
    return Group.objects.filter(name=name).first()


def _apply_membership_groups(membership: Membership):
    """Asegura que el usuario tenga (si activo) o no tenga (si inactivo) el grupo mapeado por su rol.
    No elimina otros grupos manuales del usuario.
    """
    group = _get_group(membership.role)
    if not group:
        return
    user = membership.user
    if membership.is_active:
        if not user.groups.filter(id=group.id).exists():
            user.groups.add(group)
    else:
        # Si se desactiva la membership, quitamos el grupo solo si ninguna otra membership activa
        # del mismo rol queda (multi-org futuro)
        still_active = Membership.objects.filter(
            user=user, role=membership.role, is_active=True
        ).exclude(pk=membership.pk).exists()
        if not still_active:
            user.groups.remove(group)


@receiver(post_save, sender=Membership)
def sync_membership_to_groups(sender, instance: Membership, **kwargs):
    _apply_membership_groups(instance)


@receiver(post_delete, sender=Membership)
def remove_group_on_delete(sender, instance: Membership, **kwargs):
    group = _get_group(instance.role)
    if not group:
        return
    user = instance.user
    # Si no quedan memberships activas con ese rol para el usuario, quitar grupo
    remaining = Membership.objects.filter(
        user=user, role=instance.role, is_active=True
    ).exists()
    if not remaining:
        user.groups.remove(group)