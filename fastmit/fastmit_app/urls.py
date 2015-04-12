from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^some-secret-api/registration$', 'fastmit_app.views.registration', name='registration'),
    url(r'^some-secret-api/login$', 'fastmit_app.views.login', name='login'),
    url(r'^some-secret-api/logout$', 'fastmit_app.views.logout', name='logout'),
)
