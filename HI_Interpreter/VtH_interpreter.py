import time
import os
import cv2
import redis
import requests
import threading
import torch
import mediapipe as mp
import numpy as np
import torch.nn as nn
import screeninfo
import Jetson.GPIO as GPIO
from PIL import ImageFont, ImageDraw, Image
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader


path = '/etc/netplan/50-cloud-init.yaml'
redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')
touch_pin = 7
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) 
GPIO.setup(touch_pin, GPIO.IN)
flag = False

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    cls_num = conn.get('cls_num').decode('utf-8')
    class_num = int(cls_num)


class SkeletonLSTM(nn.Module):
    def __init__(self):
        super(SkeletonLSTM, self).__init__()
        self.lstm1 = nn.LSTM(input_size=50, hidden_size=128, num_layers=1, batch_first=True)
        self.lstm2 = nn.LSTM(input_size=128, hidden_size=256, num_layers=1, batch_first=True)
        self.lstm3 = nn.LSTM(input_size=256, hidden_size=512, num_layers=1, batch_first=True)
        self.dropout1 = nn.Dropout(0.1)
        self.lstm4 = nn.LSTM(input_size=512, hidden_size=256, num_layers=1, batch_first=True)
        self.lstm5 = nn.LSTM(input_size=256, hidden_size=128, num_layers=1, batch_first=True)
        self.lstm6 = nn.LSTM(input_size=128, hidden_size=64, num_layers=1, batch_first=True)
        self.dropout2 = nn.Dropout(0.1)
        self.lstm7 = nn.LSTM(input_size=64, hidden_size=32, num_layers=1, batch_first=True)
        self.fc = nn.Linear(32, class_num)

    def forward(self, x) :
        x, _ = self.lstm1(x)
        x, _ = self.lstm2(x)
        x, _ = self.lstm3(x)
        x = self.dropout1(x)
        x, _ = self.lstm4(x)
        x, _ = self.lstm5(x)
        x, _ = self.lstm6(x)
        x = self.dropout2(x)
        x, _ = self.lstm7(x)
        x = self.fc(x[:, -1, :])
        return x


class MyDataset(Dataset):
    def __init__(self, seq_list):
        self.X = []
        self.y = []
        for dic in seq_list:
            self.y.append(dic['key'])
            self.X.append(dic['value'])

    def __getitem__(self, index):
        data = self.X[index]
        label = self.y[index]
        return torch.Tensor(np.array(data)), torch.tensor(np.array(int(label)))

    def __len__(self):
        return len(self.X)


if torch.cuda.is_available() == True:
    device = 'cuda:0'
    print('현재 가상환경 GPU 사용 가능상태')
else:
    device = 'cpu'
    print('GPU 사용 불가능 상태')


mp_pose = mp.solutions.pose
attention_dot = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
draw_line = [[0, 1], [0, 4], [1, 2], [2, 3], [3, 7], [4, 5], [5, 6], [6, 8], [9, 10], [11, 13], [13, 15], [12, 14],
             [14, 16], [11, 12], [11, 23], [23, 24], [12, 24], [15, 21], [16, 22], [15, 17], [16, 18], [17, 19],
             [18, 20], [15, 19], [16, 20]]


def threading_transmit(snd_txt):
    conn.set('1st_word', snd_txt)
    vip = conn.get('_headset').decode('utf-8')
    requests.post('http://{}:8000/VtH_interpreter/'.format(vip))


