from StringIO import StringIO

from django.core.management import call_command
from django.test import TestCase

from model_mommy import mommy

from multitenancy.models import BackendLink

INSTALLED_BACKENDS = {
    "message_tester": {
        "ENGINE": "rapidsms.backends.database.DatabaseBackend",
    },
}


class UpdateBackendLinksTest(TestCase):

    def setUp(self):
        self.output = StringIO()

    def test_no_backends_then_no_links(self):
        with self.settings(INSTALLED_BACKENDS={}):
            call_command('update_backend_links', stdout=self.output)
        self.assertEqual(BackendLink.all_tenants.count(), 0)
        self.assertEqual(self.output.getvalue(), '')

    def test_adds_links_to_new_backends(self):
        with self.settings(INSTALLED_BACKENDS=INSTALLED_BACKENDS):
            call_command('update_backend_links', stdout=self.output)
        self.assertEqual(BackendLink.all_tenants.count(), 1)
        self.assertEqual(self.output.getvalue(), 'Added multitenant backend link message_tester\n')

    def test_dont_add_links_if_already_created(self):
        backend = mommy.make('Backend', name='message_tester')
        link = mommy.make('BackendLink', backend=backend)
        with self.settings(INSTALLED_BACKENDS=INSTALLED_BACKENDS):
            call_command('update_backend_links', stdout=self.output)
        # still only 1 link
        self.assertEqual(BackendLink.all_tenants.get(), link)
        self.assertEqual(self.output.getvalue(), '')

    def test_can_turn_off_output_with_verbosity_flag(self):
        with self.settings(INSTALLED_BACKENDS=INSTALLED_BACKENDS):
            call_command('update_backend_links', verbosity=0, stdout=self.output)
        self.assertEqual(BackendLink.all_tenants.count(), 1)
        self.assertEqual(self.output.getvalue(), '')
