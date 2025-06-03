from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (InfoBar, PrimaryPushButton, setTheme, Theme, FluentWindow,
                            GroupHeaderCardWidget, InfoBarPosition, SubtitleLabel, setFont,FluentLabelBase)
from qfluentwidgets import FluentIcon as FIF

from views.TransportHeader import TransportHeader
from views.TransportTable import TransportTable

from OreUtils.S3Utils import s3Utils
from OreUtils.SqliteUtils import *

class SettingCard(GroupHeaderCardWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setTitle("基本设置")
        self.setBorderRadius(8)
        self.res = list(UploaderItem.select())
        self.clearBtn = PrimaryPushButton('清理',self)
        self.clearBtn.clicked.connect(self.clearBuffer)
        self.clearGroup = self.addGroup(FIF.DELETE,'清理缓存',f'共有{len(self.res)}条记录',self.clearBtn)
    
    def clearBuffer(self):
        UploaderItem.delete().execute()
        InfoBar.success(
            title='已清理缓存',
            content="",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self.window()
        ).show()
        self.res = list(UploaderItem.select())
        self.clearGroup.setContent(f'共有{len(self.res)}条记录')

class SettingWidget(SubtitleLabel):
    def __init__(self,text:str,parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.__setting_layout = QVBoxLayout()
        self.__setting_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__setting_card = SettingCard(self)
        self.__setting_layout.addWidget(self.__setting_card)
        self.setLayout(self.__setting_layout)