# -*- coding: utf-8 -*-

import os
import time
import json
import redis
import errno
import string
import random
import hashlib
import tempfile
from PIL import Image

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

FILE_PREFIX = '/getfile'
FILE_PREFIX_AVATAR = '/avatar'
URL_PREFIX = 'http://95.85.8.141'


def post_decorator(func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return json_response({})
        elif request.method == 'POST':
            return func(request, *args, **kwargs)
        else:
            return json_response({'response': 'Invalid method'}, status=403)
    return wrapper


def get_decorator(func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return json_response({})
        elif request.method == 'GET':
            return func(request, *args, **kwargs)
        else:
            return json_response({'response': 'Invalid method'}, status=403)
    return wrapper


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


def redis_connect():
    return redis.StrictRedis(host='localhost', port=6379, db=0)


def is_online(uid):
    redis_client = redis_connect()
    return redis_client.exists(uid)


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
    info['publicKey'] = user.public_key.public_key
    info['photoUrl'] = r.get('user_%s_avatar' % user.pk)
    info['previewUrl'] = r.get('user_%s_avatar_crop' % user.pk)
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
            friend['previewUrl'] = r.get('user_%s_avatar_crop' % friend_id)
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


def save_file(username, _file, token, avatar=False):
    if avatar:
        file_path = '%s/%s/%s' % (FILE_PREFIX_AVATAR, username[0], username)
    else:
        file_path = '%s/%s/%s' % (FILE_PREFIX, username[0], username)
    mkdir_p(file_path)
    ts = int(time.time())
    _hash = hashlib.sha1('%s%s' % (token, ts)).hexdigest()[:15]
    file_name = '%s/%s' % (file_path, _hash)
    if avatar:
        file_name += '.png'
        f = tempfile.NamedTemporaryFile()
        f.write(_file.decode('base64'))
        f.seek(0)
        image = Image.open(f.name)
        image.save(file_name)
    else:
        f = open(file_name, 'w')
        f.write(_file)
    f.close()
    file_link = '%s%s' % (URL_PREFIX, file_name)
    return file_link


def crop_image(file_link, avatar=False):
    file_path = get_file_path(file_link, avatar=avatar)
    if not file_path:
        return None
    try:
        image = Image.open(file_path)
    except IOError:
        return
    w, h = image.size
    base = 200
    if w > h:
        big_side = w
        small_side = h
    else:
        big_side = h
        small_side = w
    percent = base / float(small_side)
    new_size_big_side = int(big_side * percent)
    if w > h:
        new_sizes = (new_size_big_side, base)
    else:
        new_sizes = (base, new_size_big_side)
    image = image.resize(new_sizes, Image.ANTIALIAS)
    w, h = image.size
    if w > h:
        px_to_crop = (w - base) / 2
        image = image.crop((px_to_crop, 0, w - px_to_crop, h))
    else:
        px_to_crop = (h - base) / 2
        image = image.crop((0, px_to_crop, w, h - px_to_crop))
    path_to_save = '%s/crop_%s' % (os.path.dirname(file_path), os.path.basename(file_path))
    image.save(path_to_save)
    return '%s%s' % (URL_PREFIX, path_to_save)


def remove_file(file_link, avatar=False):
    file_link = str(file_link)
    file_path = get_file_path(file_link, avatar=avatar)
    if not file_path:
        return None
    try:
        os.remove(file_path)
    except OSError:
        pass


def read_file(file_link):
    file_link = str(file_link)
    file_path = get_file_path(file_link)
    if not file_path:
        return None
    try:
        f = open(file_path)
        data = f.read()
        f.close()
    except IOError:
        return None
    return data


def get_file_path(file_link, avatar=False):
    try:
        if avatar:
            file_path = '%s%s' % (FILE_PREFIX_AVATAR, file_link.split(FILE_PREFIX_AVATAR)[1])
        else:
            file_path = '%s%s' % (FILE_PREFIX, file_link.split(FILE_PREFIX)[1])
    except IndexError:
        return
    return file_path


def pass_gen(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def color_gen():
    return random.choice(open(os.path.join(BASE_DIR, "fastmit_app/colors.txt")).readlines()).rstrip().upper()
