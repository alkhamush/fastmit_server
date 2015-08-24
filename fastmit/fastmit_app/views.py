# -*- coding: utf-8 -*-

from django.contrib import auth
from django.db import IntegrityError
from django.core.mail import send_mail

from fastmit_app.models import PublicKey

from utils import *


@post_decorator
def registration(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    username = params.get('username', None)
    email = params.get('email', None)
    password = params.get('password', None)
    public_key = params.get('publicKey', None)
    if not username or not email or not password or not public_key:
        return json_response({'response': 'Invalid data'}, status=403)
    if User.objects.filter(email=email).count():
        return json_response({'response': 'Email is already registered'}, status=403)
    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        PublicKey.objects.create(user=user, public_key=public_key)
        user = auth.authenticate(username=username, password=password)
        auth.login(request, user)
        session_key = request.session.session_key
        r = redis_connect()
        r.set('user_%s_color' % user.pk, color_gen())
        info = get_user_info(user)
        return json_response({'token': session_key, 'info': info})
    except IntegrityError:
        return json_response({'response': 'User exists'}, status=403)


@post_decorator
def login(request):
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
            info = get_user_info(user)
            return json_response({'token': session_key, 'info': info})
        else:
            return json_response({'response': 'User is sleeping'}, status=403)
    else:
        return json_response({'response': 'Wrong login or password'}, status=403)


@post_decorator
def logout(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    token = params.get('token', None)
    session = get_session(token)
    if not session:
        return json_response({'response': 'Logout fail'}, status=403)
    session.delete()
    return json_response({'response': 'Ok'})


@post_decorator
def friends(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    token = params.get('token', None)
    session = get_session(token)
    if not session:
        return json_response({'response': 'token error'}, status=403)
    uid = get_uid(session)
    r = redis_connect()
    list_friend_id = list(r.smembers('user_%s_friends' % uid))
    all_friends = []
    if len(list_friend_id) > 0:
        for friend_id in list_friend_id:
            friend = dict()
            friend['id'] = friend_id
            user = User.objects.get(pk=friend_id)
            friend['username'] = user.username
            friend['publicKey'] = user.public_key.public_key
            friend['isOnline'] = is_online(friend_id)
            friend['photoUrl'] = r.get('user_%s_avatar' % friend_id)
            friend['previewUrl'] = r.get('user_%s_avatar_crop' % friend_id)
            friend['hasUnread'] = len(r.zrange('messages_from_%s_to_%s' % (friend_id, uid), 0, -1, withscores=True)) > 0
            friend['color'] = r.get('user_%s_color' % friend_id)
            all_friends.append(friend)
    return json_response({'friends': all_friends})


@post_decorator
def potential_friends(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    token = params.get('token', None)
    session = get_session(token)
    if not session:
        return json_response({'response': 'token error'}, status=403)
    uid = get_uid(session)
    r = redis_connect()
    list_friend_id_in = list(r.smembers('user_%s_potential_friends_in' % uid))
    list_friend_id_out = list(r.smembers('user_%s_potential_friends_out' % uid))
    all_potential_friends = []
    potential_friends_response(all_potential_friends, list_friend_id_in, 'in', r)
    potential_friends_response(all_potential_friends, list_friend_id_out, 'out', r)
    return json_response({'users': all_potential_friends})


@post_decorator
def friends_add(request):
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
    uid = get_uid(session)
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


@post_decorator
def friends_delete(request):
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
    uid = get_uid(session)
    r = redis_connect()
    r.srem('user_%s_friends' % uid, friend_id)
    r.srem('user_%s_friends' % friend_id, uid)
    r.srem('user_%s_potential_friends_out' % uid, friend_id)
    r.srem('user_%s_potential_friends_out' % friend_id, uid)
    r.srem('user_%s_potential_friends_in' % friend_id, uid)
    r.srem('user_%s_potential_friends_in' % uid, friend_id)
    return json_response({'response': 'User is removed from your list'})


@post_decorator
def friends_search(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    token = params.get('token', None)
    session = get_session(token)
    if not session:
        return json_response({'response': 'token error'}, status=403)
    users = []
    find_name = params.get('username', None)
    if find_name is None:
        return json_response({'users': users})
    qs = User.objects.all()
    qs = qs.filter(username__icontains=find_name)
    for find_user in qs[:3]:
        user = dict()
        uid = get_uid(session)
        r = redis_connect()
        user['id'] = find_user.id
        user['username'] = find_user.username
        user['isFriend'] = str(find_user.id) in r.smembers('user_%s_friends' % uid)
        user['isOnline'] = is_online(find_user.id)
        user['photoUrl'] = r.get('user_%s_avatar' % uid)
        user['previewUrl'] = r.get('user_%s_avatar_crop' % uid)
        user['color'] = r.get('user_%s_color' % uid)
        users.append(user)
    return json_response({'users': users})


@post_decorator
def user_info(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    token = params.get('token', None)
    session = get_session(token)
    if not session:
        return json_response({'response': 'token error'}, status=403)
    uid = get_uid(session)
    user = get_user(uid)
    info = get_user_info(user)
    return json_response({'info': info})


@post_decorator
def change_password(request):
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


@post_decorator
def change_avatar(request):
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
    avatar_link = save_file(user.username, avatar, token, avatar=True)
    avatar_link_crop = crop_image(avatar_link, avatar=True)
    print avatar_link_crop
    r = redis_connect()
    old_avatar_link = r.get('user_%s_avatar' % uid)
    remove_file(old_avatar_link, avatar=True)
    old_avatar_crop_link = r.get('user_%s_avatar_crop' % uid)
    remove_file(old_avatar_crop_link, avatar=True)
    r.set('user_%s_avatar' % uid, avatar_link)
    r.set('user_%s_avatar_crop' % uid, avatar_link_crop)
    return json_response({'response': 'Ok'})


@post_decorator
def get_photo(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    token = params.get('token', None)
    file_link = params.get('photoUrl', None)
    if not file_link:
        return json_response({'response': 'no such file'}, status=403)
    session = get_session(token)
    if not session:
        return json_response({'response': 'token error'}, status=403)
    photo = read_file(file_link)
    if not photo:
        return json_response({'response': 'no such file'}, status=403)
    remove_file(file_link)
    return json_response({'data': photo})


@post_decorator
def put_photo(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    token = params.get('token', None)
    photo = params.get('photo', None)
    if not photo:
        return json_response({'response': 'file error'}, status=403)
    session = get_session(token)
    if not session:
        return json_response({'response': 'token error'}, status=403)
    uid = get_uid(session)
    user = get_user(uid)
    url = save_file(user.username, photo, uid)
    return json_response({'url': url})


@get_decorator
def forgot_password(request):
    response = json_response({'response': 'New password has been sent to your email'})
    email = request.GET.get('email', None)
    user = get_user(email=email)
    if not user:
        return response
    r = redis_connect()
    tmp_pass = pass_gen()
    recover = dict()
    recover['pass'] = tmp_pass
    recover['expires'] = int(time.time()) + 3600
    r.set('user_%s_recover' % user.pk, json.dumps(recover))
    send_mail(subject='Fastmit Password Recovery', from_email='no-reply@fastmit.com',
              recipient_list=[user.email], fail_silently=True,
              message='Dear %s,\n\nYour temp password for 1 hour is "%s" without quotes.\n\nBest,\nThe Fastmit Team' % (user.username, tmp_pass))
    return response


@post_decorator
def recover_password(request):
    response_error = json_response({"response": "Wrong tmp password or expired"}, status=403)
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    email = params.get('email', None)
    tmp_pass = params.get('tmpPassword', None)
    new_password = params.get('newPassword', None)
    if new_password == '':
        return json_response({'response': 'Empty new password'}, status=403)
    user = get_user(email=email)
    if not user:
        return response_error
    r = redis_connect()
    redis_tmp = r.get('user_%s_recover' % user.pk)
    if not redis_tmp:
        return response_error
    recover = json.loads(redis_tmp)
    if recover.get('pass', None) == tmp_pass and recover.get('expires', None) > int(time.time()):
        r.delete('user_%s_recover' % user.pk)
        user.set_password(new_password)
        user.save()
        return json_response({'response': 'Password is changed'})
    return response_error


@post_decorator
def set_device_token(request):
    params = parse_json(request.body)
    if not params:
        return json_response({'response': 'json error'}, status=403)
    device_token = params.get('deviceToken', None)
    token = params.get('token', None)
    if not device_token or not token:
        return json_response({'response': 'Invalid data'}, status=403)
    session = get_session(token)
    uid = get_uid(session)
    add_gcm_key(uid)

