from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def in_group(context, group_name):
    request = context.get("request")
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()
