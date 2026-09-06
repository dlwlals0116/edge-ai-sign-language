import redis
import time


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

organization = input("OpenAI의 organization 값을 입력하세요: ")
print('\n')
OPENAI_API_KEY = input("OpenAI의 Key 값을 입력하세요: ")
print('\n')
model = input("OpenAI의 GPT 모델을 입력하세요: ")
print('\n')
actor1 = input("1번 헤드셋의 성우를 입력하세요. \n(alloy, echo, fable, onyx, nova, shimmer): ")
print('\n')
actor2 = input("2번 헤드셋의 성우를 입력하세요. \n(alloy, echo, fable, onyx, nova, shimmer): ")
print('\n')

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    if organization != '':
        conn.hset('openai_key', 'organization', organization)
        print('\norganization 설정이 완료되었습니다.')
    if OPENAI_API_KEY != '':
        conn.hset('openai_key', 'OPENAI_API_KEY', OPENAI_API_KEY)
        print('\nOPENAI_API_KEY 설정이 완료되었습니다.')
    if model != '':
        conn.hset('openai_key', 'model', model)
        print('\nGPT Model 설정이 완료되었습니다.')
    if actor1 != '':
        conn.hset('openai_key', 'actor1', actor1)
        print('\n1번 헤드셋의 성우(AI Voice Engine) 설정이 완료되었습니다.')
    if actor2 != '':
        conn.hset('openai_key', 'actor2', actor2)
        print('\n2번 헤드셋의 성우(AI Voice Engine) 설정이 완료되었습니다.')

time.sleep(3)
