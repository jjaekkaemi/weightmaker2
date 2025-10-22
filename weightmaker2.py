import sys
import random
import time
import threading
import serial

from PyQt5.QtWidgets import (
    QWidget, QApplication, QLabel, QLineEdit, QPushButton,
    QBoxLayout, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSlot, pyqtSignal

# ===== 설정값 =====
MIN_TARGET = 2000
MAX_TARGET = 10000    # 요청: 2000~10000
STEP_MIN = 300
STEP_MAX = 500
# ==================

class firstthread(threading.Thread):
    def __init__(self, name):
        super().__init__()
        self.name = name
    def run(self):
        global weight, se, status
        while status != 0:
            try:
                se.write(bytes(status + ',NT,+' + str(weight).zfill(5) + '.0kg', 'utf-8'))
            except Exception:
                pass
            time.sleep(0.2)

class SerialThread(QThread):
    change_data_signal = pyqtSignal(str)
    def run(self):
        global weight, status
        while status != 0:
            text = status + ',NT,+' + str(weight).zfill(5) + '.0kg'
            self.change_data_signal.emit(text)
            time.sleep(0.1)

class Thread1(QThread):
    # 목표값을 UI에 알려주기 위한 신호
    target_set = pyqtSignal(int)

    def run(self):
        global weight, status, flag
        flag = 3
        target = random.randint(MIN_TARGET, MAX_TARGET)  # 목표값 난수
        self.target_set.emit(target)

        while weight < target:
            if flag != 3:
                return
            status = 'US'
            step = random.randint(STEP_MIN, STEP_MAX)
            weight = min(weight + step, target)  # 목표 초과 방지
            time.sleep(0.2)

        time.sleep(1)
        status = 'ST'

class Thread2(QThread):
    def run(self):
        global weight, status, flag
        flag = 1
        while weight > 0:
            if flag != 1:
                return
            status = 'US'
            step = random.randint(STEP_MIN, STEP_MAX)
            weight = max(weight - step, 0)       # 0 미만 방지
            time.sleep(0.2)
        time.sleep(1)
        status = 'ST'

class SecondWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(560, 220)

        # 표시 라벨
        self.weightlabel = QLabel("SN, NT, +0000.0 kg", self)
        self.weightlabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.targetlabel = QLabel("Target: -", self)
        self.targetlabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 버튼
        self.pb_up = QPushButton("up", self)
        self.pb_down = QPushButton("down", self)
        self.pb_stop = QPushButton("stop", self)

        # 레이아웃 구성
        top_box = QVBoxLayout()
        top_box.addWidget(self.weightlabel)
        top_box.addWidget(self.targetlabel)

        btn_box = QHBoxLayout()
        btn_box.addWidget(self.pb_up)
        btn_box.addWidget(self.pb_down)
        btn_box.addWidget(self.pb_stop)

        root = QVBoxLayout(self)
        root.addLayout(top_box)
        root.addLayout(btn_box)

        # 시리얼 송신 쓰레드
        self.serialThread = SerialThread()
        self.serialThread.change_data_signal.connect(self.update_data)
        self.serialThread.start()

        # 버튼 이벤트
        self.pb_up.clicked.connect(self.handle_up)
        self.pb_down.clicked.connect(self.handle_down)
        self.pb_stop.clicked.connect(self.handle_stop)

        # 현재 동작 쓰레드 핸들
        self.upthread = None
        self.downthread = None

    def _cleanup_threads(self):
        global flag, status
        flag = 0
        status = 'ST'
        self.upthread = None
        self.downthread = None

    def handle_up(self):
        # 동시 실행 방지
        self._cleanup_threads()
        # 새 up 쓰레드 생성
        self.upthread = Thread1()
        self.upthread.target_set.connect(self._on_target_set)
        self.upthread.start()

    def handle_down(self):
        # 동시 실행 방지
        self._cleanup_threads()
        # 새 down 쓰레드 생성
        self.downthread = Thread2()
        self.downthread.start()

    def handle_stop(self):
        # 즉시 정지
        self._cleanup_threads()
        self.targetlabel.setText("Target: -")

    @pyqtSlot(int)
    def _on_target_set(self, target):
        self.targetlabel.setText(f"Target: {target}")

    @pyqtSlot(str)
    def update_data(self, str_data):
        global se
        try:
            if se:
                se.write(bytes(str_data + '\r\n', 'utf-8'))
        except Exception:
            pass
        self.weightlabel.setText(str_data)

class Form(QWidget):
    """
    테스트용도의 단독 실행때만 사용하는 폼
    """
    def __init__(self):
        QWidget.__init__(self, flags=Qt.Widget)
        self.pb = QPushButton("Connect")
        self.cb_port = QLineEdit("/dev/ttyUSB0")
        self.cb_baud_rate = QLineEdit("9600")
        self.init_widget()

    def init_widget(self):
        self.setWindowTitle("Tester")
        form_lbx = QBoxLayout(QBoxLayout.TopToBottom, parent=self)
        self.setLayout(form_lbx)

        self.pb.clicked.connect(self.connect)

        form_lbx.addWidget(QLabel('COM PORT'))
        form_lbx.addWidget(self.cb_port)
        form_lbx.addWidget(QLabel('COM baud rate'))
        form_lbx.addWidget(self.cb_baud_rate)
        form_lbx.addWidget(self.pb)

    def connect(self):
        global se, status
        self.w = SecondWindow()
        time.sleep(1)
        try:
            se = serial.Serial(self.cb_port.text(), self.cb_baud_rate.text())
        except Exception:
            se = None  # 시리얼 미연결 상태에서도 UI 동작하도록
        status = 'ST'
        self.w.show()

    def closeEvent(self, e):
        global status
        status = 0

# 전역 상태
weight = 0
status = 'ST'
flag = 0
se = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    excepthook = sys.excepthook
    sys.excepthook = lambda t, val, tb: excepthook(t, val, tb)
    form = Form()
    form.show()
    sys.exit(app.exec_())
