import sys
import redis


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')
print('현재 설정된 언어 목록입니다.\n')


with redis.StrictRedis(connection_pool=redis_pool) as conn:
    for i in range(1,7):
        print(f"{i}. {conn.hget('language_type', str(i+2)).decode('utf-8')}")
    while True:
        try:
            change_num = int(input("\n바꿀 언어 번호를 선택해주세요. (q 나가기): "))
            if change_num == 'q':
                break
            elif change_num >= 1 or change_num <= 6:
                change_lang = input("변경하실 언어를 입력해주세요: ")
                conn.hset('language_type', change_num+2, change_lang)
                print("변경이 완료되었습니다.")
            else:
                sys.exit(0)
        except ValueError:
            sys.exit(0)

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    for i in range(1,7):
        print(f"{i}. {conn.hget('language_type', str(i)).decode('utf-8')}")
