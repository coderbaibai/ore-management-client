from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BodyLabel, MessageBox, setTheme, CaptionLabel, FluentWindow,
                            IconWidget, CheckBox, SubtitleLabel, setFont,SubtitleLabel)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidgetHeader import FilesWidgetHeader

class FileTypge():
    directory = 1
    file = 2

    def getTypeName(input:int):
        if input==FileTypge.directory:
            return '文件夹'
        elif input==FileTypge.file:
            return '文件'
        else:
            return 'unknown'
    def getIconPath(input:int):
        if input==FileTypge.directory:
            return './resources/icons/directory.png'
        elif input==FileTypge.file:
            return './resources/icons/file.png'
        else:
            return 'unknown'

class TableItem(BodyLabel):
    def __init__(self,type:int,name:str,size:str,time:str,parent=None):
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

        self.__img = QLabel("", self)
        self.__img.setFixedSize(30,30)
        self.__img.setPixmap(QPixmap(FileTypge.getIconPath(type)))
        self.__img.setScaledContents(True)


        self.__download_btn = QLabel("", self)
        self.__download_btn.setFixedSize(15,15)
        self.__download_btn.setPixmap(QPixmap('./resources/icons/download.png'))
        self.__download_btn.setScaledContents(True)

        self.__more_btn = QLabel("", self)
        self.__more_btn.setFixedSize(15,15)
        self.__more_btn.setPixmap(QPixmap('./resources/icons/more.png'))
        self.__more_btn.setScaledContents(True)

        self.__name = BodyLabel(name,self)
        self.__name.setFixedWidth(170)
        self.__size = CaptionLabel(size,self)
        self.__size.setFixedWidth(130)
        self.__type = CaptionLabel(FileTypge.getTypeName(type),self)
        self.__type.setFixedWidth(100)
        self.__time = CaptionLabel(time,self)
        self.__time.setFixedWidth(120)

        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__checkBox)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__img)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__name)
        self.__layout.addSpacing(150)
        self.__layout.addWidget(self.__download_btn)
        self.__layout.addWidget(self.__more_btn)
        self.__layout.addSpacing(5)
        self.__layout.addWidget(self.__size)
        self.__layout.addWidget(self.__type)
        self.__layout.addWidget(self.__time,Qt.AlignmentFlag.AlignRight)

        self.isSelect = False
        self.hideBtn()
        
        self.setLayout(self.__layout)
        self.setFixedHeight(50)

        self.__name.setCursor(Qt.CursorShape.PointingHandCursor)  # 鼠标悬停显示手型
        self.__name.mousePressEvent = self.nameMousePressEvent
        
    def nameMousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_click()

    def on_click(self):
        print(f"Label clicked: {self.__name}")  # 打印被点击的文本


    def enterEvent(self, event):
        """鼠标移入事件"""
        self.setStyleSheet("background-color: green;")
        self.showBtn()


    def leaveEvent(self, event):
        """鼠标移出事件"""
        self.setStyleSheet("background-color: pink;")
        if not self.isSelect:
            self.hideBtn()
    
    def showBtn(self):
        op1 = QGraphicsOpacityEffect()
        op1.setOpacity(1)
        self.__checkBox.setGraphicsEffect(op1)
        op2 = QGraphicsOpacityEffect()
        op2.setOpacity(1)
        self.__download_btn.setGraphicsEffect(op2)
        op3 = QGraphicsOpacityEffect()
        op3.setOpacity(1)
        self.__more_btn.setGraphicsEffect(op3)

    def hideBtn(self):
        op1 = QGraphicsOpacityEffect()
        op1.setOpacity(0)
        self.__checkBox.setGraphicsEffect(op1)
        op2 = QGraphicsOpacityEffect()
        op2.setOpacity(0)
        self.__download_btn.setGraphicsEffect(op2)
        op3 = QGraphicsOpacityEffect()
        op3.setOpacity(0)
        self.__more_btn.setGraphicsEffect(op3)


class TableHeader(CaptionLabel):
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
        self.__type = CaptionLabel('类型',self)
        self.__type.setFixedWidth(100)
        self.__time = CaptionLabel('修改时间',self)
        self.__time.setFixedWidth(120)

        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__checkBox)
        self.__layout.addSpacing(10)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__name)
        self.__layout.addSpacing(235)
        self.__layout.addWidget(self.__size)
        self.__layout.addWidget(self.__type)
        self.__layout.addWidget(self.__time,Qt.AlignmentFlag.AlignRight)

        self.setLayout(self.__layout)
        self.setFixedHeight(40)


    def enterEvent(self, event):
        """鼠标移入事件"""
        self.setStyleSheet("background-color: green;")


    def leaveEvent(self, event):
        """鼠标移出事件"""
        self.setStyleSheet("background-color: pink;")

class FilesTable(SubtitleLabel):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet("background-color: skyblue")
        self.fileLayout = QVBoxLayout(self)
        self.fileLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fileLayout.setContentsMargins(0,0,0,0)
        self.fileLayout.setSpacing(0)
        self.header = TableHeader(self)
        self.items:list[TableItem] = []
        self.items.append(TableItem(FileTypge.file,'文档.txt','200KB','2024.01.04 21:58',self))
        self.items.append(TableItem(FileTypge.directory,'考研资料11111111111234567894561237','-','2024.01.03 15:13',self))
        
        self.header.setStyleSheet("background-color: pink")
        self.fileLayout.addWidget(self.header)
        for i in self.items:
            i.setStyleSheet("background-color: pink")
            self.fileLayout.addWidget(i)

        self.setLayout(self.fileLayout)