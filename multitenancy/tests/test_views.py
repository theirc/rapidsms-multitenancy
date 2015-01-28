from django.core.urlresolvers import reverse
from django.test import TestCase

from model_mommy import mommy

from .. import models


class GroupViewMixin(object):
    """Mixin for testing group related views."""

    url_name = ''

    def setUp(self):
        self.group = mommy.make('TenantGroup')
        self.user = mommy.make('User')
        self.user.set_password('test')
        self.user.save()
        self.client.login(username=self.user.username, password='test')
        super(GroupViewMixin, self).setUp()

    def url(self, **kwargs):
        return reverse(self.url_name, kwargs=kwargs)


class TenantViewMixin(GroupViewMixin):
    """Extension to handle tenant related views."""

    def setUp(self):
        super(TenantViewMixin, self).setUp()
        self.tenant = mommy.make('Tenant', group=self.group)


class GroupLandingViewTestCase(GroupViewMixin, TestCase):
    """Selection page for users with multiple groups."""

    url_name = 'group-landing'

    def assertGroupsEqual(self, response, expected):
        """Assert groups in the response context."""
        self.assertEqual(response.status_code, 200)
        expected = sorted(expected, key=lambda x: x.pk)
        found = sorted(response.context['groups'], key=lambda x: x.pk)
        self.assertEqual(found, expected)

    def test_get_page(self):
        """Users with multiple groups can get the page to pick an group."""
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)
        other = mommy.make('TenantGroup')
        mommy.make('TenantRole',
                   group=other, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)
        # Create group with no relation to the user
        mommy.make('TenantGroup')
        with self.assertTemplateUsed('multitenancy/group-landing.html'):
            response = self.client.get(self.url())
            self.assertGroupsEqual(response, [self.group, other])

    def test_superuser_get_page(self):
        """Super users will see all groups."""
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(update_fields=('is_staff', 'is_superuser'))
        other = mommy.make('TenantGroup')
        with self.assertTemplateUsed('multitenancy/group-landing.html'):
            response = self.client.get(self.url())
            self.assertGroupsEqual(response, [self.group, other])

    def test_inactive_user_get_page(self):
        """Inactive users will see no groups."""
        self.user.is_active = False
        self.user.save(update_fields=('is_active', ))
        with self.assertTemplateUsed('multitenancy/group-landing.html'):
            response = self.client.get(self.url())
            self.assertGroupsEqual(response, [])
            self.assertContains(response, 'do not have permissions to manage any groups')

    def test_single_group_get_page(self):
        """Redirect user to group if there is only one."""
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)
        response = self.client.get(self.url())
        self.assertRedirects(response, self.group.get_absolute_url())

    def test_mixed_roles_get_page(self):
        """Users with roles on two groups need to select groups."""
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)
        other = mommy.make('TenantGroup')
        other_tenant = mommy.make('Tenant', group=other)
        mommy.make('TenantRole',
                   group=other, tenant=other_tenant, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)
        with self.assertTemplateUsed('multitenancy/group-landing.html'):
            response = self.client.get(self.url())
            self.assertGroupsEqual(response, [self.group, other])

    def test_no_groups_get_page(self):
        """Users with no groups will be shown an error message."""
        with self.assertTemplateUsed('multitenancy/group-landing.html'):
            response = self.client.get(self.url())
            self.assertContains(response, 'do not have permissions to manage any groups')


