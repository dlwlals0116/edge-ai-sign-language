import redis


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    conn.set('hi_work', 'off')
