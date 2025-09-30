from django.contrib import admin
from .models import Client
from ruralapp.models import Organization, Membership


class OrganizationProxy(Organization):
	class Meta:
		proxy = True
		verbose_name = "Organization"
		verbose_name_plural = "Organizations"
		app_label = "management"


class MembershipProxy(Membership):
	class Meta:
		proxy = True
		verbose_name = "Membership"
		verbose_name_plural = "Memberships"
		app_label = "management"

# Register your models here.
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "employees")


@admin.register(OrganizationProxy)
class OrganizationAdmin(admin.ModelAdmin):
	list_display = ("name", "type", "is_active", "created_at")
	list_filter = ("type", "is_active")
	search_fields = ("name",)
	ordering = ("name",)


@admin.register(MembershipProxy)
class MembershipAdmin(admin.ModelAdmin):
	list_display = ("user", "organization", "role", "is_active", "created_at")
	list_filter = ("role", "is_active", "organization__type")
	search_fields = ("user__username", "user__email", "organization__name")
	autocomplete_fields = ("user", "organization")
