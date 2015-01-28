from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .auth import get_user_groups, get_user_tenants


@login_required
def group_selection(request):
    """Allow user to select a TenantGroup if they have more than one."""

    groups = get_user_groups(request.user)
    count = len(groups)
    if count == 1:
        # Redirect to the detail page for this group
        return redirect(groups[0])
    context = {
        'groups': groups,
        'count': count,
    }
    return render(request, 'multitenancy/group-landing.html', context)


@login_required
def group_dashboard(request, group_slug):
    """Dashboard for managing a TenantGroup."""
    groups = get_user_groups(request.user)
    group = get_object_or_404(groups, slug=group_slug)
    tenants = get_user_tenants(request.user, group)
    can_edit_group = request.user.has_perm('multitenancy.change_tenantgroup', group)
    count = len(tenants)
    if count == 1:
        # Redirect to the detail page for this tenant
        return redirect(tenants[0])
    context = {
        'group': group,
        'tenants': tenants,
        'count': count,
        'can_edit_group': can_edit_group,
    }
    return render(request, 'multitenancy/group-detail.html', context)


@login_required
def tenant_dashboard(request, group_slug, tenant_slug):
    """Dashboard for managing a tenant."""
    groups = get_user_groups(request.user)
    group = get_object_or_404(groups, slug=group_slug)
    tenants = get_user_tenants(request.user, group)
    tenant = get_object_or_404(tenants, slug=tenant_slug)
    can_edit_tenant = request.user.has_perm('multitenancy.change_tenant', tenant)
    context = {
        'group': group,
        'tenant': tenant,
        'can_edit_tenant': can_edit_tenant,
    }
    return render(request, 'multitenancy/tenant-detail.html', context)
