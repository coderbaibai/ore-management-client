from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (InfoBar, InfoBarPosition, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont,FluentLabelBase)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidgetHeader import FilesWidgetHeader
from models.FilesTable import FilesTable

from utils.S3Utils import s3Utils

class FilesWidget(SubtitleLabel):
    def __init__(self,text:str,parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.vLayout = QVBoxLayout(self)
        self.header = FilesWidgetHeader(self)
        self.table = FilesTable(self)

        self.vLayout.setContentsMargins(0,0,0,0)
        self.vLayout.setSpacing(0)
        self.vLayout.addWidget(self.header)
        self.vLayout.addWidget(self.table)
        self.setLayout(self.vLayout)

        self.sourceKey = []
        self.sourcePath = ''
        self.sourceBucket = ''

        self.isCopy = False
        
        self.table.jump_signal.connect(self.handle_jump_signal)
        self.table.show_signal.connect(self.handle_show_signal)
        self.header.update_signal.connect(self.handle_update_signal)
        self.header.copy_signal.connect(self.handle_copy_signal)
        self.header.move_signal.connect(self.handle_move_signal)
        self.header.paste_signal.connect(self.handle_paste_signal)
        self.header.delete_signal.connect(self.handle_delete_signal)

        self.table.update(['全部文件'])