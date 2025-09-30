from django.urls import include, path, re_path
from ruralapp import views


urlpatterns = [
    path('ruralapp/', views.ruralapp, name='ruralapp'),
    path('restoboard/', views.restoboard, name='restoboard'),
    path('clientes/', views.restaurant_clients, name='restaurant_clients'),
    path('clientes/nuevo/', views.new_client, name='new_client'),
    path('clientes/<int:org_id>/editar/', views.edit_client, name='edit_client'),
    path('order/', views.order_view, name='order'),
    path('misordenes/', views.mis_ordenes, name='mis_ordenes'),
    path('editar-orden/<int:order_id>/', views.edit_order, name='edit_order'),
    # path('ordenes_24hs/', views.ordenes_24hs, name='ordenes_24hs'),
    path('resumen_pedidos/', views.resumen_pedidos, name='resumen_pedidos'),  
]