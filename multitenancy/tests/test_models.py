from django.db import models, IntegrityError
from django.test import TestCase

from model_mommy import mommy
from rapidsms.backends.database import DatabaseBackend
from rapidsms.backends.database.models import BackendMessage
from rapidsms.tests.harness import CustomRouterMixin

from ..models import MultitenantIncompatiblityError, TenantEnabled


class TenantModelTest(TestCase):

    def setUp(self):
        self.group = mommy.make('TenantGroup')
        self.tenant = mommy.make('Tenant', group=self.group)

    def test_unicode(self):
        self.assertEqual(str(self.group), self.group.name)
        self.assertIn(self.tenant.name, str(self.tenant))
        self.assertIn(self.group.name, str(self.tenant))

    def test_absolute_url(self):
        self.assertTrue(self.group.get_absolute_url())
        self.assertTrue(self.tenant.get_absolute_url())

    def test_tenant_unique_within_group(self):
        g2 = mommy.make('TenantGroup')
        # Creating a tenant with the same name and slug is OK
        t2 = mommy.make('Tenant', group=g2, name=self.tenant.name, slug=self.tenant.slug)
        self.assertTrue(t2)
        with self.assertRaises(IntegrityError):
            # but not in the same group
            mommy.make('Tenant', group=g2, name=self.tenant.name, slug=self.tenant.slug)


class BackendTest(CustomRouterMixin, TestCase):

    backends = {
        'tenant_backend': {'ENGINE': DatabaseBackend},
        'other_backend': {'ENGINE': DatabaseBackend},
    }

    def setUp(self):
        # create tenant
        self.tenant = mommy.make('Tenant')
        # create backend
        self.tenant_backend = self.create_backend(data={'name': 'tenant_backend'})
        self.tenant_backend_link = mommy.make('BackendLink', tenant=self.tenant, backend=self.tenant_backend)

    def test_get_tenant_assoicated_with_backend(self):
        self.assertEqual(self.tenant_backend_link.tenant, self.tenant)

    def test_get_list_of_backends(self):
        second_backend = mommy.make('BackendLink')
        self.tenant.backendlink_set.add(second_backend)
        self.assertIn(self.tenant_backend_link.backend.name, self.tenant.get_backend_names())
        self.assertIn(second_backend.backend.name, self.tenant.get_backend_names())

    def test_tenant_gets_messages_to_its_backend(self):
        # create second backend
        other_backend = self.create_backend(data={'name': 'other_backend'})
        mommy.make('BackendLink', backend=other_backend)
        # receive message and send response via both backends
        tenant_conn = self.lookup_connections(identities=['5551212'], backend=self.tenant_backend)[0]
        other_conn = self.lookup_connections(identities=['5551212'], backend=other_backend)[0]
        self.send('echo tenant message', tenant_conn)
        self.send('echo other message', other_conn)
        # only messages via associated backend show up in query
        expected_count = 1
        tenant_backend_names = [b.name for b in self.tenant.get_backends()]
        self.assertEqual(expected_count, BackendMessage.objects.filter(name__in=tenant_backend_names).count())


class TestModel(TenantEnabled):
    """A Test Model that inherits from TenantEnabled so we can test functionality."""
    name = models.CharField(max_length=20)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'multitenancy'
        get_latest_by = 'date'


