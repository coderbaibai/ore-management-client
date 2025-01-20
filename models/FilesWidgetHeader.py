import collections
from tkinter import filedialog
from uuid import uuid1
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BreadcrumbBar, CommandBar, setFont, SearchLineEdit, BodyLabel,
                            Action, PrimaryPushButton, ToolButton,CommandBarView,PushButton)
from qfluentwidgets import FluentIcon as FIF

from utils.S3Utils import *

class FilesWidgetHeader(QWidget):

    update_signal = pyqtSignal(list)

    copy_signal = pyqtSignal(str,str)
    move_signal = pyqtSignal(str,str)
    paste_signal = pyqtSignal(str,str)
    delete_signal = pyqtSignal(str,str)

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(100)
        self.vLayout = QVBoxLayout(self)
        self.disabled_times = 0

        # 设置顶部
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(2)
        self.search = SearchLineEdit(self)
        self.search.setMaximumWidth(200)
        self.commandBarMove = CommandBar(self)

        self.drawbackBtn = ToolButton(FIF.LEFT_ARROW,self)
        self.drawbackBtn.clicked.connect(self.drawback)
        self.forwardBtn = ToolButton(FIF.RIGHT_ARROW,self)
        self.forwardBtn.clicked.connect(self.forward)

        self.uploadBtn = PrimaryPushButton(FIF.UP,'上传',self)
        self.isUpload = True
        self.uploadBtn.clicked.connect(self.uploadItems)

        self.pasteBtn = PushButton(FIF.PASTE,text='粘贴',parent = self)
        self.pasteBtn.setVisible(False)
        self.pasteBtn.clicked.connect(self.pasteItems)

        self.commandBarTrans = CommandBarView(self)
        self.commandBarTrans.addAction(Action(FIF.DOWNLOAD,text='下载', triggered=lambda: print("下载")))
        self.commandBarTrans.addSeparator()
        self.commandBarTrans.addAction(Action(FIF.COPY,text='复制', triggered=self.copyItems))
        self.commandBarTrans.addSeparator()
        self.commandBarTrans.addAction(Action(FIF.CUT,text='移动', triggered=self.moveItems))
        self.commandBarTrans.addSeparator()
        self.commandBarTrans.addAction(Action(FIF.DELETE,text='删除', triggered=self.deleteItems))
        self.commandBarTrans.resizeToSuitableWidth()
        # 批量添加动作
        self.topLayout.addWidget(self.drawbackBtn)
        self.topLayout.addWidget(self.forwardBtn)
        self.topLayout.addSpacing(8)
        self.topLayout.addWidget(self.uploadBtn)
        self.topLayout.addSpacing(10)
        self.topLayout.addWidget(self.pasteBtn)
        self.topLayout.addSpacing(5)
        self.topLayout.addWidget(self.commandBarTrans)
        self.topLayout.addStretch()
        self.topLayout.addWidget(self.search)
        # 设置底部
        self.bottomLayout = QHBoxLayout()
        self.navi = BreadcrumbBar(self)
        self.labelTotal = BodyLabel("已加载x个",self)
        self.bottomLayout.addWidget(self.navi)
        self.bottomLayout.addWidget(self.labelTotal,alignment=(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter))
        # 设置整体
        self.vLayout.addLayout(self.topLayout)
        self.vLayout.addLayout(self.bottomLayout)
        self.setLayout(self.vLayout)

        # self.navi.currentItemChanged.connect(lambda key: print(key))
        self.navi.currentIndexChanged.connect(self.clickBar)
        setFont(self.navi, 15)
        self.navi.setSpacing(20)

        self.currentPath:list[str] = []
        self.historyPath = collections.deque()
        self.curIndex = 0
        self.pushPath(["全部文件"])

        self.updateBreadBar()
        
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(220,220,220))
        self.setPalette(palette)
        self.setAutoFillBackground(True)  # 启用背景填充
        # 隐藏命令栏
        self.changeBarState(False)

    
    
    def addItemAndJump(self,item:str):
        newPath = self.currentPath.copy()
        newPath.append(item)
        self.pushPath(newPath)
        self.updateBreadBar()

    def pushPath(self,path:list):
        # 修改历史路径
        self.currentPath = path.copy()
        while len(self.historyPath)>self.curIndex+1:
            self.historyPath.pop()
        self.historyPath.append(self.currentPath.copy())
        self.curIndex = len(self.historyPath)-1
        # 更新当前文件夹
        self.update_signal.emit(self.currentPath.copy())
        self.updatePathBtnState()

    def drawback(self):
        # 修改历史路径
        self.curIndex = self.curIndex-1
        self.currentPath = self.historyPath[self.curIndex].copy()
        # 更新当前文件夹
        self.updateBreadBar()
        self.update_signal.emit(self.currentPath.copy())
        self.updatePathBtnState()

    def forward(self):
        # 修改历史路径
        self.curIndex = self.curIndex+1
        self.currentPath = self.historyPath[self.curIndex].copy()
        # 更新当前文件夹
        self.updateBreadBar()
        self.update_signal.emit(self.currentPath.copy())
        self.updatePathBtnState()

    def updateBreadBar(self):
        self.changeBarState(False)
        self.navi.clear()
        for item in self.currentPath:
            self.disabled_times = self.disabled_times+1
            self.navi.addItem(uuid1().hex,item)
        if len(self.currentPath)<=1:
            self.uploadBtn.setText('新建桶')
            self.uploadBtn.setIcon(FIF.ADD)
            self.isUpload = False
        else:
            self.uploadBtn.setText('上传')
            self.uploadBtn.setIcon(FIF.UP)
            self.isUpload = True
    
    def clickBar(self,index):
        if self.disabled_times!=0:
            self.disabled_times = self.disabled_times-1
        else:
            temp = self.currentPath.copy()
            while index<len(temp)-1:
                temp.pop()
            self.pushPath(temp)
            self.updateBreadBar()

    def updatePathBtnState(self):
        if self.curIndex!=0:
            self.drawbackBtn.setEnabled(True)
        else:
            self.drawbackBtn.setEnabled(False)
        if self.curIndex!=len(self.historyPath)-1:
            self.forwardBtn.setEnabled(True)
        else:
            self.forwardBtn.setEnabled(False)

    def changeBarState(self,data):
        if len(self.currentPath) <= 1:
            op1 = QGraphicsOpacityEffect()
            op1.setOpacity(0)
            self.commandBarTrans.setGraphicsEffect(op1)
            return
        if data:
            op1 = QGraphicsOpacityEffect()
            op1.setOpacity(1)
            self.commandBarTrans.setGraphicsEffect(op1)
        else:
            op1 = QGraphicsOpacityEffect()
            op1.setOpacity(0)
            self.commandBarTrans.setGraphicsEffect(op1)
    def copyItems(self):
        if len(self.currentPath) <= 1:
            print('不可复制桶')
        pathStr = '/'.join(self.currentPath[2:])
        if pathStr!='':
            pathStr = pathStr+'/'
        self.pasteBtn.setVisible(True)
        self.copy_signal.emit(self.currentPath[1],pathStr)

    def moveItems(self):
        if len(self.currentPath) <= 1:
            print('不可移动桶')
        pathStr = '/'.join(self.currentPath[2:])
        if pathStr!='':
            pathStr = pathStr+'/'
        self.pasteBtn.setVisible(True)
        self.move_signal.emit(self.currentPath[1],pathStr)

    def pasteItems(self):
        if len(self.currentPath) <= 1:
            print('不可移动到桶目录下')
        pathStr = '/'.join(self.currentPath[2:])
        if pathStr!='':
            pathStr = pathStr+'/'
        self.paste_signal.emit(self.currentPath[1],pathStr)

    def deleteItems(self):
        if len(self.currentPath) <= 1:
            print('不可删除桶')
        pathStr = '/'.join(self.currentPath[2:])
        if pathStr!='':
            pathStr = pathStr+'/'
        self.pasteBtn.setVisible(True)
        self.delete_signal.emit(self.currentPath[1],pathStr)

    def uploadItems(self):
        if self.isUpload:
            localPath = filedialog.askopenfilename(title="选择文件", filetypes=[("All files", "*.*")])
            if localPath=='' or localPath=='()':
                return
            
        
