from gcm import GCM
from redis_utils import get_gcm_key

API_KEY_GCM = GCM("AIzaSyBemf-r6a69HsdbL6WzfbGqs9oI6smI-Gw")


def push_message(uid):

    reg_id = get_gcm_key(uid)
    if reg_id:
        data = {'the_message': 'You have x new friends', 'param2': 'value2'}
        API_KEY_GCM.plaintext_request(registration_id=reg_id, data=data)
