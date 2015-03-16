from django.contrib import admin
from django.test import TestCase

from mock import Mock
from model_mommy import mommy

from ..admin import TenantAdmin, TenantGroupAdmin
from ..models import Tenant, TenantGroup, TenantRole


class TenantGroupAdminTestCase(TestCase):

    def setUp(self):
        self.tenant_group = mommy.make('TenantGroup')
        self.user = mommy.make('User', is_staff=True)

    def get_tenant_group_admin_queryset(self, user=None):
        """Helper function to get queryset for TenantGroupAdmin."""
        tenant_group_admin = TenantGroupAdmin(TenantGroup, admin.site)
        request = Mock()
        request.user = user or self.user
        return tenant_group_admin.get_queryset(request)

    def test_staff_sees_no_groups(self):
        """Nonmanagers should see no groups."""
        qs = self.get_tenant_group_admin_queryset()
        self.assertNotIn(self.tenant_group, qs)

    def test_tenant_manager_cant_see_groups(self):
        """Tenant Managers should not be able to see groups."""
        tenant = mommy.make('Tenant', group=self.tenant_group)
        mommy.make('TenantRole', group=self.tenant_group, tenant=tenant,
                   user=self.user, role=TenantRole.ROLE_TENANT_MANAGER)
        qs = self.get_tenant_group_admin_queryset()
        self.assertNotIn(self.tenant_group, qs)

    def test_group_manager_sees_its_groups(self):
        """Group Managers should see their group, but no other groups."""
        other_group = mommy.make('TenantGroup')
        mommy.make('TenantRole', group=self.tenant_group,
                   user=self.user, role=TenantRole.ROLE_GROUP_MANAGER)
        qs = self.get_tenant_group_admin_queryset()
        self.assertIn(self.tenant_group, qs)
        self.assertNotIn(other_group, qs)

    def test_superuser_sees_all_groups_even_if_also_a_manager(self):
        """Superusers should see all groups, even if they are also a Manager"""
        other_group = mommy.make('TenantGroup')
        self.user.is_superuser = True
        self.user.save()
        mommy.make('TenantRole', group=self.tenant_group,
                   user=self.user, role=TenantRole.ROLE_GROUP_MANAGER)
        qs = self.get_tenant_group_admin_queryset()
        self.assertIn(self.tenant_group, qs)
        self.assertIn(other_group, qs)


class TenantAdminTestCase(TestCase):

    def setUp(self):
        self.tenant = mommy.make('Tenant')
        self.user = mommy.make('User', is_staff=True)

    def get_tenant_admin_queryset(self, user=None):
        """Helper function to get queryset for TenantAdmin."""
        tenant_admin = TenantAdmin(Tenant, admin.site)
        request = Mock()
        request.user = user or self.user
        return tenant_admin.get_queryset(request)

    def test_staff_sees_no_tenants(self):
        """Nonmanagers should see no tenants."""
        qs = self.get_tenant_admin_queryset()
        self.assertNotIn(self.tenant, qs)

    def test_tenant_manager_sees_its_tenants(self):
        """Tenant Managers should see their tenant, but no other tenants."""
        other_tenant_same_group = mommy.make('Tenant', group=self.tenant.group)
        other_tenant = mommy.make('Tenant')
        mommy.make('TenantRole', group=self.tenant.group, tenant=self.tenant,
                   user=self.user, role=TenantRole.ROLE_TENANT_MANAGER)
        qs = self.get_tenant_admin_queryset()
        self.assertIn(self.tenant, qs)
        self.assertNotIn(other_tenant_same_group, qs)
        self.assertNotIn(other_tenant, qs)

    def test_group_manager_sees_its_tenants(self):
        """Group Managers should see all tenants in their group, but no other groups."""
        tenant_in_same_group = mommy.make('Tenant', group=self.tenant.group)
        other_tenant = mommy.make('Tenant')
        mommy.make('TenantRole', group=self.tenant.group,
                   user=self.user, role=TenantRole.ROLE_GROUP_MANAGER)
        qs = self.get_tenant_admin_queryset()
        self.assertIn(self.tenant, qs)
        self.assertIn(tenant_in_same_group, qs)
        self.assertNotIn(other_tenant, qs)

    def test_dual_manager_sees_its_tenants(self):
        """Group Managers can also be made Tenant Managers of tenants in other groups."""
        tenant1 = mommy.make('Tenant')
        other_tenant_in_tenant1_group = mommy.make('Tenant', name='other', group=tenant1.group)
        other_tenant = mommy.make('Tenant')
        mommy.make('TenantRole', group=self.tenant.group,
                   user=self.user, role=TenantRole.ROLE_GROUP_MANAGER)
        # make user a TenantManager of tenant in a different group
        mommy.make('TenantRole', group=tenant1.group, tenant=tenant1,
                   user=self.user, role=TenantRole.ROLE_TENANT_MANAGER)
        qs = self.get_tenant_admin_queryset()
        self.assertIn(self.tenant, qs)
        self.assertIn(tenant1, qs)
        self.assertNotIn(other_tenant_in_tenant1_group, qs)
        self.assertNotIn(other_tenant, qs)

    def test_superuser_sees_all_tenants_even_if_also_a_manager(self):
        """Superusers should see all tenants, even if they are also a Manager"""
        other_tenant = mommy.make('Tenant')
        self.user.is_superuser = True
        self.user.save()
        mommy.make('TenantRole', group=self.tenant.group, tenant=self.tenant,
                   user=self.user, role=TenantRole.ROLE_TENANT_MANAGER)
        qs = self.get_tenant_admin_queryset()
        self.assertIn(self.tenant, qs)
        self.assertIn(other_tenant, qs)
