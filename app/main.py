import os

import redis

host = os.environ["REDIS_HOST"]
r = redis.Redis(host=host, port=6379)

if r.ping():
    print("PONG")
