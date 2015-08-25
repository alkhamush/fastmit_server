from gcm import GCM
from redis_utils import get_gcm_key

API_KEY_GCM = GCM("AIzaSyDejSxmynqJzzBdyrCS-IqMhp0BxiGWL1M")


def push_message(uid):
    reg_id = get_gcm_key(uid)
    if reg_id:
        data = {'the_message': 'You have x new friends', 'param2': 'value2'}
        API_KEY_GCM.plaintext_request(registration_id=reg_id, data=data)