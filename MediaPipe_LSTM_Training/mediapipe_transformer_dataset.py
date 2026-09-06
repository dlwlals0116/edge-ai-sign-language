import os
import time
import random
import cv2
import gc
import redis
import torch
import mediapipe as mp
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import torch.nn.functional as F
from torch.cuda import empty_cache
from torch.optim import Adam
from torch.utils.data import Dataset, DataLoader
from torch.utils.data import random_split
from IPython.display import clear_output


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')
mp_pose = mp.solutions.pose
attention_dot = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
draw_line = [[0, 1], [0, 4], [1, 2], [2, 3], [3, 7], [4, 5], [5, 6], [6, 8], [9, 10], [11, 13], [13, 15], [12, 14],
             [14, 16], [11, 12], [11, 23], [23, 24], [12, 24], [15, 21], [16, 22], [15, 17], [16, 18], [17, 19],
             [18, 20], [15, 19], [16, 20]]


def show_skeleton(video_path, interval, attention_dot, draw_line):
    xy_list_list, xy_list_list_flip = [], []
    cv2.destroyAllWindows()
    pose = mp_pose.Pose(static_image_mode=True, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.3)
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        cnt = 0
        while True:
            ret, img = cap.read()
            if cnt == interval and ret == True:
                cnt = 0
                xy_list, xy_list_flip = [], []
                img = cv2.resize(img, (640, 480))
                results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                if not results.pose_landmarks:
                    continue
                idx = 0
                draw_line_dic = {}
                for x_and_y in results.pose_landmarks.landmark:
                    if idx in attention_dot:
                        xy_list.append(x_and_y.x)
                        xy_list.append(x_and_y.y)
                        xy_list_flip.append(1 - x_and_y.x)
                        xy_list_flip.append(x_and_y.y)
                        x, y = int(x_and_y.x*640), int(x_and_y.y*480)
                        draw_line_dic[idx] = [x, y]
                    idx += 1
                xy_list_list.append(xy_list)
                xy_list_list_flip.append(xy_list_flip)
                for line in draw_line:
                    x1, y1 = draw_line_dic[line[0]][0], draw_line_dic[line[0]][1]
                    x2, y2 = draw_line_dic[line[1]][0], draw_line_dic[line[1]][1]
                    img = cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # cv2.imshow('Landmarks', img)
                cv2.waitKey(1)
            elif ret == False:
                break
            cnt += 1
    cap.release()
    cv2.destroyAllWindows()
    return xy_list_list + xy_list_list_flip


video_path = './train_video'
video_name_list = os.listdir(video_path)
dataset = []
length = 20
interval = 1
cls_num = len(video_name_list)

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    conn.set('cls_num', cls_num)
    for x in range(cls_num):
        if video_name_list[x]:
            label = x
        skel_data = show_skeleton('{}/{}'.format(video_path, video_name_list[x]), interval, attention_dot, draw_line)
        for idx in range(0, len(skel_data), int(length/2)):
            seq_list = skel_data[idx:idx+length]
            if len(seq_list) == length:
                dataset.append({'key': label, 'value': seq_list})
        conn.hset('sign_label', label, video_name_list[x][:-4])
    random.shuffle(dataset)
    print(dataset)


if torch.cuda.is_available() == True:
    device = 'cuda:0'
    print('현재 가상환경 GPU 사용 가능상태')
else:
    device = 'cpu'
    print('GPU 사용 불가능 상태')


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


split_ratio = [0.8, 0.1, 0.1]
train_len = int(len(dataset) * split_ratio[0])
val_len = int(len(dataset) * split_ratio[1])
test_len = len(dataset) - train_len - val_len
print('{}, {}, {}'.format(train_len, val_len, test_len))

train_dataset = MyDataset(dataset)
train_data, valid_data, test_data = random_split(train_dataset, [train_len, val_len, test_len])

