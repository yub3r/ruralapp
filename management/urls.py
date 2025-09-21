from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path("", views.index, name = 'admin-panel'),
    path("template", views.download_excel, name = 'download-template'),
    path("upload", views.upload_data, name = 'upload-data'),
    path('create', views.add_client, name = 'add-client'),
    path('clients', views.clients_management, name = 'manage-clients'),
    path('add_user', views.create_user, name = 'create-user')
]
