# Contexto de Base de Datos

Este archivo resume la configuración y las tablas principales de la base de datos PostgreSQL utilizada en el proyecto.

## Conexión
- Host: Localohost
- Base de datos principal: postgres
- Usuario administrador: postgres
- Motor: PostgreSQL 14.18

## Tablas principales
- auth_user: Usuarios del sistema
- ruralapp_order: Pedidos realizados
- ruralapp_otherdish, ruralapp_salad, ruralapp_sidedish: Opciones de menú


## Notas
- Las relaciones y claves foráneas están documentadas en el esquema.
- Se recomienda mantener los backups actualizados en BKPs/
- Para ver la estructura completa, consultar el archivo STRUCTURE.md y el esquema exportado.