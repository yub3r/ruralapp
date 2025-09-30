from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Salad,
    OtherDish,
    SideDish,
    WeeklyMenu,
    Order,
    EventLog,
    AppState,
    UserProfile,
    WhatsAppGroup,
    GroupNotification,
    Organization,
)
from .models import Membership


class SaladAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

class OtherDishAdmin(admin.ModelAdmin):
    list_display = ['name', 'plus_side']

class SideDishAdmin(admin.ModelAdmin):
    list_display = ['name']

class WeeklyMenuAdmin(admin.ModelAdmin):
    list_display = ['week', 'day', 'main_dish_1', 'main_dish_2', 'dessert']
    list_filter = ['day', 'week']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'order_date', 'main_dish', 'salad', 'other_dish', 'side_dish']
    list_filter = ['user', 'order_date']

class WhatsAppGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'group_id', 'phone_number']
    list_filter = ['name']

class EventLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'event_type', 'description']
    list_filter = ['timestamp', 'event_type']

class GroupNotificationAdmin(admin.ModelAdmin):
    list_display = ['group', 'message', 'send_date', 'status', 'notification_type']
    list_filter = ['group', 'send_date', 'status', 'notification_type']

class AppStateAdmin(admin.ModelAdmin):
    list_display = ['id', 'current_week']


# Define un inline para mostrar UserProfile en el panel de User
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de usuario'


class MembershipInline(admin.TabularInline):
    model = Membership
    fk_name = "user"
    extra = 0
    fields = ("organization", "role", "is_active")
    autocomplete_fields = ("organization",)

# Define una clase de administración personalizada
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, MembershipInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'menu_status')  # Agrega 'menu_status'

    def menu_status(self, obj):
        return obj.userprofile.menu
    menu_status.boolean = True  # Muestra como un ícono de True/False
    menu_status.short_description = 'Menu Habilitado'  # Nombre de la columna

# Re-registra el modelo User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Salad, SaladAdmin)
admin.site.register(OtherDish, OtherDishAdmin)
admin.site.register(SideDish, SideDishAdmin)
admin.site.register(WeeklyMenu, WeeklyMenuAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(EventLog, EventLogAdmin)
admin.site.register(AppState, AppStateAdmin)


# NOTIFICATIONS section via proxy models
class WhatsAppGroupProxy(WhatsAppGroup):
    class Meta:
        proxy = True
        verbose_name = "Whats app group"
        verbose_name_plural = "Whats app groups"
        app_label = "notifications"


class GroupNotificationProxy(GroupNotification):
    class Meta:
        proxy = True
        verbose_name = "Group notification"
        verbose_name_plural = "Group notifications"
        app_label = "notifications"


@admin.register(WhatsAppGroupProxy)
class WhatsAppGroupProxyAdmin(WhatsAppGroupAdmin):
    pass


@admin.register(GroupNotificationProxy)
class GroupNotificationProxyAdmin(GroupNotificationAdmin):
    pass


# Hidden admin for real Organization model to enable autocomplete
@admin.register(Organization)
class OrganizationHiddenAdmin(admin.ModelAdmin):
    search_fields = ("name",)

    def get_model_perms(self, request):
        return {}


@admin.register(Membership)
class MembershipHiddenAdmin(admin.ModelAdmin):
    search_fields = ("user__username", "organization__name")

    def get_model_perms(self, request):
        return {}
