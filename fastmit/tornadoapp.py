# coding=utf-8
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fastmit.settings")
import json
import redis_utils
from django.core.exceptions import ObjectDoesNotExist

import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options, parse_command_line
from django.contrib.sessions.models import Session
define("port", default=8888, type=int)


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        print origin
        return True

    def open(self, *args):
        print "New connection"
	session =  self.get_cookie("sessionid")
	print session
	try:
		session = Session.objects.get(session_key=session)
	except ObjectDoesNotExist, e:
		print e
		return
	uid = int(session.get_decoded().get('_auth_user_id'))
	print uid
	print redis_utils.get_messages(uid)
	self.uid = uid
	self.application.webSocketPool[uid] = self
        #self.write_message("Welcome!")

    def on_message(self, message):
        print message
        message2 = json.loads(message)
        to = int(message2["body"]["id_friend"])
	print to
	message2["body"]["id_friend"] = str(self.uid)
	message = json.dumps(message2)
	print message
	redis_utils.add_message(to, message)
	self.application.webSocketPool[to].write_message(message)
        #self.write_message(message)

    def on_close(self):
	#del self.application.webSocketPool[self.uid]
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
