# -*- coding: utf-8 -*-

import json
import redis

from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import IntegrityError

def json_response(response_dict, status=200):
    response = HttpResponse(json.dumps(response_dict), content_type="application/json", status=status)
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Credentials'] = 'true'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

def redis_connect():
    return redis.StrictRedis(host='localhost', port=6379, db=0)

def potential_friends_response(all_potential_friends, list_friend_id, request, r):
    if len(list_friend_id) > 0:
        for friend_id in list_friend_id:
            friend = dict()
            friend['id'] = friend_id
            friend['username'] = User.objects.get(pk=friend_id).username
            friend['photoUrl'] = r.get('user_%s_avatar' % friend_id)
            friend['request'] = request
            all_potential_friends.append(friend)

def get_unread_count(uid, r):
    unread_count = 0
    set_friend_id = r.smembers('user_%s_friends' % uid)
    for friend_id in set_friend_id:
        unread_count += len(r.zrange('messages_from_%s_to_%s' % (friend_id, uid), 0, -1, withscores=True))
    return unread_count

def registration(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        params = json.loads(request.body)
        try:
            username = params['username']
        except KeyError:
            username = None
        try:
            email = params['email']
        except KeyError:
            email = None
        try:
            password = params['password']
        except KeyError:
            password = None
        if username is None or email is None or password is None:
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
        params = json.loads(request.body)
        try:
            username = params['username']
        except KeyError:
            username = None
        try:
            password = params['password']
        except KeyError:
            password = None
        if username is None or password is None:
            return json_response({'response': 'Wrong login or password'}, status=403)
        user = auth.authenticate(username=username, password=password)
        if user is not None:
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
        params = json.loads(request.body)
        try:
            token = params['token']
        except KeyError:
            token = None
        if token is None:
            return json_response({'response': 'Logout fail'}, status=403)
        try:
            Session.objects.get(pk=token).delete()
            return json_response({'response': 'Ok'})
        except Session.DoesNotExist:
            return json_response({'response': 'Logout fail'}, status=403)
    else:
        return json_response({'response': 'Invalid method'}, status=403)

def friends(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'GET':
        token = request.GET.get('token', None)
        if token is None:
            return json_response({'response': 'token error'}, status=403)
        try:
            session = Session.objects.get(pk=token)
        except Session.DoesNotExist:
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
    elif request.method == 'GET':
        token = request.GET.get('token', None)
        if token is None:
            return json_response({'response': 'token error'}, status=403)
        try:
            session = Session.objects.get(pk=token)
        except Session.DoesNotExist:
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
    elif request.method == 'GET':
        token = request.GET.get('token', None)
        if token is None:
            return json_response({'response': 'token error'}, status=403)
        friend_id = request.GET.get('friendId', None)
        if friend_id is None:
            return json_response({'response': 'friend_id error'}, status=403)
        try:
            session = Session.objects.get(pk=token)
        except Session.DoesNotExist:
            return json_response({'response': 'token error'}, status=403)
        try:
            User.objects.get(id=friend_id)
        except User.DoesNotExist:
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
    elif request.method == 'GET':
        token = request.GET.get('token', None)
        if token is None:
            return json_response({'response': 'token error'}, status=403)
        friend_id = request.GET.get('friendId', None)
        if friend_id is None:
            return json_response({'response': 'friend_id error'}, status=403)
        try:
            session = Session.objects.get(pk=token)
        except Session.DoesNotExist:
            return json_response({'response': 'token error'}, status=403)
        try:
            User.objects.get(id=friend_id)
        except User.DoesNotExist:
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
    elif request.method == 'GET':
        token = request.GET.get('token', None)
        if token is None:
            return json_response({'response': 'token error'}, status=403)
        try:
            session = Session.objects.get(pk=token)
        except Session.DoesNotExist:
            return json_response({'response': 'token error'}, status=403)
        users = []
        find_name = request.GET.get('username', None)
        if find_name is None:
            return json_response({'users': users})
        try:
            find_user = User.objects.get(username=find_name)
        except User.DoesNotExist:
            return json_response({'users': users})
        user = dict()
        uid = session.get_decoded().get('_auth_user_id')
        r = redis_connect()
        user['id'] = find_user.id
        user['username'] = find_user.username
        user['isFriend'] = str(find_user.id) in r.smembers('user_%s_friends' % uid)
        user['isOnline'] = False
        users.append(user)
        return json_response({'users': users})
    else:
        return json_response({'response': 'Invalid method'}, status=403)

def user_info(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'GET':
        token = request.GET.get('token', None)
        if token is None:
            return json_response({'response': 'token error'}, status=403)
        try:
            session = Session.objects.get(pk=token)
        except Session.DoesNotExist:
            return json_response({'response': 'token error'}, status=403)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=uid)
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
        params = json.loads(request.body)
        try:
            token = params['token']
        except KeyError:
            return json_response({'response': 'token error'}, status=403)
        try:
            old_password = params['oldPassword']
        except KeyError:
            return json_response({'response': 'Wrong old password'}, status=403)
        try:
            new_password = params['newPassword']
        except KeyError:
            return json_response({'response': 'Empty new password'}, status=403)
        if new_password == '':
            return json_response({'response': 'Empty new password'}, status=403)
        try:
            session = Session.objects.get(pk=token)
        except Session.DoesNotExist:
            return json_response({'response': 'token error'}, status=403)
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=uid)
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return json_response({'response': 'Password is changed'})
        else:
            return json_response({'response': 'Wrong old password'}, status=403)
    else:
        return json_response({'response': 'Invalid method'}, status=403)
