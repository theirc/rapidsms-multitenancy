from django.conf.urls import url

from . import views


urlpatterns = (
    url(r'^$', views.group_selection, name='group-landing'),
    url(r'^(?P<group_slug>[\w-]+)/$',
        views.group_dashboard, name='group-detail'),
    url(r'^(?P<group_slug>[\w-]+)/(?P<tenant_slug>[\w-]+)/$',
        views.tenant_dashboard, name='tenant-detail'),
)
