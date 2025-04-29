import asyncio
from functools import partial
import json
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
import sys
import os
from config.GConfig import gConfig,cookieJar
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager,QNetworkReply

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加模块所在目录到 sys.path
from qfluentwidgets import (NavigationItemPosition, InfoBar, InfoBarPosition, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidget import FilesWidget
from models.MarketsWidget import MarketWidget
from models.TransportWidget import TransportWidget
from models.UploadWidget import UploadWidget
from models.DownloadWidget import DownloadWidget
from models.SettingWidget import SettingWidget
from models.UsersWidget import UsersWidget
from models.StatisticWidget import StatisticWidget

import tkinter as tk
from tkinter import filedialog
from utils.S3Uploader import *
from utils.S3Downloader import *
from qasync import QEventLoop, asyncSlot

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
        
        self.manager = QNetworkAccessManager()
        self.manager.setCookieJar(cookieJar)
        # create sub interface
        self.fileInterface = FilesWidget('Home Interface', self)
        self.transportInterface = TransportWidget('Transport Interface',self)
        self.marketInterface = MarketWidget('Market Interface', self)
        self.downloadInterface = DownloadWidget('Download Interface',self)
        self.uploadInterface = UploadWidget('Upload Interface',self)
        self.statisticInterface = StatisticWidget('statistic Interface', self)
        self.libraryInterface = UsersWidget('Management Interface', self)
        self.settingInterface = SettingWidget('settings Interface', self)
        self.navigationInterface.setExpandWidth(170)
        self.navigationInterface.setCollapsible(False)

        self.fileInterface.upload_signal.connect(self.handle_upload_signal)
        self.fileInterface.download_signal.connect(self.handle_download_signal)
        self.statisticInterface.market_download_signal.connect(self.handle_market_download_signal)
        self.downloadInterface.table.market_download_finish_signal.connect(self.handle_market_download_finish_signal)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.fileInterface, FIF.FOLDER, '文件')
        self.addSubInterface(self.transportInterface, FIF.SAVE_COPY, '传输')
        self.addSubInterface(self.downloadInterface, FIF.DOWN, '正在下载',parent=self.transportInterface)
        self.addSubInterface(self.uploadInterface, FIF.UP, '正在上传',parent=self.transportInterface)
        self.addSubInterface(self.marketInterface, FIF.TAG, '数据市场')
        self.addSubInterface(self.statisticInterface, FIF.BOOK_SHELF, '处理')
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
    
    def handle_upload_signal(self,bucket,path,local):
        if not S3Uploader.start(bucket,path,local):
            InfoBar.error(
                title='上传出错',
                content="存在相同的上传，请勿重复上传",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1000,
                parent=self
            ).show()
        else:
            self.uploadInterface.start_upload(bucket,path,local)

    def handle_download_signal(self,bucket,targets):
        for tmp in targets:
            if not S3FileDownloader.start(bucket,tmp['cloud'],tmp['local']):
                InfoBar.error(
                    title='上传出错',
                    content="存在相同的下载，请勿重复下载",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1000,
                    parent=self
                ).show()
            else:
                self.downloadInterface.start_download(bucket,tmp['cloud'],tmp['local'])

    def handle_market_download_signal(self,marketId,marketName):
        url = QUrl(gConfig['server']['spring']['url']+'/market/items/current')
        query = QUrlQuery()
        query.addQueryItem("id", str(marketId))
        url.setQuery(query)
        request = QNetworkRequest(url)
        handler = partial(self.market_download_response,marketName = marketName)
        self.manager.finished.connect(handler)
        self.manager.get(request)
            
    def market_download_response(self,reply:QNetworkReply,marketName):
        self.manager.finished.disconnect()
        res = json.loads(reply.readAll().data().decode())
        if 'code' not in res:
            print(f"❗ Error Code: {res['status']}\n")
            print(f"❗ Error msg: {res['error']}")
            return
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            total_size = 0
            for dic in res['data']['marketItems']:
                total_size+=dic['size']
            if len(res['data']['marketItems']):
                if S3MarketDownloader.start(res['data']['marketItems'][0]['marketId'],marketName,total_size):
                    self.downloadInterface.start_market_download(res['data']['marketItems'][0]['marketId'],res['data']['marketItems'],marketName,total_size)

    def handle_market_download_finish_signal(self,marketId,marketName):
        InfoBar.success(
            title='下载完成',
            content=f'正在处理市场: {marketName}',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        ).show()
        self.statisticInterface.process(marketId,marketName)

async def main():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    w = Window()
    w.show()

    with loop:
        sys.exit(loop.run_forever())

if __name__ == '__main__':
    asyncio.run(main())

