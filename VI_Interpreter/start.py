import time
import os
import redis
import wave
import pyaudio
import audioop
import requests


path = '/etc/netplan/50-cloud-init.yaml'


def voice_rec(sound_volume, exit_volume):
    po = pyaudio.PyAudio()  # 녹음 기능을 위한 pyaudio 초기화
    for index in range(po.get_device_count()):
        desc = po.get_device_info_by_index(index)
        # if desc["name"] == "record":
        print("DEVICE: %s  INDEX:  %s  RATE:  %s " % (desc["name"], index, int(desc["defaultSampleRate"])))

    FORMAT = pyaudio.paInt16
    CHANNELS = 1  # 모노 음성
    RATE = 44100  # 전송률
    CHUNK = 640  # 전송 단위 크기
    RECORD_SECONDS = 7  # 녹음 시간
    WAVE_OUTPUT_FILENAME = "Sound/talk.mp3"  # 녹음 생성 오디오 파일

    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []

    print("---음성 녹음 시작---")

    while True:
        data = stream.read(CHUNK)
        rms = audioop.rms(data, 2)
        print('currunt: ', rms)
        if rms > sound_volume:
            print('input: ', rms)  # 마이크에 기준 볼륨보다 큰 소리가 들어오면 녹음 작동
            frames.append(data)
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            data = stream.read(CHUNK)
            rms = audioop.rms(data, 2)
            if rms < exit_volume:
                print('exit: ', rms)  # 큰 소리가 들어오지 않으면 녹음 종료
                break
            else:
                continue

    print("---음성 녹음 완료---")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    time.sleep(0.1)


def replace_in_file(path, cur, new):
    f_read = open(path, 'r')
    lines = f_read.readlines()
    f_read.close()
    f_write = open(path, 'w')
    for line in lines:
        f_write.write(line.replace(cur, new))
    f_write.close()


if __name__ == "__main__":
    connect_value = os.popen("iw wlan0 link").read().strip()
    if connect_value != 'Not connected.':
        ip = os.popen("ping -c 2 google.com").read().strip()
        if 'transmitted' in ip:
            redis_pool = redis.ConnectionPool(host='192.168.10.9', port=6379, db=0, max_connections=4, password='')
            with redis.StrictRedis(connection_pool=redis_pool) as conn:
                db_ssid = conn.get('ssid').decode('utf-8')
                db_password = conn.get('password').decode('utf-8')
            print(db_ssid, db_password)

            with open(path, 'r') as f:
                lines = f.readlines()
                cur_ssid = lines[15][17:-3]
                cur_password = lines[16][31:-2]
                print(cur_ssid)
                print(cur_password)

            if db_ssid == cur_ssid:
                vi_ip1 = os.popen("ifconfig wlan0 | grep 'inet ' |awk '{print $2}'").read().strip()
                print(vi_ip1)
                with redis.StrictRedis(connection_pool=redis_pool) as conn:
                    conn.set('vi_ip1', vi_ip1)
            else:
                replace_in_file(path, cur_ssid, db_ssid)
                replace_in_file(path, cur_password, db_password)
                os.system("mpg123 ./Sound/no_match.mp3")
                os.system('reboot')
            
            while True:
                with redis.StrictRedis(connection_pool=redis_pool) as conn:
                    address = conn.get('select_interpreter').decode('utf-8')
                    vip2 = conn.get('vi_ip2').decode('utf-8')
                    hip = conn.get('hi_ip').decode('utf-8')
                    sound_volume = conn.get('sound_volume1').decode('utf-8')
                    exit_volume = conn.get('exit_volume1').decode('utf-8')
                    start_talk = conn.get('start_talk1').decode('utf-8')
                    conn.set('send_txt', '')
                print(address)
                if start_talk == 'on':
                    if address == 'vision':
                        voice_rec(int(sound_volume), int(exit_volume))
                        os.system("mpg123 ./Sound/recording.mp3")
                        start_talk = conn.get('start_talk1').decode('utf-8')
                        if start_talk == 'off':
                            continue
                        files = {'file': open('./Sound/talk.mp3', 'rb')}
                        requests.post('http://{}:8000/interpreter/'.format(vip2), files=files)
                        os.system("mpg123 ./Sound/transmitting.mp3")
                    elif address == 'hearing':
                        voice_rec(int(sound_volume), int(exit_volume))
                        os.system("mpg123 ./Sound/recording.mp3")
                        start_talk = conn.get('start_talk1').decode('utf-8')
                        if start_talk == 'off':
                            continue
                        files = {'file': open('./Sound/talk.mp3', 'rb')}
                        response = requests.post('http://127.0.0.1:8000/self_interpreter/', files=files)
                        res = response.json()
                        print(res)
                        with redis.StrictRedis(connection_pool=redis_pool) as conn:
                            conn.set('send_txt', res)
                            requests.post('http://{}:8000/HtV_interpreter/'.format(hip))
                            os.system("mpg123 ./Sound/transmitting.mp3")
                        os.system("rm ./Sound/talk.mp3")
                    elif address == 'chatbot':
                        voice_rec(int(sound_volume), int(exit_volume))
                        os.system("mpg123 ./Sound/recording.mp3")
                        start_talk = conn.get('start_talk1').decode('utf-8')
                        if start_talk == 'off':
                            continue
                        files = {'file': open('./Sound/talk.mp3', 'rb')}
                        response = requests.get('http://127.0.0.1:8000/chatbot/')
                time.sleep(3)
        else:
            os.system("mpg123 ./Sound/no_ip.mp3")
            os.system('reboot')
    else:
        with open(path, 'r') as f:
            lines = f.readlines()
            cur_ssid = lines[15][17:-3]
            cur_password = lines[16][31:-2]
            print(cur_ssid)
            print(cur_password)
        replace_in_file(path, cur_ssid, 'CodeFair_Homer_5G')
        replace_in_file(path, cur_password, 'homerhomer')
        os.system("mpg123 ./Sound/no_match.mp3")
        os.system('reboot')
