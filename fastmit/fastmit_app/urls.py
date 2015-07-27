from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^some-secret-api/registration$', 'fastmit_app.views.registration', name='registration'),
    url(r'^some-secret-api/login$', 'fastmit_app.views.login', name='login'),
    url(r'^some-secret-api/logout$', 'fastmit_app.views.logout', name='logout'),
    url(r'^some-secret-api/friends$', 'fastmit_app.views.friends', name='friends'),
    url(r'^some-secret-api/potential-friends$', 'fastmit_app.views.potential_friends', name='potential_friends'),
    url(r'^some-secret-api/friends/add$', 'fastmit_app.views.friends_add', name='friends_add'),
    url(r'^some-secret-api/friends/delete$', 'fastmit_app.views.friends_delete', name='friends_delete'),
    url(r'^some-secret-api/friends/search$', 'fastmit_app.views.friends_search', name='friends_search'),
    url(r'^some-secret-api/user/info$', 'fastmit_app.views.user_info', name='user_info'),
    url(r'^some-secret-api/user/change-password$', 'fastmit_app.views.change_password', name='change_password'),
    url(r'^some-secret-api/user/change-avatar$', 'fastmit_app.views.change_avatar', name='change_avatar'),
    url(r'^some-secret-api/chat/get-photo$', 'fastmit_app.views.get_photo', name='get_photo'),
    url(r'^some-secret-api/chat/get-photourl$', 'fastmit_app.views.get_photourl', name='get_photourl'),
)
