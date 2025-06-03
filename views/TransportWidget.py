from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (InfoBar, InfoBarPosition, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont,FluentLabelBase)
from qfluentwidgets import FluentIcon as FIF

from views.TransportHeader import TransportHeader
from views.TransportTable import TransportTable

from OreUtils.S3Utils import s3Utils
from OreUtils.SqliteUtils import *

class TransportWidget(SubtitleLabel):
    def __init__(self,text:str,parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.vLayout = QVBoxLayout(self)
        self.header = TransportHeader(self)
        self.scrollTable = QScrollArea()
        self.scrollTable.setWidgetResizable(True)
        self.scrollTable.setStyleSheet("background-color: #F7F9FC;")
        self.table = TransportTable()

        self.scrollTable.setWidget(self.table)

        self.vLayout.setContentsMargins(0,0,0,0)
        self.vLayout.setSpacing(0)
        self.vLayout.addWidget(self.header)
        self.vLayout.addWidget(self.scrollTable)
        self.setLayout(self.vLayout)
        
        self.table.show_signal.connect(self.handle_show_signal)
        self.table.number_signal.connect(self.handle_number_signal)
        self.header.delete_signal.connect(self.handle_delete_signal)
        self.header.update_signal.connect(self.handle_update_signal)

        self.table.update()

    def handle_jump_signal(self, data):
        # 处理子组件传递的列表参数
        self.header.addItemAndJump(data)


    def handle_show_signal(self, data):
        # 处理子组件传递的列表参数
        self.header.changeBtnState(data)

    def handle_delete_signal(self):
        ids = self.table.getTargets()
        if len(ids) == 0:
            TransportRecord.delete().execute()
        for id in ids:
            TransportRecord.delete_by_id(id)
        InfoBar.success(
            title='删除成功',
            content="",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self.window()
        ).show()
        self.table.update()

    def handle_update_signal(self):
        self.table.update()

    def handle_number_signal(self,data):
        self.header.setNumber(data)