class TenantEnabledTest(TestCase):

    def setUp(self):
        self.tenant = mommy.make('Tenant')
        self.instance = TestModel.all_tenants.create(name='My Name', tenant=self.tenant)
        # create another tenant and instance so we can show that queries are tenant-specific
        self.other_tenant = mommy.make('Tenant')
        self.other_instance = TestModel.all_tenants.create(name='My Name', tenant=self.other_tenant)

    def test_first_call_on_manager_needs_to_be_by_tenant(self):
        """Calls to the manager should only succeed if by_tenant is the first call in the chain."""
        with self.assertRaises(MultitenantIncompatiblityError):
            # get_queryset is the most generic call, since all other methods call it
            TestModel.objects.get_queryset()
        with self.assertRaises(MultitenantIncompatiblityError):
            # by_tenant is missing
            TestModel.objects.all()
        with self.assertRaises(MultitenantIncompatiblityError):
            # by_tenant is not first
            TestModel.objects.all().by_tenant(self.tenant)
        # should succeed if by_tenant is first
        instances = TestModel.objects.by_tenant(self.tenant).all()
        self.assertEqual(len(instances), 1)
        # all_tenants works
        all_instances = TestModel.all_tenants.all()
        self.assertEqual(len(all_instances), 2)

    # Run through the various QuerySet methods to make sure they all work as expected

    def test_count(self):
        self.assertEqual(TestModel.objects.by_tenant(self.tenant).count(), 1)

    def test_datetimes(self):
        datetimes = TestModel.objects.by_tenant(self.tenant).datetimes('date', 'year')
        self.assertEqual(len(datetimes), 1)

    def test_get_or_create(self):
        instance, created = TestModel.objects.by_tenant(self.tenant).get_or_create(name='blah')
        self.assertEqual(instance.tenant, self.tenant)
        self.assertTrue(created)
        self.assertEqual(instance.name, 'blah')

    def test_create(self):
        instance = TestModel.objects.by_tenant(self.tenant).create()
        self.assertEqual(instance.tenant, self.tenant)
        # Also OK if you specify the tenant in the create kwargs
        instance2 = TestModel.objects.by_tenant(self.tenant).create(tenant=self.tenant)
        self.assertEqual(instance2.tenant, self.tenant)
        # Not OK if you specify a different tenant in the create kwargs
        with self.assertRaises(MultitenantIncompatiblityError):
            TestModel.objects.by_tenant(self.tenant).create(tenant=self.other_tenant)

    def test_bulk_create(self):
        instances = TestModel.objects.by_tenant(self.tenant).bulk_create([
            TestModel(name='one'),
            TestModel(name='two'),
        ])
        for instance in instances:
            self.assertEqual(instance.tenant, self.tenant)

    def test_bulk_create_fails_if_wrong_tenant(self):
        with self.assertRaises(MultitenantIncompatiblityError):
            TestModel.objects.by_tenant(self.tenant).bulk_create([
                TestModel(name='one', tenant=self.other_tenant),
                TestModel(name='two'),
            ])

    def test_filter(self):
        instances = TestModel.objects.by_tenant(self.tenant).filter(name='My Name')
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].tenant, self.tenant)

    def test_aggregate(self):
        from django.db.models import Count
        result = TestModel.objects.by_tenant(self.tenant).aggregate(count=Count('name'))
        self.assertEqual(result['count'], 1)

    def test_earliest_and_latest(self):
        earliest = TestModel.objects.by_tenant(self.tenant).earliest()
        latest = TestModel.objects.by_tenant(self.tenant).latest()
        # since there's only one object for this tenant, should be equal
        self.assertEqual(earliest, latest)
        # the same is NOT true for all_tenants
        self.assertNotEqual(TestModel.all_tenants.earliest(),
                            TestModel.all_tenants.latest())

    def test_first_and_last(self):
        first = TestModel.objects.by_tenant(self.tenant).first()
        last = TestModel.objects.by_tenant(self.tenant).last()
        # since there's only one object for this tenant, should be equal
        self.assertEqual(first, last)
        # the same is NOT true for all_tenants
        self.assertNotEqual(TestModel.all_tenants.first(),
                            TestModel.all_tenants.last())

    def test_values(self):
        values = TestModel.objects.by_tenant(self.tenant).values('tenant')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['tenant'], self.tenant.id)

    def test_values_list(self):
        values_list = TestModel.objects.by_tenant(self.tenant).values_list('tenant', flat=True)
        self.assertEqual(len(values_list), 1)
        self.assertEqual(values_list[0], self.tenant.id)

    def test_update(self):
        TestModel.objects.by_tenant(self.tenant).update(name='new name')
        self.assertEqual(TestModel.objects.by_tenant(self.tenant)[0].name, 'new name')
        self.assertEqual(TestModel.all_tenants.get(id=self.other_instance.id).name, 'My Name')

    def test_delete_and_exists(self):
        TestModel.objects.by_tenant(self.tenant).delete()
        exists = TestModel.objects.by_tenant(self.tenant).exists()
        self.assertFalse(exists)
        self.assertEqual(TestModel.all_tenants.count(), 1)