def make_mp4(video_path):
    cap = cv2.VideoCapture(video_path)
    img_list = []
    interval = 1
    if cap.isOpened():
        cnt = 0
        current_button = False
        last_button = False
        touch_state = False
        touch_cnt = 0
        while True:
            ret, frame = cap.read()
            print('start')
            current_button = GPIO.input(touch_pin)
            if last_button == 0 and current_button == 1:
                touch_state = not touch_state
            last_button = current_button
            print('touch_state', touch_state)
            
            if not touch_state:
                if ret:
                    img = cv2.resize(frame, (640, 480))
                    if cnt == interval:
                        img_list.append(img)
                        cnt = 0
                    cv2.imshow('frame', img)
                    cv2.waitKey(1)
                    cnt += 1
                touch_cnt = 1
            else:
                if touch_cnt == 1:
                    break
    cap.release()
    cv2.destroyAllWindows()

    print('저장된 frame의 개수: {}'.format(len(img_list)))

    net.eval()
    out_img_list = []
    length = 20
    word_insert = []
    status = 'None'
    pose = mp_pose.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.3)
    print('시퀀스 데이터 분석 중...')
    xy_list_list = []
    for img in tqdm(img_list):
        result = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not result.pose_landmarks: continue
        xy_list = []
        idx = 0
        draw_line_dic = {}
        for x_and_y in result.pose_landmarks.landmark:
            if idx in attention_dot:
                xy_list.append(x_and_y.x)
                xy_list.append(x_and_y.y)
                x, y = int(x_and_y.x*640), int(x_and_y.y*480)
                draw_line_dic[idx] = (x, y)
            idx += 1
        xy_list_list.append(xy_list)
        for line in draw_line:
            x1, y1 = draw_line_dic[line[0]][0], draw_line_dic[line[0]][1]
            x2, y2 = draw_line_dic[line[1]][0], draw_line_dic[line[1]][1]
            img = cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        if len(xy_list_list) == length:
            dataset = []
            dataset.append({'key': 0, 'value': xy_list_list})
            dataset = MyDataset(dataset)
            dataset = DataLoader(dataset)
            xy_list_list = []
            with redis.StrictRedis(connection_pool=redis_pool) as conn:
                snd_txt = ''
                cls_num = conn.get('cls_num')
                for data, label in dataset:
                    data = data.to(device)
                    with torch.no_grad():
                        result = net(data)
                        _, out = torch.max(result, 1)
                        for x in range(int(cls_num)):
                            if out.item() == x:
                                status = conn.hget('sign_label', str(x)).decode('utf-8')
                                print(status)
                        word_insert.append(status)
                        tmp = ''
                        word_cnt = 0
                        for word in word_insert:
                            if tmp == word:
                                word_cnt += 1
                            if word_cnt == 3:
                                snd_txt = tmp
                                word_cnt = 0
                            tmp = word
                        print(snd_txt)
                        if snd_txt:
                            threading.Thread(target=threading_transmit(snd_txt)).start()
                            conn.set('1st_word', snd_txt)
                            vip = conn.get('_headset').decode('utf-8')
                            requests.post('http://{}:8000/VtH_interpreter/'.format(vip))

        cv2.putText(img, status, (0, 50), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 255), 2)
        out_img_list.append(img)
    filename = '/home/homer/HI_Interpreter/video_out.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    fps = 30
    frameSize = (640, 480)
    isColor = True
    out = cv2.VideoWriter(filename, fourcc, fps, frameSize, isColor)
    for img in out_img_list:
        out.write(img)
    out.release()


def predict(img_list):
    print('저장된 frame의 개수: {}'.format(len(img_list)))

    net.eval()
    out_img_list = []
    length = 20
    word_insert = []
    status = 'None'
    pose = mp_pose.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.5)
    print('시퀀스 데이터 분석 중...')
    xy_list_list = []
    for img in tqdm(img_list):
        result = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not result.pose_landmarks: continue
        xy_list = []
        idx = 0
        draw_line_dic = {}
        for x_and_y in result.pose_landmarks.landmark:
            if idx in attention_dot:
                xy_list.append(x_and_y.x)
                xy_list.append(x_and_y.y)
                x, y = int(x_and_y.x * 640), int(x_and_y.y * 480)
                draw_line_dic[idx] = (x, y)
            idx += 1
        xy_list_list.append(xy_list)
        for line in draw_line:
            x1, y1 = draw_line_dic[line[0]][0], draw_line_dic[line[0]][1]
            x2, y2 = draw_line_dic[line[1]][0], draw_line_dic[line[1]][1]
            img = cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        if len(xy_list_list) == length:
            dataset = []
            dataset.append({'key': 0, 'value': xy_list_list})
            dataset = MyDataset(dataset)
            dataset = DataLoader(dataset)
            xy_list_list = []
            with redis.StrictRedis(connection_pool=redis_pool) as conn:
                snd_txt = ''
                cls_num = conn.get('cls_num')
                for data, label in dataset:
                    data = data.to(device)
                    with torch.no_grad():
                        result = net(data)
                        _, out = torch.max(result, 1)
                        for x in range(int(cls_num)):
                            if out.item() == x:
                                status = conn.hget('sign_label', str(x)).decode('utf-8')
                                print(status)
                        word_insert.append(status)
                        tmp = ''
                        word_cnt = 0
                        for word in word_insert:
                            if tmp == word:
                                word_cnt += 1
                            if word_cnt == 3:
                                snd_txt = tmp
                                word_cnt = 0
                            tmp = word
                        print(snd_txt)
                        if snd_txt:
                            conn.set('1st_word', snd_txt)
                            vip = conn.get('_headset').decode('utf-8')
                            requests.post('http://{}:8000/VtH_interpreter/'.format(vip))

        cv2.putText(img, status, (0, 50), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 255), 2)
        out_img_list.append(img)
    filename = './video_out.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    fps = 30
    frameSize = (640, 480)
    isColor = True
    out = cv2.VideoWriter(filename, fourcc, fps, frameSize, isColor)
    for img in out_img_list:
        out.write(img)
    out.release()
    flag = False
    time.sleep(1)


