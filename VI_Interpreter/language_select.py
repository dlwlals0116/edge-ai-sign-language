import os
import redis
import time
from periphery import GPIO
import redis

SW_PIN = 1
DT_PIN = 0
CLK_PIN = 2

DIRECTION_CW = 0
DIRECTION_CCW = 1

counter = 0
lang_num = 0
direction = DIRECTION_CW
CLK_state = 0
prev_CLK_state = 0
CLK = GPIO("/dev/gpiochip3", CLK_PIN, "in")
DT = GPIO("/dev/gpiochip1", DT_PIN, "in")
SW = GPIO("/dev/gpiochip1", SW_PIN, "in")
SW.bias = "pull_up"
prev_CLK_state = CLK.read()
prev_button_state = True

redis_pool = redis.ConnectionPool(host='192.168.10.9', port=6379, db=0, max_connections=4, password='')

def tts(lang):
    global client
    response = client.audio.speech.create(
        model="tts-1",
        voice=os.getenv("actor"),
        input=lang,
    )
    response.stream_to_file(f"Sound/{lang}.mp3")


if __name__ == "__main__":
    try:
        while True:
            CLK_state = CLK.read()
            if CLK_state != prev_CLK_state and CLK_state == True:
                if DT.read() == True:
                    counter -= 1
                    direction = DIRECTION_CCW
                    if counter <= 0:
                        counter = 10
                else:
                    counter += 1
                    direction = DIRECTION_CW
                    if counter >= 11:
                        counter = 1

                print("Rotary Encoder:: direction:", "CLOCKWISE" if direction == DIRECTION_CW else "ANTICLOCKWISE",
                      "- count:", counter)
                with redis.StrictRedis(connection_pool=redis_pool) as conn:
                    lang = conn.hget('language_type', str(counter)).decode('utf-8')    
                    os.system(f"mpg123 Sound/{lang}.mp3")
            prev_CLK_state = CLK_state

            button_state = SW.read()
            if button_state != prev_button_state:
                time.sleep(0.01)
                if button_state == False:
                    print("The button is pressed")
                    with redis.StrictRedis(connection_pool=redis_pool) as conn:
                        if lang == '자연어':
                            conn.set('select_interpreter', 'vision')
                        elif lang == '수어':
                            conn.set('select_interpreter', 'hearing')
                            vip1 = conn.get('vi_ip1').decode('utf-8')
                            conn.set('_headset', vip1)
                            conn.set('camera', '192.168.10.7')
                        elif lang == '챗봇':
                            conn.set('select_interpreter', 'chatbot')
                        elif lang == '대화시작':
                            conn.set('start_talk1', 'on')
                        elif lang == '대화중지':
                            conn.set('start_talk1', 'off')
                        else:
                            conn.set('selected_lang1', lang)
                    os.system("mpg123 Sound/selected.mp3")
                else:
                    button_pressed = False
            prev_button_state = button_state
            time.sleep(0.001)
    except:
        CLK.close()
        DT.close()
        SW.close()
