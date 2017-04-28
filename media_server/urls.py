from django.conf.urls import *
from media.views import *
from django.conf import settings
from django.contrib import admin
import os.path
from django.views.generic import TemplateView
from django.conf.urls.static import static
from media import rest
from media.rest import *
from rest_framework import routers
from rest_framework.authtoken import views

site_media = os.path.join(
	os.path.dirname(__file__), 'site_media'
)

admin.autodiscover()


urlpatterns = [
	url(r'^admin/', include(admin.site.urls)),
	url(r'^$', main_page),
    url(r'^tags=(\w+)$', main_page),
    url(r'^embed/(\d+)/$', embed_page),
	url(r'^login/$', login_page),
	url(r'^user/(\w+)/$', user_page),
	url(r'^logout/$', logout_page),
    url(r'^download/', download),
	url(r'^changeviews/',changeviews),
	url(r'^delete_media/',delete_media),
	url(r'^favorite/',favorite),
    url(r'^delete_favorite/',delete_favorite),
    url(r'^more_space/', more_space),
    # (r'^featured/', featured),
    url(r'^categories/([\w.]{0,256})/$', main_page),
    url(r'^logthis/', logthis),
	url(r'^v/(\d+)/$',main_page),
	url(r'^360/$', TemplateView.as_view(template_name='360.html')),
	url(r'^api-token-auth/', views.obtain_auth_token),
	url(r'^rest/media/(?P<numvids>[0-9]+)$', rest.MediaList.as_view()),
	url(r'^rest/media/$', rest.MediaList.as_view()),
	#Admin
] + static(settings.STATIC_URL, document_user=settings.STATIC_user)

