from django import template
from ..authz import user_has_roles

register = template.Library()


@register.simple_tag(takes_context=True)
def has_role(context, role):
    request = context.get("request")
    if not request:
        return False
    return user_has_roles(request.user, getattr(request, "current_org", None), [role])
