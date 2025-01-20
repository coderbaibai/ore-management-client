import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BodyLabel, MessageBox, setTheme, CaptionLabel, FluentWindow,
                            IconWidget, CheckBox, SubtitleLabel, setFont,SubtitleLabel)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidgetHeader import FilesWidgetHeader
from utils.S3Utils import s3Utils
from utils.SqliteUtils import TransportRecord
from utils.TypeUtils import FileType,StateType
from peewee import Select


class TransportItem(BodyLabel):

    only_selected_signal = pyqtSignal()
    state_change_signal = pyqtSignal(bool)

    def __init__(self,id:int,type:int,name:str,size:str,time:str,state:int,parent=None):
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
        self.__size.setFixedWidth(130)

        self.__state_img = QLabel("", self)
        self.__state_img.setFixedSize(15,15)
        self.__state_img.setPixmap(QPixmap(StateType.getIconPath(state)))
        self.__state_img.setScaledContents(True)
        self.__state_info = CaptionLabel(StateType.getTypeName(state),self)

        self.__time = CaptionLabel(time,self)
        self.__time.setFixedWidth(75)

        self.__find_btn = QLabel("", self)
        self.__find_btn.setFixedSize(15,15)
        self.__find_btn.setPixmap(QPixmap('./resources/icons/search.png'))
        self.__find_btn.setScaledContents(True)

        self.__delete_btn = QLabel("", self)
        self.__delete_btn.setFixedSize(15,15)
        self.__delete_btn.setPixmap(QPixmap('./resources/icons/eraser.png'))
        self.__delete_btn.setScaledContents(True)

        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__checkBox)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__img)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__name)
        self.__layout.addSpacing(160-text_width)
        self.__layout.addSpacing(155)
        self.__layout.addWidget(self.__size)
        self.__layout.addWidget(self.__state_img)
        self.__layout.addWidget(self.__state_info)
        self.__layout.addWidget(self.__time)
        self.__layout.addWidget(self.__find_btn)
        self.__layout.addSpacing(5)
        self.__layout.addWidget(self.__delete_btn)
        
        self.setLayout(self.__layout)
        self.setFixedHeight(50)

        self.__name.setCursor(Qt.CursorShape.PointingHandCursor)  # 鼠标悬停显示手型

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


class TransportTable(SubtitleLabel):

    show_signal = pyqtSignal(bool)
    number_signal = pyqtSignal(int)

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.fileLayout = QVBoxLayout(self)
        self.fileLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fileLayout.setContentsMargins(0,0,0,0)
        self.fileLayout.setSpacing(0)

        self.header = TableHeader(self)
        self.fileLayout.addWidget(self.header)
        self.items:list[TransportItem] = []
        self.setLayout(self.fileLayout)
        self.header.all_selected_signal.connect(self.handle_all_selected_signal)
    
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


    def update(self):
        self.header.setState(False)
        self.items.clear()
        temps :list[TransportRecord] = list(TransportRecord.select().where(TransportRecord.finish == 1))
        for tmp in temps:
            self.items.append(TransportItem(tmp.id,tmp.type,tmp.name,str(tmp.size),tmp.time,tmp.state,self))

        while self.fileLayout.count() > 1:
            item = self.fileLayout.takeAt(1)  # 取出布局中的第一个子项
            widget = item.widget()  # 获取子项对应的组件
            if widget is not None:
                widget.deleteLater()  # 销毁组件

        for i in self.items:
            i.only_selected_signal.connect(self.handle_selected_signal)
            i.state_change_signal.connect(self.handle_state_change_signal)
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