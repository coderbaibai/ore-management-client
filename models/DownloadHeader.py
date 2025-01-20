from uuid import uuid1
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BreadcrumbBar, CommandBar, setFont, SearchLineEdit, BodyLabel,
                            Action, PrimaryPushButton, ToolButton,CommandBarView,PushButton,StrongBodyLabel)
from qfluentwidgets import FluentIcon as FIF
import collections

from utils.S3Utils import *

class FilesWidgetHeader(QWidget):

    update_signal = pyqtSignal(list)

    copy_signal = pyqtSignal(str,str)
    move_signal = pyqtSignal(str,str)
    paste_signal = pyqtSignal(str,str)
    delete_signal = pyqtSignal(str,str)

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(100)
        self.vLayout = QVBoxLayout(self)

        # 设置顶部
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(2)

        # 设置底部
        self.bottomLayout = QHBoxLayout()
        self.title = StrongBodyLabel("传输完成",self)
        self.labelTotal = BodyLabel("已加载x个",self)
        self.bottomLayout.addWidget(self.labelTotal,alignment=(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter))
        # 设置整体
        self.vLayout.addLayout(self.topLayout)
        self.vLayout.addLayout(self.bottomLayout)
        self.setLayout(self.vLayout)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(220,220,220))
        self.setPalette(palette)
        self.setAutoFillBackground(True)  # 启用背景填充
