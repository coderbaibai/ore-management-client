from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加模块所在目录到 sys.path
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidget import FilesWidget
from models.TransportWidget import TransportWidget

import tkinter as tk
from tkinter import filedialog

# 创建一个 Tkinter 根窗口（不显示窗口）


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))



class Window(FluentWindow):

    def __init__(self):
        super().__init__()

        # create sub interface
        self.homeInterface = FilesWidget('Home Interface', self)
        self.transportInterface = TransportWidget('Transport Interface',self)
        self.downloadInterface = Widget('Download Interface',self)
        self.uploadInterface = Widget('Upload Interface',self)
        self.videoInterface = Widget('Video Interface', self)
        self.libraryInterface = Widget('library Interface', self)
        self.settingInterface = Widget('settings Interface', self)
        self.navigationInterface.setExpandWidth(170)
        self.navigationInterface.setCollapsible(False)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.FOLDER, '文件')
        self.addSubInterface(self.transportInterface, FIF.SAVE_COPY, '传输')
        self.addSubInterface(self.downloadInterface, FIF.DOWN, '正在下载',parent=self.transportInterface)
        self.addSubInterface(self.uploadInterface, FIF.UP, '正在上传',parent=self.transportInterface)
        self.addSubInterface(self.videoInterface, FIF.BOOK_SHELF, '处理')
        self.addSubInterface(self.libraryInterface, FIF.PEOPLE, '管理', position= NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', position= NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.resize(1050, 700)
        self.setMinimumSize(1050, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('大数据矿石治理系统')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
