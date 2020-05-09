import sys
import requests
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from get_params import get_params
from PyQt5.QtWidgets import *


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('шкура.ui', self)
        self.map_api_server = "http://static-maps.yandex.ru/1.x/"
        self.pushButton.clicked.connect(self.click)

    def click(self):
        spn = self.lineEdit.text() + ',' + self.lineEdit_2.text()
        coords = self.lineEdit_3.text() + ',' + self.lineEdit_4.text()
        self.final(get_params(coords, spn))

    def final(self, params):
        f = open('file.png', 'wb')
        f.write(requests.get(self.map_api_server, params=params).content)
        self.label.setPixmap(QPixmap('file.png').scaled(self.label.size()))


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.exit(app.exec())
