from django.apps import apps
from django.db import models

from .models import TenantRole, TenantGroup, Tenant


def get_user_groups(user):
    """Return the set of associated TenantGroups for the given user."""
    if user.is_active and user.is_authenticated():
        if user.is_superuser:
            return TenantGroup.objects.all()
        else:
            return TenantGroup.objects.filter(tenantrole__user=user).distinct()
    else:
        return TenantGroup.objects.none()


def get_user_tenants(user, group):
    """Return the set of associated Tenants for the given user and group."""
    if user.is_active and user.is_authenticated():
        if user.is_superuser or is_group_manager(user, group.pk):
            return Tenant.objects.filter(group=group)
        else:
            return Tenant.objects.filter(group=group, tenantrole__user=user).distinct()
    else:
        return Tenant.objects.none()


def get_user_roles(user):
    """Return a list of all of the user's roles."""
    if not hasattr(user, '_role_cache'):
        user._role_cache = list(TenantRole.objects.filter(user=user).values_list(
            'group', 'role', 'tenant'))
    return user._role_cache


def is_group_manager(user, group=None):
    """Returns True if user is a group manager either for the group or any group."""
    roles = get_user_roles(user)
    return any(x[1] == TenantRole.ROLE_GROUP_MANAGER and (not group or x[0] == group) for x in roles)


def is_tenant_manager(user, group=None, tenant=None):
    """Returns True if user is a tenant manager either for the group/tenant or any group/tenant."""
    roles = get_user_roles(user)
    return any(
        x[1] == TenantRole.ROLE_TENANT_MANAGER and
        (not group or x[0] == group) and
        (not tenant or x[2] == tenant)
        for x in roles
    )


class TenantRolesBackend(object):
    """Custom authentication backend to handle role-based permissions. """

    def authenticate(self, *args, **kwargs):  # pragma: no cover
        """Dummy method, required for all auth backends."""
        return None

    def get_user(self, user_id):  # pragma: no cover
        """Dummy method, required for all auth backends."""
        return None

    def has_perm(self, user, perm, obj=None):
        if not user.is_active:
            return False

        if user.is_superuser:
            return True

        app_label, permission_label = perm.split('.', 1)
        action, model_label = permission_label.split('_', 1)
        model = apps.get_model(app_label, model_label)
        if obj is None:
            group_manager = is_group_manager(user)
            tenant_manager = is_tenant_manager(user)
            if model == TenantGroup:
                return group_manager and action == 'change'
            elif model == Tenant:
                return group_manager or (tenant_manager and action == 'change')
            elif model == TenantRole:
                return group_manager
        else:
            group = None
            tenant = None
            if isinstance(obj, TenantGroup):
                group = obj.pk
            elif isinstance(obj, Tenant):
                tenant = obj.pk
                group = obj.group_id
            else:
                # Check if object has FK to group or tenant
                for field in obj.__class__._meta.fields:
                    if isinstance(field, models.ForeignKey):
                        if field.rel.to == TenantGroup:
                            group = getattr(obj, field.get_attname())
                        elif field.rel.to == Tenant:
                            tenant = getattr(obj, field.get_attname())
                            if getattr(obj, field.name):
                                group = getattr(obj, field.name).group_id
            group_manager = is_group_manager(user, group=group)
            tenant_manager = is_tenant_manager(user, group=group, tenant=tenant)
            if tenant:
                # Has permission for the tenant if manager or has explicit tenant permission
                return group_manager or tenant_manager
            elif group:
                return group_manager
        # User does not have permission from our backend.
        # Other backends will check for additional permissions
        return False

    def has_module_perms(self, user, app_label):
        if not user.is_active:
            return False

        if user.is_superuser:
            return True

        config = apps.get_app_config(app_label)
        group_manager = is_group_manager(user)
        tenant_manager = is_tenant_manager(user)
        related = any(
            m in (TenantGroup, Tenant, TenantRole)
            for m in config.get_models())
        return (group_manager or tenant_manager) and related
