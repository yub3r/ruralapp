from django.utils.deprecation import MiddlewareMixin
from .models import Organization


class CurrentOrganizationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        org_id = request.session.get("current_org_id")
        request.current_org = None
        if org_id:
            try:
                request.current_org = Organization.objects.get(id=org_id, is_active=True)
            except Organization.DoesNotExist:
                request.current_org = None
        return None
