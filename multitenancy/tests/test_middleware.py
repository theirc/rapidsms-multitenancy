from django.http import Http404
from django.test import TestCase

import mock
from model_mommy import mommy
from rapidsms.tests.harness.base import CreateDataMixin

from ..middleware import MultitenancyMiddleware


class MiddlewareTest(CreateDataMixin, TestCase):

    def setUp(self):
        self.group = mommy.make('TenantGroup')
        self.tenant = mommy.make('Tenant', group=self.group)
        self.mm = MultitenancyMiddleware()
        self.request = mock.Mock()
        self.view_kwargs = {
            'group_slug': self.group.slug,
            'tenant_slug': self.tenant.slug,
        }

    def call_process_view(self):
        return self.mm.process_view(
            request=self.request,
            view_func=mock.Mock(),
            view_args=[],
            view_kwargs=self.view_kwargs
        )

    def test_if_tenant_and_group_slugs_present_then_tenant_is_added_to_request(self):
        result = self.call_process_view()

        # result should be None, so that view will get called
        self.assertEqual(result, None)
        # tenant object is added to request.tenants
        self.assertEqual(self.request.tenants, [self.tenant])

    def test_wrong_group_raises_404(self):
        wrong_group = mommy.make('TenantGroup')
        self.view_kwargs['group_slug'] = wrong_group.slug

        with self.assertRaises(Http404):
            self.call_process_view()

    def test_invalid_tenant_slug_raises_404(self):
        self.view_kwargs['tenant_slug'] = 'invalid-tenant'

        with self.assertRaises(Http404):
            self.call_process_view()

    def test_valid_tenant_slug_but_missing_group_slug_raises_404(self):
        del self.view_kwargs['group_slug']

        with self.assertRaises(Http404):
            self.call_process_view()

    def test_slug_is_case_insensitive(self):
        self.view_kwargs['group_slug'] = self.view_kwargs['group_slug'].upper()
        self.view_kwargs['tenant_slug'] = self.view_kwargs['tenant_slug'].upper()

        result = self.call_process_view()

        # result should be None, so that view will get called
        self.assertEqual(result, None)
        # tenants object is added to request
        self.assertEqual(self.request.tenants, [self.tenant])

    def test_no_slugs_means_tenants_should_be_none(self):
        del self.view_kwargs['group_slug']
        del self.view_kwargs['tenant_slug']

        result = self.call_process_view()

        # result should be None, so that view will get called
        self.assertEqual(result, None)
        self.assertEqual(self.request.tenants, None)

    def test_only_group_slug_then_tenants_added_to_request(self):
        """
        If only a group slug is given, then provide a queryset of that group's tenants
        """
        del self.view_kwargs['tenant_slug']

        result = self.call_process_view()

        # result should be None, so that view will get called
        self.assertEqual(result, None)
        self.assertEqual(list(self.request.tenants), list(self.group.tenants.all()))

    def test_invalid_group_slug_raises_404(self):
        del self.view_kwargs['tenant_slug']
        self.view_kwargs['group_slug'] = 'invalid-slug'

        with self.assertRaises(Http404):
            self.call_process_view()
