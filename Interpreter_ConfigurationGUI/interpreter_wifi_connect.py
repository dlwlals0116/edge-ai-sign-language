import redis
import os


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')

os.system('chcp 65001')

os.system("netsh wlan show networks interface=Wi-Fi")
Selected_SSID = input('접속을 원하는 SSID를 입력하세요 : ')
Selected_PW = input('접속을 원하는 SSID의 비밀번호를 입력하세요 : ')
config = """<?xml version=\"1.0\"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>"""+Selected_SSID+"""</name>
    <SSIDConfig>
        <SSID>
            <name>"""+Selected_SSID+"""</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>"""+Selected_PW+"""</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""

with open(Selected_SSID+".xml", 'w') as file:
    file.write(config)
    os.system("netsh wlan add profile filename=\""+Selected_SSID+".xml\""+" interface=Wi-Fi")

try:
    os.system("netsh wlan connect name=\""+Selected_SSID+"\" ssid=\""+Selected_SSID+"\" interface=Wi-Fi")
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
        conn.set('ssid', Selected_SSID, )
        conn.set('password', Selected_PW, )
except:
    print("Error")

os.system("pause")
