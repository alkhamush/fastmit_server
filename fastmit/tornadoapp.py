# -*- coding: utf-8 -*-
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fastmit.settings")
import json
import message_utils
import redis_utils
from django.core.exceptions import ObjectDoesNotExist

import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options
from django.contrib.sessions.models import Session

define("port", default=8888, type=int)


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        print origin
        return True

    def open(self, *args):
        print "New connection"
        session = self.get_cookie("sessionid")
        print session
        try:
            session = Session.objects.get(session_key=session)
        except ObjectDoesNotExist:
            self.close()
            return
        uid = int(session.get_decoded().get('_auth_user_id'))
        print uid

        self.uid = uid
        self.application.webSocketPool[uid] = self

        message_bodies = redis_utils.get_messages(uid)
        messages_packet = message_utils.generate_messages_packet(message_bodies)
        messages_packet_json = json.dumps(messages_packet)
        self.application.webSocketPool[uid].write_message(messages_packet_json)
        print messages_packet_json

    def on_message(self, message_packet_json):
        print message_packet_json
        message_packet = json.loads(message_packet_json)

        # if not message_utils.validate_message_packet(message_packet):
        #     print message_packet_json
        #     return

        to = int(message_packet["body"]["friendId"])
        print to

        message_packet["body"]["friendId"] = str(self.uid)
        print message_packet
        if to in self.application.webSocketPool:
            message_packet_json = json.dumps(message_packet)
            self.application.webSocketPool[to].write_message(message_packet_json)
        else:
            message_body_json = json.dumps(message_packet["body"])
            redis_utils.add_message(to, message_body_json)

    def on_close(self):
        try:
            del self.application.webSocketPool[self.uid]
        except AttributeError:
            print "Connection closed"


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
