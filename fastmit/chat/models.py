from django.db import models

from django.contrib.auth.models import User

_PUBLIC_KEY_MAX_LENGTH = 172


class PublicKey(models.Model):
    user = models.OneToOneField(User, related_name="public_key")
    public_key = models.CharField(max_length=_PUBLIC_KEY_MAX_LENGTH)


class APIKeyGCM(models.Model):
    user = models.OneToOneField(User, related_name="api_key_gcm")
    api_key_gcm = models.TextField()