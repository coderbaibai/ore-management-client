from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
import sys
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont,FluentWindow)
from qfluentwidgets import FluentIcon as FIF

class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        # 必须给子界面设置全局唯一的对象名
        self.setObjectName(text.replace(' ', '-'))

class TransportWidget(FluentWindow):

    def __init__(self,text:str,parent=None):
        super().__init__(parent=parent)

        self.uploadingInterface = Widget('Uploading Interface', self)
        self.downloadingInterface = Widget('Downloading Interface', self)
        self.finishInterface = Widget('Finish Interface', self)

        self.addSubInterface(self.uploadingInterface, FIF.HOME, '正在上传')
        self.addSubInterface(self.downloadingInterface, FIF.MUSIC, '正在下载')
        self.addSubInterface(self.finishInterface, FIF.VIDEO, '传输完成')

        self.setObjectName(text.replace(' ', '-'))
