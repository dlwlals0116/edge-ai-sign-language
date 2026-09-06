import os
import time
import paramiko
import redis


user = os.environ['USERNAME']
redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    work = conn.get('server_work').decode('utf-8')
    hip = conn.get('hi_ip').decode('utf-8')
    hi_state = conn.get('hi_work').decode('utf-8')
if work == 'off':
    print('\n딥러닝 서버가 꺼져있습니다.')
elif hi_state == 'off':
    print('\n청각장애인용 통역기가 꺼져있습니다.')
else:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname='', port=2222, username='', password='')

    stdin, stdout, stderr = client.exec_command('ls -1U /home/homer/model | wc -l')
    output = ''

    for line in stdout.readlines():
        output = output + line

    if output == '1\n':
        sftp = client.open_sftp()
        sftp.get('/home/homer/model/homer.pt', 'C:\\Users\\{}\\Desktop\\homer.pt'.format(user))
        sftp.close()

    client.connect(hostname='{}'.format(hip), username='homer', password='homer')
    sftp = client.open_sftp()
    sftp.put('C:\\Users\\{}\\Desktop\\homer.pt'.format(user), '/home/homer/HI_Interpreter/model/homer.pt')
    print('\n모델 업데이트가 완료되었습니다.\n')
    os.remove('C:\\Users\\{}\\Desktop\\homer.pt'.format(user))
    sftp.close()
    client.close()
time.sleep(3)
