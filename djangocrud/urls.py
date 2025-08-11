from django.contrib import admin
from django.urls import path, re_path, include
from tasks import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve 
from django.contrib.auth.decorators import user_passes_test

urlpatterns = [
    path('', views.home_view, name='home'),
    path('ruralapp/', include("ruralapp.urls")),
    # path('crypto-prices/', views.crypto_prices, name='crypto_prices'),
    # path('', views.crypto_prices, name='crypto_prices'),
    path("about", views.sobremi, name="About"),
    path('admin/', admin.site.urls, name="Admin"),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),


    re_path(r'^favicon\.ico$', views.favicon_view),
    path('favicon.ico',RedirectView.as_view(url='/media/favicon.ico')),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]