# -*- coding: utf-8 -*-

import os
import time
import json
import redis
import errno
import string
import random
import hashlib

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

FILE_PREFIX = '/getfile'
FILE_PREFIX_AVATAR = '/avatar'
URL_PREFIX = 'http://95.85.8.141'


def parse_json(_str):
    try:
        params = json.loads(_str)
    except ValueError:
        return None
    return params


def json_response(response_dict, status=200):
    response = HttpResponse(json.dumps(response_dict), content_type="application/json", status=status)
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Credentials'] = 'true'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


def get_session(token):
    try:
        session = Session.objects.get(pk=token)
    except Session.DoesNotExist:
        return None
    return session


def get_user(id=0, username=None, email=None):
    try:
        if username:
            user = User.objects.get(username=username)
        elif email:
            user = User.objects.get(email=email)
        else:
            user = User.objects.get(id=id)
    except User.DoesNotExist:
        return None
    return user


def get_uid(session):
    return session.get_decoded().get('_auth_user_id')


def get_user_info(user):
    info = dict()
    r = redis_connect()
    info['id'] = user.pk
    info['username'] = user.username
    info['photoUrl'] = r.get('user_%s_avatar' % user.pk)
    info['email'] = user.email
    info['friendsCount'] = len(r.smembers('user_%s_friends' % user.pk))
    info['unreadCount'] = get_unread_count(user.pk, r)
    info['color'] = r.get('user_%s_color' % user.pk)
    return info


def potential_friends_response(all_potential_friends, list_friend_id, request, r):
    if len(list_friend_id) > 0:
        for friend_id in list_friend_id:
            friend = dict()
            friend['id'] = friend_id
            friend['username'] = User.objects.get(pk=friend_id).username
            friend['photoUrl'] = r.get('user_%s_avatar' % friend_id)
            friend['request'] = request
            friend['color'] = r.get('user_%s_color' % friend_id)
            all_potential_friends.append(friend)


def get_unread_count(uid, r):
    unread_count = 0
    set_friend_id = r.smembers('user_%s_friends' % uid)
    for friend_id in set_friend_id:
        unread_count += len(r.zrange('messages_from_%s_to_%s' % (friend_id, uid), 0, -1, withscores=True))
    return unread_count


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def save_file(username, _file, avatar=False):
    if avatar:
        file_path = '%s/%s' % (FILE_PREFIX_AVATAR, username[0])
    else:
        file_path = '%s/%s/%s' % (FILE_PREFIX, username[0], username)
    mkdir_p(file_path)
    ts = int(time.time())
    _hash = hashlib.sha1('%s%s' % (_file, ts)).hexdigest()[:15]
    f = open('%s/%s' % (file_path, _hash), 'w')
    f.write(_file)
    f.close()
    return '%s%s/%s' % (URL_PREFIX, file_path, _hash)


def remove_file(file_link, avatar=False):
    file_link = str(file_link)
    try:
        if avatar:
            file_path = '%s/%s' % (FILE_PREFIX_AVATAR, file_link.split(FILE_PREFIX)[1])
        else:
            file_path = '%s/%s' % (FILE_PREFIX, file_link.split(FILE_PREFIX)[1])
    except IndexError:
        return
    try:
        os.remove(file_path)
    except OSError:
        pass


def read_file(file_link):
    file_link = str(file_link)
    try:
        file_path = '%s/%s' % (FILE_PREFIX, file_link.split(FILE_PREFIX)[1])
    except IndexError:
        return None
    f = open(file_path)
    data = f.read()
    f.close()
    return data


def pass_gen(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def color_gen():
    return random.choice(open(os.path.join(BASE_DIR, "fastmit_app/colors.txt")).readlines()).rstrip().upper()
