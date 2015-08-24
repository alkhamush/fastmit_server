from django.conf.urls import patterns, url

from fastmit_app import views

urlpatterns = patterns('',
    url(r'^some-secret-api/registration$', views.registration, name='registration'),
    url(r'^some-secret-api/login$', views.login, name='login'),
    url(r'^some-secret-api/logout$', views.logout, name='logout'),
    url(r'^some-secret-api/friends$', views.friends, name='friends'),
    url(r'^some-secret-api/potential-friends$', views.potential_friends, name='potential_friends'),
    url(r'^some-secret-api/friends/add$', views.friends_add, name='friends_add'),
    url(r'^some-secret-api/friends/delete$', views.friends_delete, name='friends_delete'),
    url(r'^some-secret-api/friends/search$', views.friends_search, name='friends_search'),
    url(r'^some-secret-api/user/info$', views.user_info, name='user_info'),
    url(r'^some-secret-api/user/change-password$', views.change_password, name='change_password'),
    url(r'^some-secret-api/user/change-avatar$', views.change_avatar, name='change_avatar'),
    url(r'^some-secret-api/chat/get-photo$', views.get_photo, name='get_photo'),
    url(r'^some-secret-api/chat/get-photourl$', views.put_photo, name='put_photo'),
    url(r'^some-secret-api/forgot-password$', views.forgot_password, name='forgot_password'),
    url(r'^some-secret-api/recover-password$', views.recover_password, name='recover_password'),
    url(r'^some-secret-api/set-device-token$', views.set_device_token, name='set_device_token'),
)