train_loader = DataLoader(train_data, batch_size=8)
val_loader = DataLoader(valid_data, batch_size=8)
test_loader = DataLoader(test_data, batch_size=8)


class Transformer(nn.Module):
    def __init__(self, out_channel):
        super(Transformer, self).__init__()

        self.out_channel = out_channel
        self.layerNorm = nn.LayerNorm(out_channel, 1e-6)
        self.multi_head_attn = Multi_Head_Attention(out_channel)
        self.feed_forward = Feed_Forward(out_channel)

    def forward(self, input_):
        norm_input = self.layerNorm(input_)
        mha = self.multi_head_attn(norm_input)
        out = self.feed_forward(mha)
        return out


class Multi_Head_Attention(nn.Module):
    def __init__(self, out_channel):
        super(Multi_Head_Attention, self).__init__()

        self.W_Q = nn.Linear(out_channel, out_channel)
        self.W_K = nn.Linear(out_channel, out_channel)
        self.W_V = nn.Linear(out_channel, out_channel)

        self.attn = Dot_Prod_Attention()

    def forward(self, input_):
        Q = self.W_Q(input_)
        K = self.W_K(input_)
        V = self.W_V(input_)

        attention = self.attn(Q, K, V)

        return attention + input_


class Dot_Prod_Attention(nn.Module):
    def __init__(self):
        super(Dot_Prod_Attention, self).__init__()
        self.softmax = nn.Softmax(dim=2)

    def forward(self, Q, K, V):
        score = torch.matmul(Q, K.transpose(1, 2))
        score = torch.matmul(score, V)
        attn = self.softmax(score)
        return attn


class Feed_Forward(nn.Module):
    def __init__(self, out_channel):
        super(Feed_Forward, self).__init__()

        self.layerNorm = nn.LayerNorm(out_channel, 1e-6)
        self.fc1 = nn.Linear(out_channel, 4 * out_channel)
        self.fc2 = nn.Linear(4 * out_channel, out_channel)

    def forward(self, multi_head_attn_out):
        norm_out = self.layerNorm(multi_head_attn_out)
        out = F.gelu(self.fc1(norm_out))
        out = self.fc2(out)
        return out + multi_head_attn_out


class skeleton_Transformer(nn.Module):
    def __init__(self, out_channel, num_class):
        super(skeleton_Transformer, self).__init__()
        self.cls_tok = nn.Parameter(torch.randn(1, 1, out_channel))
        self.linear_emb = nn.Linear(out_channel, out_channel)
        self.tranformer = nn.ModuleList([Transformer(out_channel) for _ in range(8)])
        self.classifier = nn.Linear(out_channel, num_class)

    def forward(self, x):
        batch_size = x.shape[0]
        cls_toks = self.cls_tok.repeat(batch_size, 1, 1)
        emb_mat = self.linear_emb(x)
        x = torch.cat([cls_toks, emb_mat], dim=1)

        for encoder in self.tranformer:
            x = encoder(x)
        out = x[:, 0, :]
        out = self.classifier(out)
        return out


def init_model():
    plt.rc('font', size=10)
    global net, loss_fn, optim
    net = skeleton_Transformer(50, cls_num).to(device)
    loss_fn = nn.CrossEntropyLoss()
    optim = Adam(net.parameters(), lr=0.0001)


def init_epoch():
    global epoch_cnt
    epoch_cnt = 0


def init_log():
    plt.rc('font', size=10)
    global log_stack, iter_log, tloss_log, tacc_log, vloss_log, vacc_log, time_log
    iter_log, tloss_log, tacc_log, vloss_log, vacc_log = [], [], [], [], []
    time_log, log_stack = [], []


def clear_memory():
    if device != 'cpu':
        empty_cache()
    gc.collect()


