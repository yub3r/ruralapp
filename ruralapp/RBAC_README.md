# RBAC / Membership ↔ Groups Sync

Este documento describe cómo se sincronizan los `Membership` con los grupos estándar de Django.

## Modelos Clave
- `Organization`: define ámbito multi-tenant (CLIENT / RESTAURANT).
- `Membership`: relación usuario–organización–rol.
- Roles (`Membership.Role`): GESTION, COCINA, DELIVERY, CLIENT_ADMIN, CLIENT_USER.

## Mapeo a Grupos Django
```
GESTION       -> Restaurant_Manager
COCINA        -> Restaurant_Kitchen
DELIVERY      -> Restaurant_Delivery
CLIENT_ADMIN  -> Client_Admin
CLIENT_USER   -> Client_User
```
Definido en `ruralapp/signals.py` como `ROLE_TO_GROUP`.

## Comportamiento de Sincronización
La sincronización ocurre automáticamente mediante señales:
- `post_save` de `Membership`: agrega el grupo si `is_active=True`.
- Si una membership se desactiva (`is_active=False`), se retira el grupo solo si no quedan otras memberships activas del mismo rol para ese usuario (pensando en organizaciones múltiples futuras).
- `post_delete`: igual lógica de limpieza.

No se eliminan otros grupos no mapeados (por ejemplo, `Developers`).

## Comando de Backfill / Reconciliación
Para forzar una reconciliación completa:
```
python manage.py sync_membership_groups --dry-run  # Vista previa
python manage.py sync_membership_groups            # Aplica cambios
```
Crea grupos faltantes si no existen.

## Casos de Uso
1. Importaste usuarios y creaste memberships manualmente -> ejecuta sync.
2. Cambiaste nombres de grupos -> actualiza `ROLE_TO_GROUP` y corre sync.
3. Desactivaste memberships masivamente vía SQL -> corre sync para limpiar grupos.

## Extensión Futura
- Añadir permisos específicos por rol (ej: `view_kitchen_screen`).
- Añadir roles por organización para separar contextos (grupos globales vs permisos scoped).
- Decoradores unificados que acepten cualquiera de: rol membership o grupo.

## Vista Rápida del Código
- Señales: `ruralapp/signals.py`
- Comando: `ruralapp/management/commands/sync_membership_groups.py`

## Verificación Manual
En shell Django:
```python
from django.contrib.auth.models import User
u = User.objects.get(username='admin')
print(u.groups.all())
```
Si falta un grupo esperado:
```bash
python manage.py sync_membership_groups
```

---
Última actualización: mantener este archivo al ampliar roles.
