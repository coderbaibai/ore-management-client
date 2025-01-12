from uuid import uuid1
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BreadcrumbBar, CommandBar, setFont, SearchLineEdit, BodyLabel,
                            Action, SubtitleLabel, StrongBodyLabel)
from qfluentwidgets import FluentIcon as FIF
import collections
from models.TransportWidget import TransportWidget

class FilesWidgetHeader(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(100)
        self.vLayout = QVBoxLayout(self)

        # 设置顶部
        self.topLayout = QHBoxLayout()
        self.search = SearchLineEdit(self)
        self.commandBarMove = CommandBar(self)

        self.commandBarMove.addAction(Action(FIF.LEFT_ARROW, '撤回', triggered=lambda: print("撤回")))
        # 添加分隔符
        self.commandBarMove.addAction(Action(FIF.RIGHT_ARROW, '前进', triggered=lambda: print("前进")))

        self.commandBarTrans = CommandBar(self)
        self.commandBarTrans.addAction(Action(FIF.UP, '上传', triggered=lambda: print("上传")))
        # 添加分隔符
        self.commandBarTrans.addSeparator()
        self.commandBarTrans.addAction(Action(FIF.DOWN, '下载', triggered=lambda: print("下载")))
        self.commandBarTrans.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.commandBarTrans.setMinimumWidth(200)
        # 批量添加动作
        self.topLayout.addWidget(self.commandBarMove)
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
        # self.navi.currentIndexChanged.connect(lambda key: print(key))
        setFont(self.navi, 15)
        self.navi.setSpacing(20)

        self.currentPath = []
        self.historyPath = collections.deque()
        self.curIndex = 0
        self.pushPath(["全部文件"])
        self.updateBreadBar()

        

    def pushPath(self,path:list):
        self.currentPath = path.copy()
        while len(self.historyPath)>self.curIndex+1:
            self.currentPath.pop()
        self.historyPath.append(self.currentPath.copy())
        self.curIndex = len(self.historyPath)-1

    def drawback(self):
        self.curIndex = self.curIndex-1
        self.currentPath = self.historyPath[self.curIndex].copy()
        self.updateBreadBar()

    def forward(self):
        self.curIndex = self.curIndex+1
        self.currentPath = self.historyPath[self.curIndex].copy()
        self.updateBreadBar()

    def updateBreadBar(self):
        self.navi.clear()
        # for key,item in enumerate(self.currentPath):
            # self.navi.addItem(item+'-'+str(key),item)
        for item in self.currentPath:
            self.navi.addItem(uuid1().hex,item)

