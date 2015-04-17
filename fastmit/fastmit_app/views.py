# -*- coding: utf-8 -*-

import json
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

def registration(request):
    if request.method == 'OPTIONS':
        return json_response({})
    elif request.method == 'POST':
        username = request.POST.get('username', None)
        email = request.POST.get('email', None)
        password = request.POST.get('password', None)
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
        json_response({})
    elif request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if username is None or password is None:
            return json_response({'response': 'Wrong login or password'})
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
        json_response({})
    elif request.method == 'POST':
        token = request.POST.get('token', None)
        if token is None:
            return json_response({'response': 'Logout fail'}, status=403)
        try:
            Session.objects.get(pk=token).delete()
            return json_response({'response': 'Ok'})
        except Session.DoesNotExist:
            return json_response({'response': 'Logout fail'}, status=403)
    else:
        return json_response({'response': 'Invalid method'}, status=403)
