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

def potential_friends_response(all_potential_friends, list_friend_id, request):
    if len(list_friend_id) > 0:
        for friend_id in list_friend_id:
            friend = dict()
            friend['id'] = friend_id
            friend['username'] = User.objects.get(pk=friend_id).username
            friend['photoUrl'] = 'some_photo_url'
            friend['request'] = request
            all_potential_friends.append(friend)

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
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        list_friend_id = list(r.smembers('user_%s_friends' % uid))
        all_friends = []
        if len(list_friend_id) > 0:
            for friend_id in list_friend_id:
                friend = dict()
                friend['id'] = friend_id
                friend['username'] = User.objects.get(pk=friend_id).username
                friend['isOnline'] = False
                friend['photoUrl'] = 'some_photo_url'
                friend['hasUnread'] = len(r.zrange("messages_from_%s_to_%s" % (friend_id, uid), 0, -1, withscores=True)) > 0
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
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        list_friend_id_in = list(r.smembers('user_%s_potential_friends_in' % uid))
        list_friend_id_out = list(r.smembers('user_%s_potential_friends_out' % uid))
        all_potential_friends = []
        potential_friends_response(all_potential_friends, list_friend_id_in, 'in')
        potential_friends_response(all_potential_friends, list_friend_id_out, 'out')
        return json_response({'users': all_potential_friends})
    else:
        return json_response({'response': 'Invalid method'}, status=403)
