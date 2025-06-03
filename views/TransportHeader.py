from uuid import uuid1
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BreadcrumbBar, CommandBar, setFont, ToolButton, BodyLabel,
                            Action, PrimaryPushButton, InfoBar,InfoBarPosition,PushButton,StrongBodyLabel)
from qfluentwidgets import FluentIcon as FIF
import collections

from OreUtils.S3Utils import *
from OreUtils.SqliteUtils import *

class TransportHeader(QWidget):

    delete_signal = pyqtSignal()
    update_signal = pyqtSignal()

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(100)
        self.vLayout = QVBoxLayout(self)

        # 设置顶部
        self.topLayout = QHBoxLayout()
        self.topLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.topLayout.setSpacing(2)
        self.delete_btn = PushButton(FIF.DELETE,'清空所有记录',self)
        self.delete_btn.clicked.connect(self.handleDelete)
        self.isAllDelete = True
        self.topLayout.addWidget(self.delete_btn)

        # 设置底部
        self.bottomLayout = QHBoxLayout()
        self.title = StrongBodyLabel("传输完成",self)
        self.labelTotal = BodyLabel("已加载x条记录",self)
        self.updateBtn = ToolButton(FIF.UPDATE)
        self.bottomLayout.addWidget(self.title)
        self.bottomLayout.addStretch()
        self.bottomLayout.addWidget(self.labelTotal)
        self.bottomLayout.addWidget(self.updateBtn)
        self.updateBtn.clicked.connect(self.handleUpdate)
        # 设置整体
        self.vLayout.addLayout(self.topLayout)
        self.vLayout.addLayout(self.bottomLayout)
        self.setLayout(self.vLayout)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(220,220,220))
        self.setPalette(palette)
        self.setAutoFillBackground(True)  # 启用背景填充

    def changeBtnState(self,data):
        if data:
            self.delete_btn.setText('清除记录')
            self.isAllDelete = False
        else:
            self.delete_btn.setText('清空所有记录')
            self.isAllDelete = True

    def handleDelete(self):
        self.delete_signal.emit()
        self.changeBtnState(False)

    def handleUpdate(self):
        self.update_signal.emit()

    def setNumber(self,data):
        self.labelTotal.setText(f'已加载{data}条记录')
            