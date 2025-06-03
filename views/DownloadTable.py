import os
from threading import Thread
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BodyLabel, MessageBox, ProgressBar, CaptionLabel, FluentWindow,
                            IconWidget, CheckBox, SubtitleLabel, setFont,SubtitleLabel)
from qfluentwidgets import FluentIcon as FIF

from views.FilesWidgetHeader import FilesWidgetHeader
from OreUtils.S3Utils import s3Utils
from OreUtils.S3Uploader import S3Uploader
from OreUtils.S3Downloader import *
from OreUtils.SqliteUtils import TransportRecord
from OreUtils.TypeUtils import FileType,StateType,UnitTranslator
from peewee import Select
from config.GConfig import gConfig


class DownloadItem(BodyLabel):

    only_selected_signal = pyqtSignal()
    state_change_signal = pyqtSignal(bool)
    is_pause_signal = pyqtSignal(int,bool)

    def __init__(self,id:int,type:int,name:str,size:str,bucket:str,cloud:str,local:str,parent=None):
        super().__init__(parent=parent)
        self.__layout = QHBoxLayout(self)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.__id = id

        self.__checkBox = CheckBox(self)
        self.__checkBox.setFixedSize(15,15)
        self.__checkBox.setStyleSheet("""
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        """)
        self.bucket = bucket
        self.cloud = cloud
        self.local = local

        self.__img = QLabel("", self)
        self.__img.setFixedSize(30,30)
        self.__img.setPixmap(QPixmap(FileType.getIconPath(type)))
        self.__img.setScaledContents(True)

        self.__name = BodyLabel(name,self)
        font_metrics = QFontMetrics(self.__name.font())
        text_width = font_metrics.width(self.__name.text())  # 获取文本宽度
        if text_width>160:
            text_width = 160
        self.__name.setFixedWidth(text_width + 10)  # 添加一些额外的空间

        self.__size = CaptionLabel(size,self)
        self.__size.setFixedWidth(110)

        self.__state_label= CaptionLabel(self)
        self.__state_label.setFixedWidth(150)
        self.__state_label.setFixedHeight(50)
        self.__state_layout = QVBoxLayout()
        self.__state_info_bar= ProgressBar(self)
        self.__state_info_label= CaptionLabel('已暂停',self)
        self.__isPause = True
        self.__state_layout.setSpacing(0)
        self.__state_layout.setContentsMargins(0,0,0,0)
        self.__state_layout.addStretch(2)
        self.__state_layout.addWidget(self.__state_info_bar)
        self.__state_layout.addWidget(self.__state_info_label)
        self.__state_layout.addStretch(10)
        self.__state_label.setLayout(self.__state_layout)

        self.__pause_btn = QLabel("", self)
        self.__pause_btn.setFixedSize(15,15)
        self.__pause_btn.setPixmap(QPixmap('./resources/icons/start.png'))
        self.__pause_btn.setScaledContents(True)

        self.__delete_btn = QLabel("", self)
        self.__delete_btn.setFixedSize(15,15)
        self.__delete_btn.setPixmap(QPixmap('./resources/icons/eraser.png'))
        self.__delete_btn.setScaledContents(True)

        self.__find_btn = QLabel("", self)
        self.__find_btn.setFixedSize(15,15)
        self.__find_btn.setPixmap(QPixmap('./resources/icons/search.png'))
        self.__find_btn.setScaledContents(True)

        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__checkBox)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__img)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__name)
        self.__layout.addSpacing(160-text_width)
        self.__layout.addSpacing(155)
        self.__layout.addWidget(self.__size)
        self.__layout.addWidget(self.__state_label)
        self.__layout.addSpacing(20)
        self.__layout.addWidget(self.__pause_btn)
        self.__layout.addSpacing(5)
        self.__layout.addWidget(self.__delete_btn)
        self.__layout.addSpacing(5)
        self.__layout.addWidget(self.__find_btn)
        
        self.setLayout(self.__layout)
        self.setFixedHeight(50)

        self.__name.setCursor(Qt.CursorShape.PointingHandCursor)  # 鼠标悬停显示手型
        self.__pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)  # 鼠标悬停显示手型
        self.__delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)  # 鼠标悬停显示手型
        self.__find_btn.setCursor(Qt.CursorShape.PointingHandCursor)  # 鼠标悬停显示手型
        self.__pause_btn.mousePressEvent = self.press
        

        self.mousePressEvent = self.onClick
        self.__checkBox.stateChanged.connect(self.onStateChanged)

    def onClick(self,event):
        self.only_selected_signal.emit()
        self.state_change_signal.emit(True)
        self.__checkBox.setChecked(True)
    
    def onStateChanged(self):
        if self.__checkBox.isChecked():
            self.setStyleSheet("background-color: #E5F9E9;")
        else:
            if not self.underMouse():
                self.setStyleSheet("background-color: #F7F9FC;")
        self.state_change_signal.emit(self.__checkBox.isChecked())

    def enterEvent(self, event):
        """鼠标移入事件"""
        self.setStyleSheet("background-color: #E5F9E9;")


    def leaveEvent(self, event):
        """鼠标移出事件"""
        if not self.__checkBox.isChecked():
            self.setStyleSheet("background-color: #F7F9FC;")
    
    def setState(self,data):
        self.__checkBox.setChecked(data)
    def getState(self):
        return self.__checkBox.isChecked()
    def getName(self):
        return self.__name.text()
    def getId(self):
        return self.__id
    
    def pause(self):
        self.__pause_btn.setPixmap(QPixmap('./resources/icons/start.png'))
        self.__pause_btn.setScaledContents(True)
        self.__state_info_bar.setValue(0)
        self.__state_info_label.setText('已暂停')
        self.__isPause = True
    def start(self):
        self.__pause_btn.setPixmap(QPixmap('./resources/icons/pause.png'))
        self.__pause_btn.setScaledContents(True)
        self.__isPause = False
    def setRate(self,data):
        if not self.__isPause:
            self.__state_info_label.setText(data)
    def setValue(self,data):
        if not self.__isPause:
            self.__state_info_bar.setValue(data)

    def press(self,event):
        if event.button() == Qt.LeftButton:
            if self.__isPause:
                self.start()
                self.is_pause_signal.emit(self.__id,False)
            else:
                self.pause()
                self.is_pause_signal.emit(self.__id,True)



