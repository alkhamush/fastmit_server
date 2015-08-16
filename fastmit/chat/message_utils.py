# -*- coding: utf-8 -*-
import json
from collections import defaultdict


def validate_message_packet(message_packet):
    try:
        if message_packet["type"] != "message":
            return False
        body = message_packet["body"]
        if type(body) != dict:
            return False
        if type(body["friendId"]) != str:
            return False
        message = body["message"]
        if type(message) != dict:
            return False
    except KeyError:
        return False


def generate_messages_packet(message_body_jsons):
    messages_packet = dict()
    messages_packet["type"] = "messages"
    messages_packet["body"] = list()

    friend_id_to_messages = defaultdict(list)

    for message_body_json in message_body_jsons:
        message_body = json.loads(message_body_json)
        friend_id_to_messages[message_body["friendId"]].append(message_body["message"])

    for friend_id, messages in friend_id_to_messages.iteritems():
        messages_from_friend = dict()
        messages_from_friend["friendId"] = friend_id
        messages_from_friend["messages"] = messages
        messages_packet["body"].append(messages_from_friend)

    return messages_packet