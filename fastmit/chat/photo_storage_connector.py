import json
import urllib2


_PHOTO_STORAGE_HOST = "http://localhost/some-secret-api/chat/"


def put_photo(session_key, photo):
    data = json.dumps({"token": session_key, "photo":photo})
    request = urllib2.Request(_PHOTO_STORAGE_HOST + "get-photourl")
    response = urllib2.urlopen(request, data=data).read()
    response = json.loads(response)
    return response["url"]
