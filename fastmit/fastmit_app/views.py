# -*- coding: utf-8 -*-

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import User
from django.contrib import auth
from django.http import HttpResponse, HttpResponseForbidden
import json


def registration(request):
    username = 'first_name'
    password = 'first_pass'
    email = 'email'
    if request.POST:
        if User.objects.filter(username=username).exists():
            return HttpResponseForbidden(json.dumps({"response": "User exists"}))
        if User.objects.filter(username=email).exists():
            return HttpResponseForbidden(json.dumps({"response": "Email is already registered"}))
        user = User(username='first_name', password=password, email=email)
        user.save()
        return HttpResponse(json.dumps({"token": "token_for_user"}))
