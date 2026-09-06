import subprocess
import sys
import multiprocessing as mp
import datetime
import time
import redis
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QTextBrowser
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QIcon
from multiprocessing import Process, Queue


redis_pool = redis.ConnectionPool(host='', port=6379, db=0, max_connections=4, password='')


class Communicate(QObject):
    closeApp = pyqtSignal()


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon('sign.ico'))
        self.btn1 = QPushButton('수어 동영상 변환 및 데이터베이스 정보 입력', self)
        self.btn1.setEnabled(True)
        self.btn1.clicked.connect(self.mp4_convert)

        self.btn2 = QPushButton('수어 데이터베이스 정보 수정', self)
        self.btn2.setEnabled(True)
        self.btn2.clicked.connect(self.redis_input)

        self.btn3 = QPushButton('복합어 업데이트', self)
        self.btn3.setEnabled(True)
        self.btn3.clicked.connect(self.compound_update)

        self.btn4 = QPushButton('딥러닝 서버 학습', self)
        self.btn4.setEnabled(True)
        self.btn4.clicked.connect(self.deep_learning_train)

        self.btn5 = QPushButton('청각장애인용 통역기 업데이트', self)
        self.btn5.setEnabled(True)
        self.btn5.clicked.connect(self.model_download)

        self.tb = QTextBrowser()
        self.tb.setAcceptRichText(True)
        self.tb.setOpenExternalLinks(True)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.btn1)
        self.vbox.addWidget(self.btn2)
        self.vbox.addWidget(self.btn3)
        self.vbox.addWidget(self.btn4)
        self.vbox.addWidget(self.btn5)
        self.vbox.addWidget(self.tb)

        self.setLayout(self.vbox)
        self.setWindowTitle('수어 학습 프로그램')
        self.setGeometry(300, 300, 400, 300)
        self.show()

    def mp4_convert(self, e):
        self.p = Process(name="mp4_convert", target=go_mp4_convert, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('한국수어사전 사이트로부터 다운받은 단어 영상을 VR 출력 영상 및 딥러닝 학습 영상으로 변환해서 서버 및 기기로 전송하고, Redis에 라벨 정보들을 입력합니다.')

    def redis_input(self, e):
        self.p = Process(name="redis_input", target=go_redis_input, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('Redis에 입력된 라벨 정보들을 수정합니다.')

    def compound_update(self, e):
        self.p = Process(name="compound_update", target=go_compound_update, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('복합어를 수어에 맞는 단어의 나열로 업데이트합니다.')

    def deep_learning_train(self, e):
        with redis.StrictRedis(connection_pool=redis_pool) as conn:
            work = conn.get('server_work').decode('utf-8')
            state = conn.get('model_training').decode('utf-8')
        if work == 'on':
            if state == 'start':
                self.tb.clear()
                self.tb.append('학습이 진행중입니다.')
            elif state == 'finish':
                self.tb.clear()
                self.tb.append('학습이 완료되었습니다.')
                conn.set('model_training', 'stop')
            else:
                self.p = Process(name="deep_learning_train", target=go_deep_learning_train, args=(q,), daemon=True)
                self.p.start()
                self.tb.clear()
                self.tb.append('딥러닝 학습이 시작되었습니다.')
        else:
            self.tb.clear()
            self.tb.append('딥러닝 서버가 꺼져있습니다.')

    def model_download(self, e):
        self.p = Process(name="model_download", target=go_model_download, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('학습된 모델 파일을 청각장애인용 통역기로 업데이트합니다.')

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '프로그램 종료', 'Are you sure to quit?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def go_mp4_convert(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./mp4_convert.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


def go_redis_input(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./redis_input.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


def go_compound_update(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./compound_update.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


def go_deep_learning_train(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./deep_learning_train.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


def go_model_download(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./model_download.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


if __name__ == '__main__':
    q = Queue()
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
