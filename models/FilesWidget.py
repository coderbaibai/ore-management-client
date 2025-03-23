import asyncio
from threading import Thread
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qasync import asyncSlot
from qfluentwidgets import (InfoBar, InfoBarPosition, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont,FluentLabelBase)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidgetHeader import FilesWidgetHeader
from models.FilesTable import FilesTable

from utils.S3Utils import s3Utils

class FilesWidget(SubtitleLabel):

    upload_signal = pyqtSignal(str,str,str)
    download_signal = pyqtSignal(str,list)

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

        self.header.upload_signal.connect(self.handle_upload_signal)
        self.header.download_signal.connect(self.handle_download_signal)
        self.header.search_signal.connect(self.handle_search_signal)
        self.table.number_signal.connect(self.handle_number_signal)
        self.table.rename_signal.connect(self.handle_rename_signal)

        self.table.update(['全部文件'])

    def handle_jump_signal(self, data):
        # 处理子组件传递的列表参数
        self.header.addItemAndJump(data)

    async def rename_process(self,old_name,new_name):
        bucket,path = self.header.getBucketAndCurrentPath()
        isSuccess,msg = await s3Utils.rename(bucket,path+old_name,path+new_name)
        self.table.update(self.header.currentPath)
        if isSuccess:
            InfoBar.success(
                title='重命名成功',
                content=msg,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            ).show()
        else:
            InfoBar.error(
                title='重命名失败',
                content=msg,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            ).show()
    @asyncSlot(str,str)
    async def handle_rename_signal(self, old_name,new_name):
        await self.rename_process(old_name,new_name)

    def handle_update_signal(self, data):
        # 处理子组件传递的列表参数
        self.table.update(data)

    def handle_show_signal(self, data):
        # 处理子组件传递的列表参数
        self.header.changeBarState(data)

    def handle_copy_signal(self,bucket,data):
        # 处理子组件传递的列表参数
        self.sourcePath = data
        self.sourceBucket = bucket
        self.sourceKey = self.table.getTargets()
        self.isCopy = True
        InfoBar.success(
            title='已复制',
            content="请在目标文件夹下粘贴",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        ).show()

    def handle_move_signal(self,bucket,data):
        # 处理子组件传递的列表参数
        self.sourcePath = data
        self.sourceBucket = bucket
        self.sourceKey = self.table.getTargets()
        self.isCopy = False
        InfoBar.success(
            title='已剪切',
            content="请在目标文件夹下粘贴",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        ).show()

    def handle_paste_signal(self,bucket,path):
        InfoBar.info(
            title='正在粘贴',
            content="",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        ).show()
        QApplication.processEvents()
        isSuccess = True
        for key in self.sourceKey:
            # 如果重名
            if self.table.findFileName(key):
                isSuccess = False
                InfoBar.error(
                    title='粘贴失败',
                    content=f"文件名重复：{key}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=10000,
                    parent=self
                ).show()
                continue
            # 如果不重名
            if self.isCopy:
                s3Utils.copyFile(
                    self.sourceBucket,
                    self.sourcePath+key,
                    bucket,
                    path+key
                )
            else:
                s3Utils.cutFile(
                    self.sourceBucket,
                    self.sourcePath+key,
                    bucket,
                    path+key
                )
        self.table.update(self.header.currentPath)
        if isSuccess:
            InfoBar.success(
                title='粘贴成功',
                content='',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            ).show()
        else:
            InfoBar.warning(
                title='部分文件无法粘贴',
                content='',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            ).show()

    def handle_delete_signal(self,bucket,path):
        targets = self.table.getTargets()
        InfoBar.info(
            title='正在删除',
            content="",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        ).show()
        for key in targets:
            s3Utils.deleteFile(bucket,path+key)
        self.table.update(self.header.currentPath)
        InfoBar.success(
            title='删除成功',
            content="",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        ).show()
    
    def handle_upload_signal(self,bucket,path,local):
        self.upload_signal.emit(bucket,path,local)
    
    def handle_download_signal(self,bucket,local,path):
        targets = self.table.getTargets()
        targets = [{'local':local+s,'cloud':path+s} for s in targets]
        self.download_signal.emit(bucket,targets)
        
    def handle_number_signal(self,data):
        self.header.setNumber(data)

    def handle_search_signal(self,bucket,key):
        self.table.search_update(bucket,key)