def epoch(data_loader, mode='train'):
    global epoch_cnt

    iter_loss, iter_acc, last_grad_performed = [], [], False

    for _data, _label in data_loader:
        data, label = _data.to(device), _label.type(torch.LongTensor).to(device)
        if mode == 'train':
            net.train()
        else:
            net.eval()

        result = net(data)
        _, out = torch.max(result, 1)

        loss = loss_fn(result, label)
        iter_loss.append(loss.item())

        if mode == 'train':
            optim.zero_grad()
            loss.backward()
            optim.step()
            last_grad_performed = True

        acc_partial = (out == label).float().sum()
        acc_partial = acc_partial / len(label)
        iter_acc.append(acc_partial.item())

    if last_grad_performed:
        epoch_cnt += 1

    clear_memory()

    return np.average(iter_loss), np.average(iter_acc)


def epoch_not_finished():
    return epoch_cnt < maximum_epoch


def record_train_log(_tloss, _tacc, _time):
    time_log.append(_time)
    tloss_log.append(_tloss)
    tacc_log.append(_tacc)
    iter_log.append(epoch_cnt)


def record_valid_log(_vloss, _vacc):
    vloss_log.append(_vloss)
    vacc_log.append(_vacc)


def last(log_list):
    if len(log_list) > 0:
        return log_list[len(log_list) - 1]
    else:
        return -1


def print_log():
    train_loss = round(float(last(tloss_log)), 3)
    train_acc = round(float(last(tacc_log)), 3)
    val_loss = round(float(last(vloss_log)), 3)
    val_acc = round(float(last(vacc_log)), 3)
    time_spent = round(float(last(time_log)), 3)

    log_str = 'Epoch: {:3} | T_Loss {:5} | T_acc {:5} | V_Loss {:5} | V_acc. {:5} | \
🕒 {:5}'.format(last(iter_log), train_loss, train_acc, val_loss, val_acc, time_spent)

    log_stack.append(log_str)
    hist_fig, loss_axis = plt.subplots(figsize=(10, 3), dpi=99)
    hist_fig.patch.set_facecolor('white')
    loss_t_line = plt.plot(iter_log, tloss_log, label='Train Loss', color='red', marker='o')
    loss_v_line = plt.plot(iter_log, vloss_log, label='Valid Loss', color='blue', marker='s')
    loss_axis.set_xlabel('epoch')
    loss_axis.set_ylabel('loss')
    acc_axis = loss_axis.twinx()
    acc_t_line = acc_axis.plot(iter_log, tacc_log, label='Train Acc.', color='red', marker='+')
    acc_v_line = acc_axis.plot(iter_log, vacc_log, label='Valid Acc.', color='blue', marker='x')
    acc_axis.set_ylabel('accuracy')
    hist_lines = loss_t_line + loss_v_line + acc_t_line + acc_v_line
    loss_axis.legend(hist_lines, [l.get_label() for l in hist_lines])
    loss_axis.grid()
    plt.title('Learning history until epoch {}'.format(last(iter_log)))
    plt.draw()
    clear_output(wait=True)
    plt.show()
    for idx in reversed(range(len(log_stack))):
        print(log_stack[idx])

init_model()
init_epoch()
init_log()
maximum_epoch = 1000

while epoch_not_finished():
    start_time = time.time()
    tloss, tacc = epoch(train_loader, mode='train')
    end_time = time.time()
    time_taken = end_time - start_time
    record_train_log(tloss, tacc, time_taken)
    with torch.no_grad():
        vloss, vacc = epoch(val_loader, mode='val')
        record_valid_log(vloss, vacc)
    print_log()

print('\n Training completed!')

with torch.no_grad():
    test_loss, test_acc = epoch(test_loader, mode = 'test')
    test_acc = round(test_acc, 4)
    test_loss = round(test_loss, 4)
    print('Test Acc.: {}'.format(test_acc))
    print('Test Loss: {}'.format(test_loss))

torch.save(net.state_dict(), 'model/homer_transformer.pt')
os.system('cp model/homer_transformer.pt /home/homer/model')

with redis.StrictRedis(connection_pool=redis_pool) as conn:
    conn.set('model_training', 'finish')