class TableHeader(CaptionLabel):

    all_selected_signal = pyqtSignal(bool)

    def __init__(self,parent=None):
        super().__init__(parent=parent)


        self.__layout = QHBoxLayout(self)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        

        self.__checkBox = CheckBox(self)
        self.__checkBox.setFixedSize(15,15)
        self.__checkBox.setStyleSheet("""
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        """)

        self.__name = CaptionLabel('文件名',self)
        self.__name.setFixedWidth(170)
        self.__size = CaptionLabel('大小',self)
        self.__size.setFixedWidth(130)
        self.__state_widget = CaptionLabel('状态',self)
        self.__state_widget.setFixedWidth(100)
        self.__operation = CaptionLabel('操作',self)
        self.__operation.setFixedWidth(120)

        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__checkBox)
        self.__layout.addSpacing(12)
        self.__layout.addWidget(self.__name)
        self.__layout.addSpacing(200)
        self.__layout.addWidget(self.__size)
        self.__layout.addWidget(self.__state_widget)
        self.__layout.addSpacing(50)
        self.__layout.addWidget(self.__operation,Qt.AlignmentFlag.AlignRight)
        self.isChildClicked = False

        self.setLayout(self.__layout)
        self.setFixedHeight(40)

        self.__checkBox.stateChanged.connect(self.changeState)


    def enterEvent(self, event):
        """鼠标移入事件"""
        self.setStyleSheet("background-color: #E5F9E9;")


    def leaveEvent(self, event):
        """鼠标移出事件"""
        self.setStyleSheet("background-color: #F7F9FC;")

    def changeState(self):
        if not self.isChildClicked:
            self.all_selected_signal.emit(self.__checkBox.isChecked())
        self.isChildClicked = False

    def setState(self,data):
        # 如果是通过子组件进入的非选中状态，则不触发事件
        if self.__checkBox.isChecked()==data:
            return
        self.isChildClicked = True
        self.__checkBox.setChecked(data)
    def getState(self):
        return self.__checkBox.isChecked()


