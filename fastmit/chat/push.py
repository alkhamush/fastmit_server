from gcm import GCM
from redis_utils import get_gcm_key

API_KEY_GCM = GCM("AIzaSyBemf-r6a69HsdbL6WzfbGqs9oI6smI-Gw")


def push_message(uid):

    reg_id = get_gcm_key(uid)
    if reg_id:
        data = {"message": "You have x new friends", "title": "Fastmit"}
        API_KEY_GCM.json_request(registration_ids=[reg_id], data=data)
