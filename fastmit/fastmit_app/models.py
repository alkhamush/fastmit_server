from django.db import models

from django.contrib.auth.models import User

_PUBLIC_KEY_MAX_LENGTH = 172


class PublicKey(models.Model):
    user = models.ForeignKey(User, related_name="public_key")
    public_key = models.CharField(max_length=_PUBLIC_KEY_MAX_LENGTH)
