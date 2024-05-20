from json import dumps, loads
from socket import socket
from socket import SHUT_WR

from PySide6.QtCore import QTimer
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont
from PySide6.QtGui import QTextCharFormat
from PySide6.QtGui import QTextCursor
from PySide6.QtGui import QTextTable
from PySide6.QtGui import QTextTableFormat
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLayout
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QScrollBar
from PySide6.QtWidgets import QTextEdit
from PySide6.QtWidgets import QWidget


HOST = '192.168.47.49'
PORT = 2077


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.text_field = QTextEdit()
        self.text_field.setFixedSize(400, 600)
        self.text_field.setReadOnly(True)

        self.nickname = QLineEdit()
        self.nickname.setPlaceholderText('Nickname')
        self.nickname.setMinimumWidth(100);

        self.start_stop = QPushButton('Start')
        self.start_stop.clicked.connect(self.activate)

        self.message = QLineEdit()
        self.message.setPlaceholderText('Enter a message...')
        self.message.setMinimumWidth(300)
        self.message.setReadOnly(True)

        self.send = QPushButton('Send')
        self.send.setDisabled(True)
        self.send.clicked.connect(self.send_message)

        layout = QGridLayout()
        layout.addWidget(self.text_field, 0, 0, 6, 4)
        layout.addWidget(self.nickname, 0, 4)
        layout.addWidget(self.start_stop, 1, 4)
        layout.addWidget(self.message, 6, 0, 1, 3)
        layout.addWidget(self.send, 6, 3, )
        layout.setSizeConstraint(QLayout.SetFixedSize)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        # self.timer.connect(self.ping)
        self.timer.timeout.connect(self.ping)

        self.last = 0

    @Slot()
    def activate(self):
        if len(self.nickname.text()) == 0:
            return
        self.nickname.setReadOnly(True)
        self.message.setReadOnly(False)
        self.send.setDisabled(False)
        self.start_stop.setText('Stop')
        self.start_stop.clicked.disconnect(self.activate)
        self.start_stop.clicked.connect(self.deactivate)
        self.timer.start()

    @Slot()
    def deactivate(self):
        self.nickname.setReadOnly(False)
        self.message.setReadOnly(True)
        self.send.setDisabled(True)
        self.start_stop.setText('Start')
        self.start_stop.clicked.disconnect(self.deactivate)
        self.start_stop.clicked.connect(self.activate)
        self.timer.stop()

    def write_message(self, nick, text):
        table_format = QTextTableFormat()
        table_format.setBorder(0)
        text_format = QTextCharFormat()

        cursor = self.text_field.textCursor()
        cursor.movePosition(QTextCursor.End)
        table = cursor.insertTable(1, 2, table_format)

        text_format.setFont(QFont('default', 11, QFont.DemiBold))
        table.cellAt(0, 0).setFormat(text_format)
        table.cellAt(0, 0).firstCursorPosition().insertText(f'{nick}:')

        text_format.setFont(QFont('default', 11))
        table.cellAt(0, 1).setFormat(text_format)
        table.cellAt(0, 1).firstCursorPosition().insertText(text)

        bar = self.text_field.verticalScrollBar()
        bar.setValue(bar.maximum())

    @Slot()
    def send_message(self):
        s = socket()
        s.connect((HOST, PORT))
        s.sendall(dumps({
            'action': 'post',
            'nick': self.nickname.text(),
            'text': self.message.text() 
        }).encode())
        self.message.clear()
        s.shutdown(SHUT_WR)
        res = bytearray()
        buf = s.recv(1024)
        while len(buf) != 0:
            res += buf
            buf = s.recv(1024)
        s.close()
        response = loads(res.decode())

    @Slot()
    def ping(self):
        s = socket()
        s.connect((HOST, PORT))
        s.sendall(dumps({
            'action': 'get',
            'last': self.last
        }).encode())
        s.shutdown(SHUT_WR)
        res = bytearray()
        buf = s.recv(1024)
        while len(buf) != 0:
            res += buf
            buf = s.recv(1024)
        s.close()
        response = loads(res.decode())
        messages = response['messages']
        if len(messages) != 0:
            self.last = messages[-1]['n']
        for m in response['messages']:
            self.write_message(m['who'], m['text'])


if __name__ == '__main__':
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()
