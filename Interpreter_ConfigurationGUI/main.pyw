import subprocess
import sys
import multiprocessing as mp
import datetime
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QTextBrowser
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QIcon
from multiprocessing import Process, Queue


class Communicate(QObject):
    closeApp = pyqtSignal()


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon('interpreter.ico'))
        self.btn1 = QPushButton('통역기 WiFi 접속', self)
        self.btn1.setEnabled(True)
        self.btn1.clicked.connect(self.wifi_connect)

        self.btn2 = QPushButton('통역기 기기 변경', self)
        self.btn2.setEnabled(True)
        self.btn2.clicked.connect(self.interpreter_change)

        self.btn3 = QPushButton('시각장애인용 통역기 Volume 변경', self)
        self.btn3.setEnabled(True)
        self.btn3.clicked.connect(self.interpreter_volume_setting)

        self.btn4 = QPushButton('시각장애인용 통역기 언어 설정', self)
        self.btn4.setEnabled(True)
        self.btn4.clicked.connect(self.interpreter_language_change)

        self.btn5 = QPushButton('API Key 설정', self)
        self.btn5.setEnabled(True)
        self.btn5.clicked.connect(self.api_key_setting)

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
        self.setWindowTitle('통역기 설정 프로그램')
        self.setGeometry(300, 300, 400, 300)
        self.show()

    def wifi_connect(self, e):
        self.p = Process(name="WiFi_Connect", target=go_wifi_connect, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('통역기의 네트워크를 동기화합니다.')

    def interpreter_change(self, e):
        self.p = Process(name="Interpreter_Change", target=go_interpreter_change, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('시각장애인용과 청각장애인용 중에서 사용할 통역기의 용도를 설정합니다.')

    def interpreter_volume_setting(self, e):
        self.p = Process(name="Interpreter_Volume_Setting", target=go_interpreter_volume_setting, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('장소에 맞게 통역기의 마이크 음량을 조정합니다.')

    def interpreter_language_change(self, e):
        self.p = Process(name="Interpreter_Language_Change", target=go_interpreter_language_change, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('통역기에 사용할 언어를 설정합니다.')

    def api_key_setting(self, e):
        self.p = Process(name="API_Key_Setting", target=go_api_key_setting, args=(q,), daemon=True)
        self.p.start()
        self.tb.clear()
        self.tb.append('통역기에 사용할 OpenAI API의 키 값을 설정합니다.')

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '프로그램 종료', 'Are you sure to quit?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def go_wifi_connect(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./interpreter_wifi_connect.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


def go_interpreter_change(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./interpreter_change.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


def go_interpreter_volume_setting(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./interpreter_volume_setting.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


def go_interpreter_language_change(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./interpreter_language_change.exe')

    while True:
        now = datetime.datetime.now()
        data = str(now)
        q.put(data)
        time.sleep(1)


def go_api_key_setting(q):
    proc = mp.current_process()
    print(proc.name)
    subprocess.run('./api_key_setting.exe')

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
