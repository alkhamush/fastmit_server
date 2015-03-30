from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^some-secret-api/registration$', 'fastmit_app.views.registration', name='registration'),
)
