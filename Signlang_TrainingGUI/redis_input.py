import os
import redis


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

src = input("파일명 입력: ")

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    while True:
        context = input("수어 내용 입력: ")
        if context == '':
            break
        conn.set(context, './Video/{}.mp4'.format(src))
        conn.set(src, context)
        data = conn.get(context)
        print(data)

os.system('pause')
