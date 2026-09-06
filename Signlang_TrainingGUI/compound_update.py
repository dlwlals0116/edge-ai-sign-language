import redis


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    while True:
        compound = input("복합어 입력: ")
        if compound == '':
            break
        context = input("수어식 단어 입력: ")
        if context == '':
            break
        conn.hset('compound_key', compound, context)
        print('\n설정이 완료되었습니다.\n')

