import asyncio
from threading import Thread
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qasync import asyncSlot
from qfluentwidgets import (InfoBar, InfoBarPosition, SingleDirectionScrollArea, ComboBox, FluentWindow,
                            MessageBoxBase, LineEdit, SubtitleLabel, setFont,FluentLabelBase)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidgetHeader import FilesWidgetHeader
from models.FilesTable import FilesTable
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager,QNetworkReply

from utils.S3Utils import s3Utils
from config.GConfig import gConfig,cookieJar
from functools import partial
import json


class SelectMarketDialog(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent):
        super().__init__(parent)

        self.viewLayout.setContentsMargins(10,10,10,10)
        self.viewLayout.setSpacing(0)
        
        self.titleLabel = SubtitleLabel('选择数据市场')

        self.market = ""
        self.marketId = None
        self.comboBox = ComboBox()
        self.comboBox.currentIndexChanged.connect(self.update_target_market)
    
        self.items = []
        self.ids = []

        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.comboBox)

        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(350)

    def update_target_market(self, index):
        self.market = self.comboBox.currentText()
        self.marketId = self.ids[index]

class FilesWidget(SubtitleLabel):

    upload_signal = pyqtSignal(str,str,str)
    download_signal = pyqtSignal(str,list)

    def __init__(self,text:str,parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.vLayout = QVBoxLayout(self)
        self.setLayout(self.vLayout)
        self.header = FilesWidgetHeader(self)

        self.scrollTable = QScrollArea()
        self.scrollTable.setWidgetResizable(True)
        self.scrollTable.setStyleSheet("background-color: #F7F9FC;")
        self.table = FilesTable()

        self.scrollTable.setWidget(self.table)

        self.vLayout.setContentsMargins(0,0,0,0)
        self.vLayout.setSpacing(0)
        self.vLayout.addWidget(self.header)
        self.vLayout.addWidget(self.scrollTable)

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
        self.header.market_items_add_signal.connect(self.handle_market_items_add_signal)

        self.header.upload_signal.connect(self.handle_upload_signal)
        self.header.download_signal.connect(self.handle_download_signal)
        self.header.search_signal.connect(self.handle_search_signal)
        self.table.number_signal.connect(self.handle_number_signal)
        self.table.rename_signal.connect(self.handle_rename_signal)

        self.table.update(['全部文件'])

        self.dialog = None
        self.manager = QNetworkAccessManager()
        self.manager.setCookieJar(cookieJar)

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
    
    def handle_market_items_add_signal(self,bucket,path):
        self.dialog = SelectMarketDialog(self.window())
        url = QUrl(gConfig['server']['spring']['url']+'/market/current')
        request = QNetworkRequest(url)
        handler = partial(self.handle_get_markets_respose,bucket=bucket,path=path)
        self.manager.finished.connect(handler)
        self.manager.get(request)

    def handle_get_markets_respose(self,reply:QNetworkReply,bucket:str,path:str):
        self.manager.finished.disconnect()
        res = json.loads(reply.readAll().data().decode())
        if 'code' not in res:
            print(f"❗ Error Code: {res['status']}\n")
            print(f"❗ Error msg: {res['error']}")
            return
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            self.dialog.items = [dic['name'] for dic in res['data']['markets']]
            self.dialog.ids = [dic['id'] for dic in res['data']['markets']]
            self.dialog.comboBox.addItems(self.dialog.items)
            if self.dialog.exec_():
                self.add_market_items(self.dialog.marketId,bucket,path)
        reply.deleteLater()
    
    def add_market_items(self,marketId:str,bucket:str,path:str):
        targets = self.table.getTargetsWithSize()
        # "marketId": 1,
        # "name": "长语汐",
        # "bucketName": "颜敏",
        # "path": "laboru",
        # "available": 1
        items = []
        for (target,targetSize) in targets:
            item = {}
            item['marketId'] = marketId
            item['name'] = bucket+':'+path+target
            item['bucketName'] = bucket
            item['path'] = path+target
            item['available'] = 1
            item['size'] = targetSize
            items.append(item)
        data_to_post = {}
        data_to_post['marketItems'] = items
        # 转换为JSON字符串并编码为字节
        json_data = json.dumps(data_to_post).encode('utf-8')

        url = QUrl(gConfig['server']['spring']['url']+'/market/items/add')
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        # 发送 POST 请求
        self.manager.finished.connect(self.handle_add_items_respose)
        self.manager.post(request, json_data)

    def handle_add_items_respose(self,reply:QNetworkReply):
        self.manager.finished.disconnect()
        res = json.loads(reply.readAll().data().decode())
        if 'code' not in res:
            print(f"❗ Error Code: {res['status']}\n")
            print(f"❗ Error msg: {res['error']}")
            return
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            InfoBar.success(
                title='添加成功',
                content="",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1000,
                parent=self.window()
            ).show()
        reply.deleteLater()

