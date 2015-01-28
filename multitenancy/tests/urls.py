from django.conf.urls import url, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = (
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('rapidsms.urls.login_logout')),
    url(r'^', include('multitenancy.urls')),
)
