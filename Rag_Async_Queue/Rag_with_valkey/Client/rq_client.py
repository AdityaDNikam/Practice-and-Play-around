from redis import Redis
from rq import Queue, SimpleWorker

queue = Queue(connection=Redis(
    host="localhost",
    port=6379
))
