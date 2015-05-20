# coding=utf-8

import json

import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options, parse_command_line

define("port", default=8888, type=int)


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        print origin
        return True

    def open(self, *args):
        print "New connection"
        #self.write_message("Welcome!")

    def on_message(self, message):
        print message
        message = json.loads(message)
        message["body"]["id_message"] += "1" 
        message = json.dumps(message)
        self.write_message(message)

    def on_close(self):
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
