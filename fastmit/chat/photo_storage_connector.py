import json
import urllib2


_PHOTO_STORAGE_HOST = "http://localhost/some-secret-api/chat/"


def put_photo(session_key, photo):
    data = json.dumps({"token": session_key, "photo":photo})
    request = urllib2.Request(_PHOTO_STORAGE_HOST + "get-photourl")
    response = urllib2.urlopen(request, data=data).read()
    return json.loads(response)


def get_photo(session_key, photo_url):
    data = json.dumps({"token": session_key, "photoUrl": photo_url})
    request = urllib2.Request(_PHOTO_STORAGE_HOST + "get-photo")
    response = urllib2.urlopen(request, data=data).read()
    return json.loads(response)