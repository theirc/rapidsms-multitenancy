from django.test import TestCase

from model_mommy import mommy

from ..forms import TenantForm


class TenantFormTest(TestCase):

    def test_if_no_backends_then_none_shown_as_choices(self):
        form = TenantForm()
        # remove blank choice
        available_backends = [choice for choice, value in list(form.fields['backend_link'].choices)
                              if choice != '']
        self.assertEqual(available_backends, [])

    def test_backend_shows_up_as_a_choice(self):
        backend_link = mommy.make('BackendLink')
        form = TenantForm()
        self.assertIn(backend_link.backend.name,
                      [choice[1] for choice in form.fields['backend_link'].choices])

    def test_form_doesnt_display_used_backends(self):
        """If a backend is already associated with a Tenant, it cannot be reused"""
        backend_link = mommy.make('BackendLink')
        tenant = mommy.make('Tenant')
        tenant.backendlink_set.add(backend_link)
        form = TenantForm()
        # remove blank choice
        available_backends = [choice for choice, value in list(form.fields['backend_link'].choices)
                              if choice != '']
        # choices should be empty since all backends are used already
        self.assertEqual(available_backends, [])

    def test_valid_form(self):
        group = mommy.make('TenantGroup')
        backend_link = mommy.make('BackendLink')
        form = TenantForm(data={
            'name': 'randomname',
            'slug': 'randomname',
            'group': group.pk,
            'backend_link': backend_link.pk,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_saving_form_updates_backends(self):
        group = mommy.make('TenantGroup')
        old_link, new_link = mommy.make('BackendLink', _quantity=2)
        tenant = mommy.make('Tenant', backendlink_set=[old_link])
        form = TenantForm(
            instance=tenant,
            data={
                'name': 'randomname',
                'slug': 'randomname',
                'group': group.pk,
                'backend_link': new_link.pk,
            })
        self.assertTrue(form.is_valid(), form.errors)
        updated_tenant = form.save()
        # it should clear old backends
        self.assertNotIn(old_link, updated_tenant.backendlink_set.all())
        # it should add requested backends
        self.assertIn(new_link, updated_tenant.backendlink_set.all())