class GroupDetailViewTestCase(GroupViewMixin, TestCase):
    """Group detail and tenant listing page."""

    url_name = 'group-detail'

    def assertTenantsEqual(self, response, expected):
        """Assert tenants in the response context."""
        self.assertEqual(response.status_code, 200)
        expected = sorted(expected, key=lambda x: x.pk)
        found = sorted(response.context['tenants'], key=lambda x: x.pk)
        self.assertEqual(found, expected)

    def test_get_page(self):
        """Group managers will see all the tenants for the group."""
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)
        tenant = mommy.make('Tenant', group=self.group)
        other = mommy.make('Tenant', group=self.group)
        # Create tenant with no relation to the user
        mommy.make('Tenant')
        with self.assertTemplateUsed('multitenancy/group-detail.html'):
            response = self.client.get(self.url(group_slug=self.group.slug))
            self.assertTenantsEqual(response, [tenant, other])

    def test_no_group_permission(self):
        """This page with 404 if the user is not associated with the group."""
        response = self.client.get(self.url(group_slug=self.group.slug))
        self.assertEqual(response.status_code, 404)

    def test_superuser_get_page(self):
        """Super users will see all tenants for the group."""
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(update_fields=('is_staff', 'is_superuser'))
        tenant = mommy.make('Tenant', group=self.group)
        other = mommy.make('Tenant', group=self.group)
        with self.assertTemplateUsed('multitenancy/group-detail.html'):
            response = self.client.get(self.url(group_slug=self.group.slug))
            self.assertTenantsEqual(response, [tenant, other])

    def test_tenant_manager_single(self):
        """A user managing a single tenant will be directed to the tenant page."""
        tenant = mommy.make('Tenant', group=self.group)
        mommy.make('TenantRole',
                   group=self.group, tenant=tenant, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)
        response = self.client.get(self.url(group_slug=self.group.slug))
        self.assertRedirects(response, tenant.get_absolute_url())

    def test_tenant_manager_multiple(self):
        """A user managing a multiples tenants will see their tenants."""
        tenant = mommy.make('Tenant', group=self.group)
        other = mommy.make('Tenant', group=self.group)
        mommy.make('TenantRole',
                   group=self.group, tenant=tenant, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)
        mommy.make('TenantRole',
                   group=self.group, tenant=other, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)
        with self.assertTemplateUsed('multitenancy/group-detail.html'):
            response = self.client.get(self.url(group_slug=self.group.slug))
            self.assertTenantsEqual(response, [tenant, other])


class TenantDetailViewTestCase(TenantViewMixin, TestCase):
    """Tenant detail page."""

    url_name = 'tenant-detail'

    def test_tenant_manager_get_page(self):
        """Tenant managers will use this page to manage their tenants."""
        mommy.make('TenantRole',
                   group=self.group, tenant=self.tenant, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)
        with self.assertTemplateUsed('multitenancy/tenant-detail.html'):
            response = self.client.get(self.url(group_slug=self.group.slug, tenant_slug=self.tenant.slug))
            self.assertEqual(response.status_code, 200)

    def test_group_manager_get_page(self):
        """Group managers also have access to their tenant pages."""
        mommy.make('TenantRole',
                   group=self.group, user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)
        with self.assertTemplateUsed('multitenancy/tenant-detail.html'):
            response = self.client.get(self.url(group_slug=self.group.slug, tenant_slug=self.tenant.slug))
            self.assertEqual(response.status_code, 200)

    def test_superuser_get_page(self):
        """Super users have access to all tenant pages."""
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(update_fields=('is_staff', 'is_superuser'))
        with self.assertTemplateUsed('multitenancy/tenant-detail.html'):
            response = self.client.get(self.url(group_slug=self.group.slug, tenant_slug=self.tenant.slug))
            self.assertEqual(response.status_code, 200)

    def test_wrong_group(self):
        """Users which don't have access to the group will see a 404."""
        mommy.make('TenantRole',
                   user=self.user,
                   role=models.TenantRole.ROLE_GROUP_MANAGER)
        response = self.client.get(self.url(group_slug=self.group.slug, tenant_slug=self.tenant.slug))
        self.assertEqual(response.status_code, 404)

    def test_wrong_tenant(self):
        """Users which don't have access to the tenant will see a 404."""
        other = mommy.make('Tenant', group=self.group)
        mommy.make('TenantRole',
                   group=self.group, tenant=other, user=self.user,
                   role=models.TenantRole.ROLE_TENANT_MANAGER)
        response = self.client.get(self.url(group_slug=self.group.slug, tenant_slug=self.tenant.slug))
        self.assertEqual(response.status_code, 404)
