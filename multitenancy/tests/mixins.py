from rapidsms.models import Backend, Contact
from rapidsms.router import lookup_connections

from ..models import BackendLink, ContactLink


class MultitenancyMixin(object):
    """Augment RapidSMS test infrastructure to link any Backends to BackendLinks.
    """

    def create_backend(self, data=None, tenant=None):
        """Whenever we create a backend, we should also create a BackendLink"""
        data = data or {}
        backend = super(MultitenancyMixin, self).create_backend(data)
        if tenant:
            BackendLink.objects.by_tenant(tenant=tenant).create(backend=backend)
        else:
            BackendLink.all_tenants.create(backend=backend)
        return backend

    def create_contact(self, data=None, tenant=None):
        """ Create and return a Contact object. A random ``name`` will be created
        if not specified in ``data`` attribute. For Multitenancy purposes, also
        create a ContactLink object.

        :param data: Optional dictionary of field name/value pairs to
            pass to the object's ``create`` method."""
        data = data or {}
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(data)
        contact = Contact.objects.create(**defaults)
        if tenant:
            ContactLink.objects.by_tenant(tenant=tenant).create(contact=contact)
        else:
            ContactLink.all_tenants.create(contact=contact)
        return contact

    def lookup_connections(self, identities, backend='mockbackend'):
        """Looks up a connection, creating both the connection and backend if either
        does not exist. For multitenancy, we also need to create a BackendLink.
        """
        if isinstance(backend, basestring):
            backend, _ = Backend.objects.get_or_create(name=backend)
        BackendLink.all_tenants.get_or_create(backend=backend)
        connections = lookup_connections(backend, identities)
        return connections
