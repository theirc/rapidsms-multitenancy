from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .auth import is_group_manager, is_tenant_manager
from .forms import TenantForm
from .models import BackendLink, ContactLink, Tenant, TenantGroup, TenantRole


class TenantInline(admin.TabularInline):
    extra = 1
    form = TenantForm
    model = Tenant
    prepopulated_fields = {"slug": ("name", )}


class TenantRoleFormset(forms.BaseInlineFormSet):
    """Filters roles to particular type."""

    role = None

    def __init__(self, *args, **kwargs):
        super(TenantRoleFormset, self).__init__(*args, **kwargs)
        if self.queryset is not None and self.role is not None:
            self.queryset = self.queryset.filter(role=self.role)

    def save_new(self, form, commit=True):
        if self.role is not None:
            form.instance.role = self.role
        return super(TenantRoleFormset, self).save_new(form, commit=commit)

    def save_existing(self, form, instance, commit=True):
        if self.role is not None:
            instance.role = self.role
            form.instance.role = self.role
        return super(TenantRoleFormset, self).save_existing(form, instance, commit=commit)


class GroupManagerForm(forms.ModelForm):

    class Meta:
        model = TenantRole
        fields = ('user', )


class GroupManagerFormset(TenantRoleFormset):
    role = TenantRole.ROLE_GROUP_MANAGER


class GroupManagerInline(admin.TabularInline):
    """Inline for adding managers to the group. """

    model = TenantRole
    form = GroupManagerForm
    formset = GroupManagerFormset
    verbose_name = _('Group Manager')
    verbose_name_plural = _('Group Managers')
    extra = 1
    fields = ('user', )


class TenantGroupAdmin(admin.ModelAdmin):
    inlines = (TenantInline, )
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name", )}
    search_fields = ('name', )

    def get_queryset(self, request):
        """Limit to TenantGroups that this user can access."""
        qs = super(TenantGroupAdmin, self).get_queryset(request)
        if is_group_manager(request.user):
            qs = qs.filter(tenantrole__user=request.user)
        return qs

    def get_inline_instances(self, request, obj=None):
        if request.user.is_superuser:
            # superuser should additionally be able to make GroupManagers
            self.inlines = (TenantInline, GroupManagerInline, )
        return super(TenantGroupAdmin, self).get_inline_instances(request, obj)


class TenantManagerForm(forms.ModelForm):

    class Meta:
        model = TenantRole
        fields = ('user', )

    def clean(self):
        if self.instance:
            if self.instance.tenant:
                self.instance.group = self.instance.tenant.group
            else:
                self.instance.group = self.cleaned_data['tenant'].group


class TenantManagerFormset(TenantRoleFormset):
    role = TenantRole.ROLE_TENANT_MANAGER


class TenantManagerInline(admin.TabularInline):
    """Inline for adding managers to the tenant."""

    model = TenantRole
    form = TenantManagerForm
    formset = TenantManagerFormset
    verbose_name = _('Tenant Manager')
    verbose_name_plural = _('Tenant Managers')
    extra = 1
    fields = ('user', )


class TenantAdmin(admin.ModelAdmin):
    """Administration of new tenants."""

    form = TenantForm
    inlines = (TenantManagerInline, )
    list_display = ('name', 'group', 'slug', 'get_backend_names', )
    list_filter = ('group', )
    prepopulated_fields = {"slug": ("name", )}
    search_fields = ('name', )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.rel.to == TenantGroup and not request.user.is_superuser:
            qs = kwargs.pop('queryset', TenantGroup.objects.all())
            qs = qs.filter(tenantrole__user=request.user)
            kwargs['queryset'] = qs
        return super(TenantAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        """Limit to Tenants that this user can access."""
        qs = super(TenantAdmin, self).get_queryset(request)
        if is_group_manager(request.user):
            qs = qs.filter(group__tenantrole__user=request.user)
        elif is_tenant_manager(request.user):
            qs = qs.filter(tenantrole__user=request.user)
        return qs

admin.site.register(BackendLink)
admin.site.register(ContactLink)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(TenantGroup, TenantGroupAdmin)
