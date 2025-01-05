from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor

class RightWidget(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet('''QWidget{background-color:rgb(100, 200, 100);}''')