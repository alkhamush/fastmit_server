# -*- coding: utf-8 -*-
import redis


def redis_connect():
    return redis.StrictRedis(host='localhost', port=6379, db=0)


def add_message(addressee, message):
    redis_client = redis_connect()
    redis_client.rpush("messages_to_{0}".format(addressee), message)


def get_messages(addressee):
    redis_client = redis_connect()
    key = "messages_to_{0}".format(addressee)
    messages = redis_client.lrange(key, 0, -1)
    redis_client.delete(key)
    return messages
