import redis

def redis_connect():
    return redis.StrictRedis(host='localhost', port=6379, db=0)

def add_message(addressee, message):
	redis_client = redis_connect()
	redis_client.lpush("messages_to_{0}".format(addressee), message)

def get_messages(addressee):
	redis_client = redis_connect()
	return redis_client.lrange("messages_to_{0}".format(addressee), 0, -1)
		
