# Estructura de plantillas

Estrategia final solicitada: centralizar todas las vistas HTML activas bajo `Clients/` dejando **solo** `Restaurant/ruralapp.html` como dashboard/landing para el lado restaurante.

```
ruralapp/templates/
  base.html (si existe)
  README.md (este archivo)
  Clients/
    order.html
    edit_order.html
    misordenes.html
    resumen_pedidos.html
    whatsapp_preview.html
    allordenes.html
    24hs_ordenes.html
    ... (cualquier otra futura vista cliente)
  Restaurant/
    ruralapp.html   (única plantilla en este subdirectorio)
```

## Convenciones
- Nuevas pantallas para usuarios finales van en `Clients/`.
- Si en el futuro se agregan vistas exclusivas de cocina / administración interna, crear más archivos dentro de `Restaurant/` pero sólo si realmente NO son de uso de cliente.
- Evitar duplicados entre carpetas. Un nombre de template debe existir en un solo lugar.
- Las vistas en `views.py` deben usar rutas explícitas: `Clients/<archivo>.html` o `Restaurant/ruralapp.html`.

## Limpieza realizada
Se eliminaron las copias duplicadas que existían en la raíz y en `Restaurant/` (`resumen_pedidos.html`, `whatsapp_preview.html`, etc.).

## Cómo añadir una nueva plantilla de cliente
1. Crear el archivo bajo `Clients/`.
2. Referenciarlo en la vista con `render(request, 'Clients/nueva.html', contexto)`.
3. (Opcional) Actualizar esta lista si es una vista importante.

## Razón
Un único origen minimiza riesgo de divergencia y simplifica mantenimiento.
