import redis


def redis_connect():
    return redis.StrictRedis(host='localhost', port=6379, db=0)


def is_online(uid):
    redis_client = redis_connect()
    return redis_client.exists(uid)
