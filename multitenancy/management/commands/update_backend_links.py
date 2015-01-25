#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from rapidsms.models import Backend
from rapidsms.conf import settings

from multitenancy.models import BackendLink


class Command(BaseCommand):
    help = "Creates an instance of the BackendLink model for each running backend."

    def handle(self, **options):
        verbosity = int(options.get("verbosity", 1))

        # fetch all multitenant backends (identified by their
        # name) that we know about
        known_backend_names = list(
            BackendLink.all_tenants.values_list("backend__name", flat=True)
        )

        # find any running backends which currently
        # don't have instances, and fill in the gaps
        for name in settings.INSTALLED_BACKENDS:
            if name not in known_backend_names:
                known_backend_names.append(name)
                backend, created = Backend.objects.get_or_create(name=name)
                backend_link = BackendLink.all_tenants.create(backend=backend)
                # log at the same level as syncdb's "created table..."
                # messages, to stay silent when called with -v 0
                if verbosity >= 1:
                    self.stdout.write(_("Added multitenant backend link %(link)s") % {'link': backend_link})
