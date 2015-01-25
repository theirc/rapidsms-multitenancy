from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from rapidsms.models import Backend, Contact


class TenantGroup(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('group-detail', kwargs=dict(group_slug=self.slug))


class Tenant(models.Model):
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    description = models.TextField(blank=True)
    group = models.ForeignKey(TenantGroup, related_name='tenants')

    class Meta:
        unique_together = (('group', 'slug'),
                           ('group', 'name'))

    def __unicode__(self):
        return '{} ({})'.format(self.name, self.group.name)

    def get_absolute_url(self):
        return reverse('tenant-detail', kwargs=dict(group_slug=self.group.slug,
                                                    tenant_slug=self.slug))

    def add_backend(self, backend):
        "Add a RapidSMS backend to this tenant"
        if backend in self.get_backends():
            return
        backend_link, created = BackendLink.all_tenants.get_or_create(backend=backend)
        self.backendlink_set.add(backend_link)

    def get_backend_names(self):
        return u'\n'.join(b.name for b in self.get_backends())
    get_backend_names.short_description = _('Backends')

    def get_backends(self):
        return Backend.objects.filter(tenantlink__in=self.backendlink_set.all())

    @cached_property
    def primary_backend(self):
        """
        Each tenant has one external backend. This method returns that backend, by excluding
        backends associated with the message_tester.
        """
        return self.get_backends().exclude(name__startswith='mt_').first()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.backendlink_set.clear()
        # post_save signal gets called during the next statement (which is why
        # we clear backendlinks above. If we were to clear it later, then it
        # would overwrite our post_save signal in messagetester)
        super(Tenant, self).save(force_insert, force_update, using, update_fields)
        if hasattr(self, 'unsaved_backendlinks'):
            self.backendlink_set.add(*self.unsaved_backendlinks)


class TenantRole(models.Model):
    """Relation between Tenants and the users who manage them."""

    ROLE_GROUP_MANAGER = 1
    ROLE_TENANT_MANAGER = 2
    ROLE_CHOICES = (
        (ROLE_GROUP_MANAGER, _('Group Manager')),
        (ROLE_TENANT_MANAGER, _('Tenant Manager')),
    )

    group = models.ForeignKey(TenantGroup)
    tenant = models.ForeignKey(Tenant, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'is_staff': True})
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES)

    def __unicode__(self):
        return '{} ({}) - {}'.format(self.group.name, self.user.username, self.get_role_display())

    class Meta:
        index_together = (('group', 'user', ), )

    def clean(self):
        if self.role == self.ROLE_TENANT_MANAGER and not self.tenant:
            raise ValidationError(_('Tenant must be provided for Tenant Manager roles.'))
        if self.tenant_id and self.tenant.group_id != self.group_id:
            raise ValidationError(_('Assigned Tenant must belong to the related Group.'))


class MultitenantIncompatiblityError(Exception):
    pass


class TenantQuerySet(models.query.QuerySet):
    """QuerySet extension to provide filtering by Tenant"""

    tenant = None

    def __init__(self, model=None, query=None, using=None, hints=None, tenant=None):
        super(TenantQuerySet, self).__init__(model, query, using, hints)
        self.tenant = tenant

    def _clone(self, klass=None, setup=False, **kwargs):
        kwargs['tenant'] = self.tenant
        return super(TenantQuerySet, self)._clone(klass, setup, **kwargs)

    # Helper method to add our Tenant to queries
    def add_tenant_to_kwargs(self, **kwargs):
        if kwargs.get('tenant', self.tenant) != self.tenant:
            raise MultitenantIncompatiblityError(
                "Tenant provided in by_tenant (%(tenant1)s) doesn't match Tenant "
                "provided in kwargs (%(tenant2)s)"
                % {'tenant1': self.tenant, 'tenant2': kwargs['tenant']}
            )
        else:
            kwargs['tenant'] = self.tenant
        return kwargs

    # Filter everything by Tenant
    def by_tenant(self):
        kwargs = self.add_tenant_to_kwargs()
        return self.filter(**kwargs)

    # Override queries that write to add our Tenant
    def bulk_create(self, objs, batch_size=None):
        for obj in objs:
            if getattr(obj, 'tenant', None) and obj.tenant != self.tenant:
                raise MultitenantIncompatiblityError(
                    "Tenant provided in by_tenant (%(tenant1)s) doesn't match Tenant "
                    "provided in object (%(tenant2)s)"
                    % {'tenant1': self.tenant, 'tenant2': obj.tenant}
                )

            obj.tenant = self.tenant
        return super(TenantQuerySet, self).bulk_create(objs, batch_size)

    def create(self, **kwargs):
        kwargs = self.add_tenant_to_kwargs(**kwargs)
        return super(TenantQuerySet, self).create(**kwargs)

    def get_or_create(self, **kwargs):
        kwargs = self.add_tenant_to_kwargs(**kwargs)
        return super(TenantQuerySet, self).get_or_create(**kwargs)


class TenantManager(models.Manager):

    def get_queryset(self, tenant=None):
        qs = TenantQuerySet(self.model, tenant=tenant)
        if not qs.tenant:
            raise MultitenantIncompatiblityError(
                "All queries on a TenantEnabled model must use .by_tenant(tenant) "
                "as the first query in your chain. Use the all_tenants Manager if "
                "you really want objects from multiple tenants."
            )
        return qs

    def by_tenant(self, tenant):
        qs = self.get_queryset(tenant=tenant)
        return qs.by_tenant()


class TenantEnabled(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, default=None, on_delete=models.SET_NULL)

    # make all_tenants first, so it's the default manager and will be used for dumpdata, etc
    all_tenants = models.Manager()
    objects = TenantManager()

    class Meta:
        abstract = True


class BackendLink(TenantEnabled):
    backend = models.OneToOneField(Backend, related_name='tenantlink')

    def __unicode__(self):
        return self.backend.name


class ContactLink(TenantEnabled):
    description = models.CharField(max_length=200, blank=True)
    email = models.EmailField(null=True, blank=True)
    contact = models.OneToOneField(Contact)

    def __unicode__(self):
        return self.contact.name