def sign_play():
    global flag
    fontpath = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
    font = ImageFont.truetype(fontpath, size=40)
    with redis.StrictRedis(connection_pool=redis_pool) as conn:
                cam = conn.get('camera').decode('utf-8')
    cap = cv2.VideoCapture('rtsp://admin@{}:8554/stream0'.format(cam))
    img_list = []
    interval = 1
    if cap.isOpened():
        cnt = 0
        while True:
            print('ready')
            touch_state = GPIO.input(touch_pin)
            print(touch_state)
            if not touch_state:
                ret, frame = cap.read()
                if ret:
                    img = cv2.resize(frame, (640, 480))
                    if cnt == interval:
                        cnt = 0
                    pt1 = 200, 50
                    pt2 = 450, 480
                    cv2.rectangle(img, pt1, pt2, (0, 255, 0), 2)
                    W, H = (480, 640)
                    img_pil = Image.fromarray(img)
                    draw = ImageDraw.Draw(img_pil)
                    _, _, w, h = font.getbbox('Ready')
                    draw.text(((W - w) / 2 + 90, (H - h) / 2 - 60), 'Ready', font=font, fill=(255, 255, 255, 0))
                    img = np.array(img_pil)
                    cv2.imshow('frame', img)
                    cv2.waitKey(1)
                    cnt += 1
            else:
                break
        cnt = 0
        current_button = False
        last_button = False
        touch_state = False
        touch_cnt = 0
        while True:
            ret, frame = cap.read()
            print('start')
            current_button = GPIO.input(touch_pin)
            if last_button == 0 and current_button == 1:
                touch_state = not touch_state
            last_button = current_button
            print('touch_state', touch_state)
            
            if touch_state:
                if ret:
                    img = cv2.resize(frame, (640, 480))
                    if cnt == interval:
                        img_list.append(img)
                        cnt = 0
                    cv2.imshow('frame', img)
                    cv2.waitKey(1)
                    cnt += 1
                touch_cnt = 1
            else:
                if touch_cnt == 1:
                    # threading.Thread(target=predict(img_list)).start()
                    print('저장된 frame의 개수: {}'.format(len(img_list)))
                    net.eval()
                    out_img_list = []
                    length = 20
                    word_insert = []
                    status = 'None'
                    pose = mp_pose.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.5)
                    print('시퀀스 데이터 분석 중...')
                    xy_list_list = []
                    for img in tqdm(img_list):
                        result = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                        if not result.pose_landmarks: continue
                        xy_list = []
                        idx = 0
                        draw_line_dic = {}
                        for x_and_y in result.pose_landmarks.landmark:
                            if idx in attention_dot:
                                xy_list.append(x_and_y.x)
                                xy_list.append(x_and_y.y)
                                x, y = int(x_and_y.x * 640), int(x_and_y.y * 480)
                                draw_line_dic[idx] = (x, y)
                            idx += 1
                        xy_list_list.append(xy_list)
                        for line in draw_line:
                            x1, y1 = draw_line_dic[line[0]][0], draw_line_dic[line[0]][1]
                            x2, y2 = draw_line_dic[line[1]][0], draw_line_dic[line[1]][1]
                            img = cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        if len(xy_list_list) == length:
                            dataset = []
                            dataset.append({'key': 0, 'value': xy_list_list})
                            dataset = MyDataset(dataset)
                            dataset = DataLoader(dataset)
                            xy_list_list = []
                            with redis.StrictRedis(connection_pool=redis_pool) as conn:
                                snd_txt = ''
                                cls_num = conn.get('cls_num')
                                for data, label in dataset:
                                    data = data.to(device)
                                    with torch.no_grad():
                                        result = net(data)
                                        _, out = torch.max(result, 1)
                                        for x in range(int(cls_num)):
                                            if out.item() == x:
                                                status = conn.hget('sign_label', str(x)).decode('utf-8')
                                                print(status)
                                        word_insert.append(status)
                                        tmp = ''
                                        word_cnt = 0
                                        for word in word_insert:
                                            if tmp == word:
                                                word_cnt += 1
                                            if word_cnt == 3:
                                                snd_txt = tmp
                                                word_cnt = 0
                                            tmp = word
                                        print(snd_txt)
                                        if snd_txt:
                                            conn.set('1st_word', snd_txt)
                                            vip = conn.get('_headset').decode('utf-8')
                                            requests.post('http://{}:8000/VtH_interpreter/'.format(vip))

                        cv2.putText(img, status, (0, 50), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 255), 2)
                        out_img_list.append(img)
                    filename = './video_out.mp4'
                    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
                    fps = 30
                    frameSize = (640, 480)
                    isColor = True
                    out = cv2.VideoWriter(filename, fourcc, fps, frameSize, isColor)
                    for img in out_img_list:
                        out.write(img)
                    out.release()
                    touch_cnt = 0                   
    cap.release()
    cv2.destroyAllWindows()


