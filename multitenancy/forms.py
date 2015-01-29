from django import forms

from .models import Tenant, BackendLink


class TenantForm(forms.ModelForm):
    backend_link = forms.ModelChoiceField(queryset=BackendLink.all_tenants.none(),
                                          required=False)

    class Meta:
        model = Tenant
        fields = ('name', 'slug', 'description', 'group', 'backend_link')

    def __init__(self, *args, **kwargs):
        super(TenantForm, self).__init__(*args, **kwargs)
        # only show backends that are already associated with this tenant ...
        if self.instance.pk:
            qs = BackendLink.objects.by_tenant(tenant=self.instance)
        else:
            qs = BackendLink.all_tenants.none()
        # ... or are not associated with any Tenant
        qs = qs | BackendLink.all_tenants.filter(tenant__isnull=True)
        # ... and finally exclude MessageTester backends (they all start with 'mt_')
        self.fields['backend_link'].queryset = qs.exclude(backend__name__startswith='mt_')
        self.fields['backend_link'].initial = self.instance.backendlink_set.first()

    def save(self, commit=True):
        tenant = super(TenantForm, self).save(commit=commit)
        # we can't update backendlinks until tenant and tenantgroup
        # have been saved, so add them to the tenant object and save
        # them in the model save method
        if self.cleaned_data['backend_link']:
            tenant.unsaved_backendlinks = [self.cleaned_data['backend_link'], ]
        if commit:
            tenant.save()
        return tenant
