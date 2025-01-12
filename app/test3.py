from uuid import uuid1
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BreadcrumbBar, LineEdit, PrimaryToolButton, SearchLineEdit, BodyLabel,
                            setFont, SubtitleLabel, SubtitleLabel, StrongBodyLabel)
from qfluentwidgets import FluentIcon as FIF

import sys

class Demo(QWidget):

    def __init__(self):
        super().__init__()
        self.setStyleSheet('Demo{background:rgb(255,255,255)}')

        self.breadcrumbBar = BreadcrumbBar(self)
        self.stackedWidget = QStackedWidget(self)

        self.lineEdit = LineEdit(self)
        self.addButton = PrimaryToolButton(FIF.SEND, self)

        self.vBoxLayout = QVBoxLayout(self)
        self.lineEditLayout = QHBoxLayout()

        # 按下回车键或者点击按钮时添加一个新导航项和子界面
        self.addButton.clicked.connect(lambda: self.addInterface(self.lineEdit.text()))
        self.lineEdit.returnPressed.connect(lambda: self.addInterface(self.lineEdit.text()))
        self.breadcrumbBar.currentItemChanged.connect(self.switchInterface)
        self.breadcrumbBar.currentIndexChanged.connect(lambda key: print(key))

        # 调整面包屑导航的尺寸
        setFont(self.breadcrumbBar, 10)
        self.breadcrumbBar.setSpacing(20)
        self.lineEdit.setPlaceholderText('Enter the name of interface')

        # 添加两个导航项
        self.addInterface('Home')
        self.addInterface('Documents')

        # 初始化布局
        self.vBoxLayout.setContentsMargins(20, 20, 20, 20)
        self.vBoxLayout.addWidget(self.breadcrumbBar)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.addLayout(self.lineEditLayout)

        self.lineEditLayout.addWidget(self.lineEdit, 1)
        self.lineEditLayout.addWidget(self.addButton)
        self.resize(500, 500)

    def addInterface(self, text: str):
        if not text:
            return

        w = SubtitleLabel(text)
        w.setObjectName(uuid1().hex)    # 使用随机生成的路由键
        w.setAlignment(Qt.AlignCenter)

        self.lineEdit.clear()
        self.stackedWidget.addWidget(w)
        self.stackedWidget.setCurrentWidget(w)

        self.breadcrumbBar.addItem(w.objectName(), text)

    def switchInterface(self, objectName):
        self.stackedWidget.setCurrentWidget(self.findChild(SubtitleLabel, objectName))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()