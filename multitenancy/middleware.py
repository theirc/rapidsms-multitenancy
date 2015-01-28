from django.shortcuts import get_object_or_404

from .models import Tenant, TenantGroup


class MultitenancyMiddleware(object):
    """
    Pulls group_slug and tenant_slug out to check if they exist and are valid.

    If only the group_slug is provided, then set request.tenants to queryset
    of that group's tenants.

    If both are provided, then set request.tenants to a 1-item list of the requested
    Tenant.

    Also set request.tenant_slug and request.group_slug if each exists, to make it
    easier to create urls.

    Returns a 404 if the group or tenant does not exist.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.tenants = request.tenant_slug = request.group_slug = None
        if 'tenant_slug' in view_kwargs:
            group_slug = view_kwargs.get('group_slug', '')
            tenant_slug = view_kwargs['tenant_slug']
            tenant = get_object_or_404(
                Tenant,
                slug__iexact=tenant_slug,
                group__slug__iexact=group_slug
            )
            request.tenants = [tenant]
            request.tenant_slug = tenant.slug
            request.group_slug = tenant.group.slug
        elif 'group_slug' in view_kwargs:
            # Only group, no tenant -> set tenants to a queryset of this group's tenants
            group_slug = view_kwargs['group_slug']
            group = get_object_or_404(TenantGroup, slug__iexact=group_slug)
            request.tenants = group.tenants.all()
            request.group_slug = group.slug
