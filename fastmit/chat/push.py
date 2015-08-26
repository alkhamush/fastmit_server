# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from gcm import GCM
from redis_utils import get_gcm_key


API_KEY_GCM = GCM("AIzaSyBemf-r6a69HsdbL6WzfbGqs9oI6smI-Gw")


def push_message(uid, sender):
    username = User.objects.values_list("username", flat=True).get(id=sender)
    reg_id = get_gcm_key(uid)
    if reg_id:
        data = {"message": "Новое сообщение", "title": username, "id": sender, "type": "msg"}
        API_KEY_GCM.json_request(registration_ids=[reg_id], data=data)
