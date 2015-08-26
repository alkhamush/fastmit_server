import redis


def redis_connect():
    return redis.StrictRedis(host='localhost', port=6379, db=0)


def is_online(uid):
    redis_client = redis_connect()
    return redis_client.exists(uid)


def get_gcm_key(uid):
    redis_client = redis_connect()
    key = "gcm{0}".format(uid)
    return redis_client.get(key)