import sys
import random
import time
import threading
import serial

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSlot, pyqtSignal

# ===== 새로 추가한 설정값 =====
MIN_TARGET = 2000
MAX_TARGET = 60000
STEP_MIN = 300
STEP_MAX = 500
# ===========================

class firstthread(threading.Thread):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def run(self):
        global weight, se, status
        while status != 0:
            se.write(bytes(status + ',NT,+' + str(weight).zfill(5) + '.0kg', 'utf-8'))
            print(weight)
            print(self.name)
            print(type(self.name))
            self.name.setText('asd')
            time.sleep(0.2)


class SerialThread(QThread):
    change_data_signal = pyqtSignal(str)
    def run(self):
        global weight, status
        print('qthread')
        while 1 and status != 0:
            text = status + ',NT,+' + str(weight).zfill(5)+'.0kg'
            self.change_data_signal.emit(text)
            time.sleep(0.1)


class Thread1(QThread):
    """
    UP: 목표를 [MIN_TARGET, MAX_TARGET] 사이 난수로 정하고
         STEP_MIN~STEP_MAX 사이 난수만큼 증가.
         목표에 도달하면 멈추고 ST로 전환.
    """
    def run(self):
        global weight, status, flag
        flag = 3
        target = random.randint(MIN_TARGET, MAX_TARGET)  # 목표값 난수
        while weight < target:
            if flag != 3:
                return
            status = 'US'
            step = random.randint(STEP_MIN, STEP_MAX)     # 증가 폭 난수
            weight = min(weight + step, target)           # 목표 초과 방지 (클램프)
            time.sleep(0.2)

        time.sleep(1)
        status = 'ST'


class Thread2(QThread):
    """
    DOWN: 0까지 STEP_MIN~STEP_MAX 사이 난수만큼 감소.
          0이 되면 멈추고 ST로 전환.
    """
    def run(self):
        global weight, status, flag
        flag = 1
        while weight > 0:
            if flag != 1:
                return
            status = 'US'
            step = random.randint(STEP_MIN, STEP_MAX)     # 감소 폭 난수
            weight = max(weight - step, 0)                # 0 미만 방지 (클램프)
            time.sleep(0.2)
        time.sleep(1)
        status = 'ST'


class SecondWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.weightlabel = QLabel("SN, NT, +0000.0 kg", self)
        self.weightlabel.move(200, 0)
        self.resize(500, 275)
        self.pb_up = QPushButton("up", self)
        self.pb_up.move(0, 20)
        self.pb_up.resize(250, 250)
        self.pb_down = QPushButton("down", self)
        self.pb_down.move(250, 20)
        self.pb_down.resize(250, 250)

        self.upthread = Thread1()
        self.downthread = Thread2()
        self.pb_up.clicked.connect(lambda: self.upthread.start())
        self.pb_down.clicked.connect(lambda: self.downthread.start())
        self.serialThread = SerialThread()
        self.serialThread.change_data_signal.connect(self.update_data)
        self.serialThread.start()

    @pyqtSlot(str)
    def update_data(self, str_data):
        global se
        print(str_data)
        se.write(bytes(str_data + '\r\n', 'utf-8'))
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
        global se
        self.w = SecondWindow()
        time.sleep(1)
        se = serial.Serial(self.cb_port.text(), self.cb_baud_rate.text())
        self.w.show()

    def closeEvent(self, e):
        global status
        status = 0


weight = 0
status = 'ST'
flag = 0


if __name__ == "__main__":
    from PyQt5.QtWidgets import QPushButton
    from PyQt5.QtWidgets import QTextEdit

    app = QApplication(sys.argv)
    excepthook = sys.excepthook
    sys.excepthook = lambda t, val, tb: excepthook(t, val, tb)
    form = Form()
    form.show()
    sys.exit(app.exec_())