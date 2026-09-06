import threading
import time
import redis
import subprocess


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')


def training_start():
    subprocess.call([r"./plink.exe", "-ssh", "-P", "",
                     "", "-pw", "", "-C",
                     "./autostart.sh"],
                    shell=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)


def trianing_view():
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        state = conn.get('model_training').decode('utf-8')
    try:
        if state == 'stop':
            conn.set('model_training', 'start')
            threading.Thread(training_start()).start()
        else:
            while True:
                print('학습중입니다.')
    except:
        with redis.StrictRedis(connection_pool=redis_pool) as conn:
            conn.set('model_training', 'stop')
        time.sleep(3)

if __name__ == '__main__':
    trianing_view()