class DownloadTable(QWidget):

    show_signal = pyqtSignal(bool)
    number_signal = pyqtSignal(int)
    market_download_finish_signal = pyqtSignal(int,str)

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.fileLayout = QVBoxLayout(self)
        self.fileLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fileLayout.setContentsMargins(0,0,0,0)
        self.fileLayout.setSpacing(0)

        self.header = TableHeader(self)
        self.fileLayout.addWidget(self.header)
        self.items:list[DownloadItem] = []
        self.setLayout(self.fileLayout)
        self.header.all_selected_signal.connect(self.handle_all_selected_signal)
        self.__downloaderList :list[S3Downloader] = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateDownloader)
        self.timer.start(gConfig['client']['update-time'])
    
    def handle_selected_signal(self):
        for i in self.items:
            i.setState(False)

    def handle_all_selected_signal(self,data):
        for i in self.items:
            i.setState(data)
    
    def handle_state_change_signal(self,data):
        isBarShow = False
        for i in self.items:
            if i.getState():
                isBarShow = True
                break
        self.show_signal.emit(isBarShow)
        for i in self.items:
            if not i.getState():
                self.header.setState(False)
                return
        self.header.setState(True)

    def handle_is_pause_signal(self,id,is_pause):
        if is_pause:
            for uploader in self.__downloaderList:
                if uploader.get_id()==id:
                    uploader.stop()
            self.__downloaderList = [item for item in self.__uploaderList if item.get_id()!=id]  
        else:
            # if len(self.__downloaderList)>=gConfig['client']['uploader-length']:
            #     #如果超出长度，暂停第一个
            #     first = self.__downloaderList[0].get_id()
            #     for i in self.items:
            #         if i.getId()==first:
            #             i.pause()
            #             break
            #     self.__downloaderList[0].stop()
            #     self.__upload__downloaderListerList = self.__downloaderList[1:]

            for i in self.items:
                if i.getId()==id:
                    downloader = (i.bucket,i.cloud,i.local,id)
                    down_thread = Thread(target=downloader.execute)
                    down_thread.start()
                    self.__downloaderList.append(uploader)



    def update(self):
        self.header.setState(False)
        self.items.clear()
        temps :list[TransportRecord] = list(TransportRecord.select().where(
                (TransportRecord.finish == 0) &
                (TransportRecord.state == StateType.download)
            ))
        for tmp in temps:
            self.items.append(DownloadItem(tmp.id,tmp.type,tmp.name,UnitTranslator.convert_bytes(tmp.size),tmp.bucket,tmp.cloud,tmp.local,self))

        while self.fileLayout.count() > 1:
            item = self.fileLayout.takeAt(1)  # 取出布局中的第一个子项
            widget = item.widget()  # 获取子项对应的组件
            if widget is not None:
                widget.deleteLater()  # 销毁组件

        for i in self.items:
            i.only_selected_signal.connect(self.handle_selected_signal)
            i.state_change_signal.connect(self.handle_state_change_signal)
            i.is_pause_signal.connect(self.handle_is_pause_signal)
            self.fileLayout.addWidget(i)
            i.show()

        if len(self.items)==0:
            self.showLable()
        
        self.number_signal.emit(len(self.items))


    def getTargets(self):
        res = []
        for i in self.items:
            if i.getState():
                res.append(i.getId())
        return res
    
    def findFileName(self,key):
        for i in self.items:
            if i.getName() == key:
                return True
        return False
    
    def showLable(self):
        self.label = SubtitleLabel('暂无记录', self)
        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.fileLayout.addWidget(self.label, 1, Qt.AlignCenter)

    def start_download(self,bucket,path,local):
        self.update()
        temps = list(TransportRecord.select().where(
            (TransportRecord.local == local) &
            (TransportRecord.bucket == bucket) &
            (TransportRecord.cloud == path) &
            (TransportRecord.finish == 0)
        ))
        if len(temps)==0:
            print('error')
            return
        # if len(self.__uploaderList)>=gConfig['client']['uploader-length']:
        #     return
        downloader = S3FileDownloader(bucket,path,local,temps[0].id)
        down_thread = Thread(target=downloader.execute)
        down_thread.start()
        for tmp in self.items:
            if tmp.getId()==temps[0].id:
                tmp.start()
        self.__downloaderList.append(downloader)

    def start_market_download(self,marketId,marketItemList,marketName,totalSize):
        self.update()
        temps = list(TransportRecord.select().where(
            (TransportRecord.market_id == marketId) &
            (TransportRecord.finish == 0)
        ))
        if len(temps)==0:
            print('error')
            return
        downloader = S3MarketDownloader(marketId,marketItemList,marketName,totalSize,temps[0].id)
        down_thread = Thread(target=downloader.execute)
        down_thread.start()

        for tmp in self.items:
            if tmp.getId()==temps[0].id:
                tmp.start()
        self.__downloaderList.append(downloader)
        
    
    def updateDownloader(self):
        for downloader in self.__downloaderList:
            id = downloader.get_id()
            if downloader.is_finished():
                if isinstance(downloader,S3MarketDownloader):
                    self.market_download_finish_signal.emit(downloader.marketId,downloader.marketName)
                record:TransportRecord = TransportRecord.get_by_id(id)
                record.finish = 1
                record.save()
                downloader.stop()
                self.deleteById(id)
            else:
                for tmp in self.items:
                    if tmp.getId()==id:
                        tmp.setRate(UnitTranslator.convert_bytes(downloader.get_delta()*4)+'/s')
                        tmp.setValue(downloader.get_process())
                        
        self.__downloaderList = [item for item in self.__downloaderList if not item.is_finished()]  
                
    def deleteById(self,id):
        for (index,val) in enumerate(self.items):
            if val.getId()==id:
                del self.items[index]
                item = self.fileLayout.takeAt(index+1)  # 取出布局中的第一个子项
                widget = item.widget()  # 获取子项对应的组件
                if widget is not None:
                    widget.deleteLater()  # 销毁组件
                break


