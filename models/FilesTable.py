import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BodyLabel, MessageBox, setTheme, CaptionLabel, FluentWindow,
                            IconWidget, CheckBox, SubtitleLabel, setFont,SubtitleLabel,RoundMenu,Action,Dialog,LineEdit,MessageBoxBase)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidgetHeader import FilesWidgetHeader
from utils.S3Utils import s3Utils
from utils.TypeUtils import FileType, UnitTranslator



class FileItem(BodyLabel):

    jump_signal = pyqtSignal(str)
    only_selected_signal = pyqtSignal()
    state_change_signal = pyqtSignal(bool)

    def __init__(self,type:int,name:str,size:str,time:str,parent=None,highlight_start=-1,highlight_end=-1):
        super().__init__(parent=parent)
        self.__layout = QHBoxLayout(self)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.__type = type

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


        self.__download_btn = QLabel("", self)
        self.__download_btn.setFixedSize(15,15)
        self.__download_btn.setPixmap(QPixmap('./resources/icons/download.png'))
        self.__download_btn.setScaledContents(True)

        self.__more_btn = QLabel("", self)
        self.__more_btn.setFixedSize(15,15)
        self.__more_btn.setPixmap(QPixmap('./resources/icons/more.png'))
        self.__more_btn.setScaledContents(True)

        self.__name = BodyLabel(self.color_text_in_range(name,highlight_start,highlight_end,"blue"),self)
        font_metrics = QFontMetrics(self.__name.font())
        text_width = font_metrics.width(self.__name.text())  # 获取文本宽度
        if text_width>160:
            text_width = 160
        self.__name.setFixedWidth(text_width + 10)  # 添加一些额外的空间

        self.__size = CaptionLabel(size,self)
        self.__size.setFixedWidth(130)
        self.__type_widget = CaptionLabel(FileType.getTypeName(type),self)
        self.__type_widget.setFixedWidth(100)
        self.__time = CaptionLabel(time,self)
        self.__time.setFixedWidth(120)

        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__checkBox)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__img)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__name)
        self.__layout.addSpacing(160-text_width)
        self.__layout.addSpacing(150)
        self.__layout.addWidget(self.__download_btn)
        self.__layout.addWidget(self.__more_btn)
        self.__layout.addSpacing(5)
        self.__layout.addWidget(self.__size)
        self.__layout.addWidget(self.__type_widget)
        self.__layout.addWidget(self.__time,Qt.AlignmentFlag.AlignRight)

        self.hideBtn()
        
        self.setLayout(self.__layout)
        self.setFixedHeight(50)

        self.__name.setCursor(Qt.CursorShape.PointingHandCursor)  # 鼠标悬停显示手型
        self.__name.mousePressEvent = self.nameMousePressEvent

        self.mousePressEvent = self.onClick
        self.__checkBox.stateChanged.connect(self.onStateChanged)
        
    def nameMousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.__type==FileType.directory:
                self.jump_signal.emit(self.__name.text())
        return super().mousePressEvent(event)
    
    def onClick(self,event):
        self.only_selected_signal.emit()
        self.state_change_signal.emit(True)
        self.__checkBox.setChecked(True)
        self.parent().showMenu(event,self.mapToGlobal(event.pos()))
    
    def onStateChanged(self):
        if self.__checkBox.isChecked():
            op1 = QGraphicsOpacityEffect()
            op1.setOpacity(1)
            self.__checkBox.setGraphicsEffect(op1)
            self.setStyleSheet("background-color: #E5F9E9;")
        else:
            if not self.underMouse():
                self.hideBtn()
                self.setStyleSheet("background-color: #F7F9FC;")
        self.state_change_signal.emit(self.__checkBox.isChecked())

    def enterEvent(self, event):
        """鼠标移入事件"""
        self.setStyleSheet("background-color: #E5F9E9;")
        self.showBtn()


    def leaveEvent(self, event):
        """鼠标移出事件"""
        self.hideBtn()
        if not self.__checkBox.isChecked():
            self.setStyleSheet("background-color: #F7F9FC;")
    
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
        if not self.__checkBox.isChecked():
            op1 = QGraphicsOpacityEffect()
            op1.setOpacity(0)
            self.__checkBox.setGraphicsEffect(op1)
        op2 = QGraphicsOpacityEffect()
        op2.setOpacity(0)
        self.__download_btn.setGraphicsEffect(op2)
        op3 = QGraphicsOpacityEffect()
        op3.setOpacity(0)
        self.__more_btn.setGraphicsEffect(op3)
    
    def setState(self,data):
        self.__checkBox.setChecked(data)
    def getState(self):
        return self.__checkBox.isChecked()
    def getName(self):
        return self.__name.text()
    def color_text_in_range(self, text, start, end, color):
        """
        对字符串中指定区间内的字符上色
        :param text: 原始字符串
        :param start: 区间起始下标（包含）
        :param end: 区间结束下标（不包含）
        :param color: 颜色值（如 'red', '#FF0000'）
        :return: 带颜色的富文本字符串
        """
        if start < 0 or end > len(text) or start >= end:
            return text  # 如果区间无效，返回原始字符串

        # 将区间内的字符用 <font> 标签包裹
        colored_part = f"<font color='{color}'>{text[start:end]}</font>"
        # 拼接字符串
        result = text[:start] + colored_part + text[end:]
        return result



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
        self.__type_widget = CaptionLabel('类型',self)
        self.__type_widget.setFixedWidth(100)
        self.__time = CaptionLabel('修改时间',self)
        self.__time.setFixedWidth(120)

        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__checkBox)
        self.__layout.addSpacing(10)
        self.__layout.addSpacing(10)
        self.__layout.addWidget(self.__name)
        self.__layout.addSpacing(235)
        self.__layout.addWidget(self.__size)
        self.__layout.addWidget(self.__type_widget)
        self.__layout.addWidget(self.__time,Qt.AlignmentFlag.AlignRight)
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


