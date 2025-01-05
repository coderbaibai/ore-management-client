from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 添加模块所在目录到 sys.path

from LeftNavi.LeftNavi import LeftNavi
from RightWidget.RightWidget import RightWidget

class ClientMainWindow(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet('''QWidget{background-color:rgb(200, 200, 100);}''')

        self.navi = LeftNavi(self)
        self.mainWindow = RightWidget(self)

        layout = QHBoxLayout()
        layout.addWidget(self.navi)  # 添加子组件
        layout.addWidget(self.mainWindow)  # 添加子组件

        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        layout.setSpacing(0)  # 移除间距
        self.setLayout(layout)


        