# -*- coding: utf-8 -*-

from utils import *

from django.contrib import auth
from django.db import IntegrityError
from django.contrib.auth.models import User


def registration(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        username = params.get('username', None)
        email = params.get('email', None)
        password = params.get('password', None)
        if not username or not email or not password:
            return json_response({'response': 'Invalid data'}, status=403)
        if User.objects.filter(email=email).count():
            return json_response({'response': 'Email is already registered'}, status=403)
        try:
            User.objects.create_user(username=username, email=email, password=password)
            user = auth.authenticate(username=username, password=password)
            auth.login(request, user)
            session_key = request.session.session_key
            return json_response({'token': session_key})
        except IntegrityError:
            return json_response({'response': 'User exists'}, status=403)
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def login(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        username = params.get('username', None)
        password = params.get('password', None)
        user = auth.authenticate(username=username, password=password)
        if user:
            if user.is_active:
                auth.login(request, user)
                session_key = request.session.session_key
                return json_response({'token': session_key})
            else:
                return json_response({'response': 'User is sleeping'}, status=403)
        else:
            return json_response({'response': 'Wrong login or password'}, status=403)
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def logout(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        session = get_session(token)
        if not session:
            return json_response({'response': 'Logout fail'}, status=403)
        session.delete()
        return json_response({'response': 'Ok'})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def friends(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        uid = session.get_decoded().get('_auth_user_id')
        r = redis_connect()
        list_friend_id = list(r.smembers('user_%s_friends' % uid))
        all_friends = []
        if len(list_friend_id) > 0:
            for friend_id in list_friend_id:
                friend = dict()
                friend['id'] = friend_id
                friend['username'] = User.objects.get(pk=friend_id).username
                friend['isOnline'] = False
                friend['photoUrl'] = r.get('user_%s_avatar' % friend_id)
                friend['hasUnread'] = len(r.zrange('messages_from_%s_to_%s' % (friend_id, uid), 0, -1, withscores=True)) > 0
                all_friends.append(friend)
        return json_response({'friends': all_friends})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def potential_friends(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        uid = session.get_decoded().get('_auth_user_id')
        r = redis_connect()
        list_friend_id_in = list(r.smembers('user_%s_potential_friends_in' % uid))
        list_friend_id_out = list(r.smembers('user_%s_potential_friends_out' % uid))
        all_potential_friends = []
        potential_friends_response(all_potential_friends, list_friend_id_in, 'in', r)
        potential_friends_response(all_potential_friends, list_friend_id_out, 'out', r)
        return json_response({'users': all_potential_friends})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def friends_add(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        friend_id = params.get('friendId', None)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        user = get_user(friend_id)
        if not user:
            return json_response({'response': 'friend_id error'}, status=403)
        uid = session.get_decoded().get('_auth_user_id')
        r = redis_connect()
        if str(friend_id) in r.smembers('user_%s_potential_friends_in' % uid):
            r.sadd('user_%s_friends' % uid, friend_id)
            r.sadd('user_%s_friends' % friend_id, uid)
            r.srem('user_%s_potential_friends_in' % uid, friend_id)
            r.srem('user_%s_potential_friends_out' % friend_id, uid)
        else:
            r.sadd('user_%s_potential_friends_out' % uid, friend_id)
            r.sadd('user_%s_potential_friends_in' % friend_id, uid)
        return json_response({'response': 'Request is sent'})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def friends_delete(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        friend_id = params.get('friendId', None)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        user = get_user(friend_id)
        if not user:
            return json_response({'response': 'friend_id error'}, status=403)
        uid = session.get_decoded().get('_auth_user_id')
        r = redis_connect()
        r.srem('user_%s_friends' % uid, friend_id)
        r.srem('user_%s_friends' % friend_id, uid)
        r.srem('user_%s_potential_friends_out' % uid, friend_id)
        r.srem('user_%s_potential_friends_out' % friend_id, uid)
        r.srem('user_%s_potential_friends_in' % friend_id, uid)
        r.srem('user_%s_potential_friends_in' % uid, friend_id)
        return json_response({'response': 'User is removed from your list'})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def friends_search(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        users = []
        find_name = request.GET.get('username', None)
        if find_name is None:
            return json_response({'users': users})
        find_user = get_user(username=find_name)
        if not find_user:
            return json_response({'users': users})
        user = dict()
        uid = get_uid(session)
        r = redis_connect()
        user['id'] = find_user.id
        user['username'] = find_user.username
        user['isFriend'] = str(find_user.id) in r.smembers('user_%s_friends' % uid)
        user['isOnline'] = False
        user['photoUrl'] = r.get('user_%s_avatar' % uid)
        users.append(user)
        return json_response({'users': users})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def user_info(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        uid = get_uid(session)
        user = get_user(uid)
        r = redis_connect()
        info = dict()
        info['username'] = user.username
        info['photoUrl'] = r.get('user_%s_avatar' % uid)
        info['email'] = user.email
        info['friendsCount'] = len(r.smembers('user_%s_friends' % uid))
        info['unreadCount'] = get_unread_count(uid, r)
        return json_response({'info': info})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def change_password(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        old_password = params.get('oldPassword', None)
        new_password = params.get('newPassword', None)
        if new_password == '':
            return json_response({'response': 'Empty new password'}, status=403)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        uid = get_uid(session)
        user = get_user(uid)
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return json_response({'response': 'Password is changed'})
        return json_response({'response': 'Wrong old password'}, status=403)
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def change_avatar(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        avatar = params.get('avatar', None)
        if not avatar:
            return json_response({'response': 'avatar error'}, status=403)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        uid = get_uid(session)
        user = get_user(uid)
        avatar_link = save_file(user.username, avatar, avatar=True)
        r = redis_connect()
        old_avatar = r.get('user_%s_avatar' % uid)
        remove_file(old_avatar, avatar=True)
        r.set('user_%s_avatar' % uid, avatar_link)
        return json_response({'response': 'Ok'})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def get_photo(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        file_link = params.get('photoUrl', None)
        if not file_link:
            return json_response({'response': 'no photo'}, status=403)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        data = read_file(file_link)
        remove_file(file_link)
        return json_response({'data': data})
    else:
        return json_response({'response': 'Invalid method'}, status=403)


def get_photourl(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = parse_json(request.body)
        if not params:
            return json_response({'response': 'json error'}, status=403)
        token = params.get('token', None)
        data = params.get('photo', None)
        if not data:
            return json_response({'response': 'file error'}, status=403)
        session = get_session(token)
        if not session:
            return json_response({'response': 'token error'}, status=403)
        uid = get_uid(session)
        user = get_user(uid)
        url = save_file(user.username, data)
        return json_response({'url': url})
    else:
        return json_response({'response': 'Invalid method'}, status=403)
