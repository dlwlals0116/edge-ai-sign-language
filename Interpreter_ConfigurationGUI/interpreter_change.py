import time
import redis


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

src = input("통역기 종류를 숫자로 입력하세요. \n(1. 시각장애인용 2. 청각장애인용): ")

if src == '1':
    src = 'vision'
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        conn.set('select_interpreter', src)
    print('\n설정이 완료되었습니다.')
elif src == '2':
    src = 'hearing'
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        conn.set('select_interpreter', src)
    print('\n')
    headset = input("청각장애인용 통역기와 연결할 헤드셋을 선택하세요. \n(1. 1번 헤드셋 2. 2번 헤드셋): ")

    if headset == '1':
        with redis.StrictRedis(connection_pool=redis_pool) as conn:
            vip1 = conn.get('vi_ip1').decode('utf-8')
            print(vip1)
            conn.set('_headset', vip1)
            conn.set('camera', '192.168.10.7')
            print('\n설정이 완료되었습니다.')
    elif headset == '2':
        with redis.StrictRedis(connection_pool=redis_pool) as conn:
            vip2 = conn.get('vi_ip2').decode('utf-8')
            print(vip2)
            conn.set('_headset', vip2)
            conn.set('camera', '192.168.10.8')
            print('\n설정이 완료되었습니다.')

time.sleep(3)

