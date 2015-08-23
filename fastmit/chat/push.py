from gcm import GCM
from models import APIKeyGCM

API_KEY_GCM = GCM("AIzaSyDejSxmynqJzzBdyrCS-IqMhp0BxiGWL1M")


def _get_reg_id_by_uid(uid):
    try:
        return APIKeyGCM.objects.values_list("api_key_gcm", flat=True).get(user=uid)
    except APIKeyGCM.DoesNotExist:
        return None


def push_message(uid):
    reg_id = _get_reg_id_by_uid(uid)
    data = {'the_message': 'You have x new friends', 'param2': 'value2'}
    API_KEY_GCM.plaintext_request(registration_id=reg_id, data=data)