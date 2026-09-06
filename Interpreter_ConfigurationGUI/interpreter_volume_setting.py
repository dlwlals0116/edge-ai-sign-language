import sys
import redis
import time


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

src = input("헤드셋의 종류를 숫자로 선택하세요. \n(1. 1번 헤드셋 2. 2번 헤드셋): ")

if src == '1':
    headset = ['sound_volume1', 'exit_volume1']
    print('1번 헤드셋을 선택하셨습니다.')
elif src == '2':
    headset = ['sound_volume2', 'exit_volume2']
    print('2번 헤드셋을 선택하셨습니다.')
else:
    sys.exit(0)


start = input("\n마이크의 작동 시작 dB을 선택하세요. \n숫자로 입력(1000~10000): ")
end = input("\n마이크의 작동 끝 dB을 선택하세요. \n숫자로 입력(0~1500): ")

if start >= '1000' and end <= '1500':
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        conn.set(headset[0],  start)
        conn.set(headset[1], end)
    print('\n설정이 완료되었습니다.')

time.sleep(3)