def screen_view():
    screen_id = 0
    is_color = False
    screen = screeninfo.get_monitors()[screen_id]
    width, height = screen.width, screen.height
    if is_color:
        image = np.ones((height, width, 3), dtype=np.float32)
        image[:10, :10] = 0  # black at top-left corner
        image[height - 10:, :10] = [1, 0, 0]  # blue at bottom-left
        image[:10, width - 10:] = [0, 1, 0]  # green at top-right
        image[height - 10:, width - 10:] = [0, 0, 1]  # red at bottom-right
    else:
        image = np.ones((height, width), dtype=np.float32)
        image[0, 0] = 0  # top-left corner
        image[height - 2, 0] = 0  # bottom-left
        image[0, width - 2] = 0  # top-right
        image[height - 2, width - 2] = 0  # bottom-right
    window_name = 'projector'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.moveWindow(window_name, screen.x - 1, screen.y - 1)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow(window_name, image)
    cv2.waitKey(1)
        

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
                hi_ip = os.popen("ifconfig wlan0 | grep 'inet ' |awk '{print $2}'").read().strip()
                print(hi_ip)
                with redis.StrictRedis(connection_pool=redis_pool) as conn:
                    conn.set('hi_ip', hi_ip)
            else:
                replace_in_file(path, cur_ssid, db_ssid)
                replace_in_file(path, cur_password, db_password)
                os.system('reboot')

            with redis.StrictRedis(connection_pool=redis_pool) as conn:
                vip1 = conn.get('vi_ip1').decode('utf-8')
                vip2 = conn.get('vi_ip2').decode('utf-8')
            
            device = torch.device('cuda')
            net = SkeletonLSTM()
            net.load_state_dict(torch.load('/home/homer/HI_Interpreter/model/homer.pt'))
            net.to(device)
            
            while True:
                sign_play()
                # make_mp4('/home/homer/HI_Interpreter/test_video/test.mp4')
                time.sleep(1)
    else:
        with open(path, 'r') as f:
            lines = f.readlines()
            cur_ssid = lines[15][17:-3]
            cur_password = lines[16][31:-2]
            print(cur_ssid)
            print(cur_password)
        replace_in_file(path, cur_ssid, 'homer')
        replace_in_file(path, cur_password, '12345678')
        os.system('reboot')


