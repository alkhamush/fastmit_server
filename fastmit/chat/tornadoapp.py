# -*- coding: utf-8 -*-

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import json

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sessions.models import Session

import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options

from message_utils import generate_messages_packet
from photo_storage_connector import put_photo
from push import push_message
from redis_utils import add_message, get_messages, add_online_user, remove_online_user

define("port", default=8888, type=int)


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self, *args):
        session_key = self.get_cookie("sessionid")
        try:
            session = Session.objects.get(session_key=session_key)
        except ObjectDoesNotExist:
            self.close()
            return
        uid = int(session.get_decoded().get('_auth_user_id'))

        self.uid = uid
        self.session_key = session_key
        self.application.webSocketPool[uid] = self
        add_online_user(self.uid)

        message_bodies = get_messages(uid)
        messages_packet = generate_messages_packet(message_bodies)
        messages_packet_json = json.dumps(messages_packet)
        self.application.webSocketPool[uid].write_message(messages_packet_json)

    def on_message(self, message_packet_json):
        message_packet = json.loads(message_packet_json)

        body = message_packet["body"]

        to = int(body["friendId"])

        body["friendId"] = str(self.uid)

        message = body["message"]

        if message["type"] == "photo":
            url = put_photo(self.session_key, message["encodedPhotoData"])
            message["photoUrl"] = url
            del message["encodedPhotoData"]
        if to in self.application.webSocketPool:
            message_packet_json = json.dumps(message_packet)
            self.application.webSocketPool[to].write_message(message_packet_json)
        else:
            message_body_json = json.dumps(body)
            add_message(to, message_body_json)
            #push_message(to)

    def on_close(self):
        try:
            del self.application.webSocketPool[self.uid]
            remove_online_user(self.uid)
        except (AttributeError, KeyError):
            pass


class Application(tornado.web.Application):
    def __init__(self, handlers):
        super(Application, self).__init__(handlers)
        self.webSocketPool = dict()

app = Application([
    (r'/some-secret-api/websocket', WebSocketHandler),
])

if __name__ == '__main__':
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
