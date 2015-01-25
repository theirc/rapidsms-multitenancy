from django.test import TestCase

from model_mommy import mommy

from .. import models
from ..auth import TenantRolesBackend


class RolePermissionsTestCase(TestCase):
    """Role based permissions."""

    def setUp(self):
        self.backend = TenantRolesBackend()
        self.group = mommy.make('TenantGroup')
        self.tenant = mommy.make('Tenant', group=self.group)
        self.user = mommy.make('User', is_staff=True)

    def assertHasPermission(self, user, permission, obj=None):
        result = self.backend.has_perm(user, permission, obj=obj)
        if obj is None:
            message = 'User does not have expected permission: {}'.format(permission)
        else:
            message = 'User does not have expected permission: {} ({})'.format(permission, obj)
        self.assertTrue(result, message)

    def assertNoPermission(self, user, permission, obj=None):
        result = self.backend.has_perm(user, permission, obj=obj)
        if obj is None:
            message = 'User has unexpected permission: {}'.format(permission)
        else:
            message = 'User has unexpected permission: {} ({})'.format(permission, obj)
        self.assertFalse(result, message)

    def test_group_manager_group_permissions(self):
        """Group managers can change their group but cannot create new ones."""
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)

        self.assertHasPermission(self.user, 'multitenancy.change_tenantgroup', self.group)
        self.assertHasPermission(self.user, 'multitenancy.delete_tenantgroup', self.group)
        # Need the generic 'change' permission to see any groups in the admin
        self.assertHasPermission(self.user, 'multitenancy.change_tenantgroup')

        self.assertNoPermission(self.user, 'multitenancy.add_tenantgroup')
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantgroup')

        other = mommy.make('TenantGroup')
        self.assertNoPermission(self.user, 'multitenancy.change_tenantgroup', other)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantgroup', other)

    def test_group_manager_role_permissions(self):
        """Group managers can add roles for their group and tenants."""
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)

        group_role = mommy.make('TenantRole',
                                group=self.group,
                                role=models.TenantRole.ROLE_GROUP_MANAGER)
        tenant_role = mommy.make('TenantRole',
                                 group=self.group, tenant=self.tenant,
                                 role=models.TenantRole.ROLE_TENANT_MANAGER)

        self.assertHasPermission(self.user, 'multitenancy.add_tenantrole')
        self.assertHasPermission(self.user, 'multitenancy.change_tenantrole', group_role)
        self.assertHasPermission(self.user, 'multitenancy.delete_tenantrole', group_role)
        self.assertHasPermission(self.user, 'multitenancy.change_tenantrole', tenant_role)
        self.assertHasPermission(self.user, 'multitenancy.delete_tenantrole', tenant_role)
        # Need the generic permissions to see them in the admin
        self.assertHasPermission(self.user, 'multitenancy.change_tenantrole')
        self.assertHasPermission(self.user, 'multitenancy.delete_tenantrole')

        other_group = mommy.make('TenantRole', role=models.TenantRole.ROLE_GROUP_MANAGER)
        other_tenant = mommy.make('TenantRole', role=models.TenantRole.ROLE_TENANT_MANAGER)
        self.assertNoPermission(self.user, 'multitenancy.change_tenantrole', other_group)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantrole', other_group)
        self.assertNoPermission(self.user, 'multitenancy.change_tenantrole', other_tenant)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantrole', other_tenant)

    def test_group_manager_tenant_permissions(self):
        """Group managers can add tenants and change any tenants for their group."""
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)

        self.assertHasPermission(self.user, 'multitenancy.add_tenant')
        self.assertHasPermission(self.user, 'multitenancy.change_tenant', self.tenant)
        self.assertHasPermission(self.user, 'multitenancy.delete_tenant', self.tenant)
        # Need the generic permissions to see them in the admin
        self.assertHasPermission(self.user, 'multitenancy.change_tenant')
        self.assertHasPermission(self.user, 'multitenancy.delete_tenant')

        other = mommy.make('Tenant')
        self.assertNoPermission(self.user, 'multitenancy.change_tenant', other)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenant', other)

    def test_tenant_manager_group_permissions(self):
        """Tenant managers cannot change their groups."""
        mommy.make('TenantRole',
                   group=self.group, tenant=self.tenant, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)

        self.assertNoPermission(self.user, 'multitenancy.change_tenantgroup', self.group)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantgroup', self.group)

        self.assertNoPermission(self.user, 'multitenancy.add_tenantgroup')
        self.assertNoPermission(self.user, 'multitenancy.change_tenantgroup')
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantgroup')

        other = mommy.make('TenantGroup')
        self.assertNoPermission(self.user, 'multitenancy.change_tenantgroup', other)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantgroup', other)

    def test_tenant_manager_role_permissions(self):
        """Tenant managers cannot add roles for the group."""
        mommy.make('TenantRole',
                   group=self.group, tenant=self.tenant, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)

        role = mommy.make('TenantRole', group=self.group, role=models.TenantRole.ROLE_GROUP_MANAGER)

        self.assertNoPermission(self.user, 'multitenancy.add_tenantrole')
        self.assertNoPermission(self.user, 'multitenancy.change_tenantrole', role)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantrole', role)

        self.assertNoPermission(self.user, 'multitenancy.change_tenantrole')
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantrole')

        other = mommy.make('TenantRole', role=models.TenantRole.ROLE_GROUP_MANAGER)
        self.assertNoPermission(self.user, 'multitenancy.change_tenantrole', other)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenantrole', other)

    def test_tenant_manager_tenant_permissions(self):
        """Tenant managers can change their tenant but not create others."""
        mommy.make('TenantRole',
                   group=self.group, tenant=self.tenant, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)

        self.assertHasPermission(self.user, 'multitenancy.change_tenant', self.tenant)
        self.assertHasPermission(self.user, 'multitenancy.delete_tenant', self.tenant)
        # Need the generic permissions to see them in the admin
        self.assertHasPermission(self.user, 'multitenancy.change_tenant')

        self.assertNoPermission(self.user, 'multitenancy.add_tenant')
        self.assertNoPermission(self.user, 'multitenancy.delete_tenant')

        other = mommy.make('Tenant')
        self.assertNoPermission(self.user, 'multitenancy.change_tenant', other)
        self.assertNoPermission(self.user, 'multitenancy.delete_tenant', other)

    def test_superuser_module_permissions(self):
        superuser = mommy.make('User', is_staff=True, is_superuser=True)

        self.assertTrue(self.backend.has_module_perms(superuser, 'multitenancy'))
        self.assertTrue(self.backend.has_module_perms(superuser, 'auth'))

    def test_group_manager_module_permissions(self):
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)
        self.assertTrue(self.backend.has_module_perms(self.user, 'multitenancy'))
        self.assertFalse(self.backend.has_module_perms(self.user, 'auth'))

    def test_tenant_manager_module_permissions(self):
        mommy.make('TenantRole',
                   group=self.group, tenant=self.tenant, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)

        self.assertTrue(self.backend.has_module_perms(self.user, 'multitenancy'))
        self.assertFalse(self.backend.has_module_perms(self.user, 'auth'))
