# -*- coding: utf-8 -*-

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import User
from django.contrib import auth
from django.http import HttpResponse, HttpResponseForbidden
import json


def registration(request):
    username = 'first_name2'
    password = 'first_pass'
    email = 'email2'
    #if request.POST:
    if User.objects.filter(username=username).exists():
        return HttpResponseForbidden(json.dumps({"response": "User exists"}))
    if User.objects.filter(email=email).exists():
        return HttpResponseForbidden(json.dumps({"response": "Email is already registered"}))
    user = User(username=username, password=password, email=email)
    user.save()
    return HttpResponse(json.dumps({"token": "token_for_user"}))
