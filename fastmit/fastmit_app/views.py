# -*- coding: utf-8 -*-

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import User
from django.contrib import auth
from django.http import HttpResponse


def registration(request):
    return HttpResponse("registration")