class RenameDialog(MessageBoxBase):
    """ Custom message box """

    def __init__(self,name, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('重命名文件')
        self.fileEdit = LineEdit()

        self.fileEdit.setPlaceholderText('输入修改后的文件名')
        self.fileEdit.setClearButtonEnabled(True)

        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.fileEdit)
        self.fileEdit.setText(name)

        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(350)


    def showMessage(window,name,table):
        w = RenameDialog(name,window)
        if w.exec():
            table.rename_signal.emit(name,w.fileEdit.text())



class FilesTable(SubtitleLabel):

    jump_signal = pyqtSignal(str)
    show_signal = pyqtSignal(bool)
    number_signal = pyqtSignal(int)
    rename_signal = pyqtSignal(str,str)

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # self.setStyleSheet("background-color: rgb(240,243,249)")
        self.fileLayout = QVBoxLayout(self)
        self.fileLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fileLayout.setContentsMargins(0,0,0,0)
        self.fileLayout.setSpacing(0)

        self.header = TableHeader(self)
        self.fileLayout.addWidget(self.header)
        self.items:list[FileItem] = []
        self.setLayout(self.fileLayout)
        self.header.all_selected_signal.connect(self.handle_all_selected_signal)

        self.menu = RoundMenu()

        # 逐个添加动作，Action 继承自 QAction，接受 FluentIconBase 类型的图标
        self.menu.addAction(Action(FIF.COPY, '重命名', triggered=self.rename))
        self.menu.addAction(Action(FIF.COPY, '复制', triggered=lambda: print("复制成功")))
        self.menu.addAction(Action(FIF.CUT, '剪切', triggered=lambda: print("剪切成功")))
        self.menu.addAction(Action(FIF.COPY, '粘贴', triggered=lambda: print("粘贴成功")))
        self.menu.addAction(Action(FIF.CUT, '删除', triggered=lambda: print("删除成功")))


    def showMenu(self,event,position):
        # 判断是否是右键点击
        if event.button() == Qt.RightButton:
            self.menu.exec_(position)# 显示右键菜单
        else:
            # 调用父类的 mousePressEvent 方法，确保其他鼠标事件正常处理
            super().mousePressEvent(event)


    def handle_jump_signal(self, data):
        # 处理子组件传递的列表参数
        self.jump_signal.emit(data)
    
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


    def update(self,currentPath:list[str]):
        self.header.setState(False)
        response = s3Utils.getItems(pathList=currentPath)
        self.items.clear()
        if len(currentPath)==1:
            for bucket in response:
                name = bucket['Name']
                time = bucket['CreationDate'].strftime('%Y.%m.%d  %H:%M')
                type = FileType.directory
                size = '-'
                self.items.append(FileItem(type,name,size,time,self))
        elif len(currentPath)>1:
            if 'Contents' in response:
                for obj in response['Contents']:
                    name = os.path.basename(os.path.normpath(obj['Key']))
                    time = obj['LastModified'].strftime('%Y.%m.%d  %H:%M')
                    type = FileType.file
                    size = obj['Size']
                    self.items.append(FileItem(type,name,UnitTranslator.convert_bytes(size),time,self))

            if 'CommonPrefixes' in response:
                for common_prefix in response['CommonPrefixes']:
                    name = os.path.basename(os.path.normpath(common_prefix['Prefix']))
                    time = '-'
                    type = FileType.directory
                    size = '-'
                    self.items.append(FileItem(type,name,size,time,self))

        while self.fileLayout.count() > 1:
            item = self.fileLayout.takeAt(1)  # 取出布局中的第一个子项
            widget = item.widget()  # 获取子项对应的组件
            if widget is not None:
                widget.deleteLater()  # 销毁组件

        for i in self.items:
            i.jump_signal.connect(self.handle_jump_signal)
            i.only_selected_signal.connect(self.handle_selected_signal)
            i.state_change_signal.connect(self.handle_state_change_signal)
            self.fileLayout.addWidget(i)
            i.show()

        self.number_signal.emit(len(self.items))
    
    def search_update(self,bucket,key):
        self.header.setState(False)
        keys = s3Utils.search(bucket_name=bucket,keyword=key)
        self.items.clear()
        for obj in keys:
            name = os.path.basename(os.path.normpath(obj['key']))
            time = obj['modify'].strftime('%Y.%m.%d  %H:%M')
            type = FileType.file
            size = obj['size']
            self.items.append(FileItem(type,name,UnitTranslator.convert_bytes(size),time,self,obj['idx'],obj['idx']+len(key)))

        while self.fileLayout.count() > 1:
            item = self.fileLayout.takeAt(1)  # 取出布局中的第一个子项
            widget = item.widget()  # 获取子项对应的组件
            if widget is not None:
                widget.deleteLater()  # 销毁组件

        for i in self.items:
            # i.jump_signal.connect(self.handle_jump_signal)
            # i.only_selected_signal.connect(self.handle_selected_signal)
            # i.state_change_signal.connect(self.handle_state_change_signal)
            self.fileLayout.addWidget(i)
            i.show()

        self.number_signal.emit(len(self.items))


    def getTargets(self):
        res = []
        for i in self.items:
            if i.getState():
                res.append(i.getName())
        return res
    
    def findFileName(self,key):
        for i in self.items:
            if i.getName() == key:
                return True
        return False
    
    def rename(self):
        for i in self.items:
            if i.getState():
                RenameDialog.showMessage(self.window(),i.getName(),self)
                break
        


