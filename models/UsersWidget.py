
from qfluentwidgets import (InfoBar, InfoBarPosition, setTheme, Theme, TableWidget,
                            PushButton, PrimaryPushButton, SubtitleLabel, LineEdit,MessageBoxBase)
from qfluentwidgets import FluentIcon as FIF
from threading import Thread
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager,QNetworkReply
from config.GConfig import gConfig
import json

class RenameDialog(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('添加用户')
        self.usernameEdit = LineEdit()

        self.usernameEdit.setPlaceholderText('请输入用户名')
        self.usernameEdit.setClearButtonEnabled(True)

        self.passwordEdit = LineEdit()

        self.passwordEdit.setPlaceholderText('请输入密码')
        self.passwordEdit.setClearButtonEnabled(True)

        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.usernameEdit)
        self.viewLayout.addWidget(self.passwordEdit)

        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(350)


    def showMessage(window):
        w = RenameDialog(window)
        if w.exec():
            return True, w.usernameEdit.text(), w.passwordEdit.text()
        else:
            return False, None, None

class UsersWidgetHeader(SubtitleLabel):
    add_signal = pyqtSignal()
    edit_signal = pyqtSignal()
    delete_signal = pyqtSignal()
    update_signal = pyqtSignal()
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(60)
        self.hLayout = QHBoxLayout(self)
        self.hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.add_btn = PrimaryPushButton('添加', self)
        self.add_btn.clicked.connect(lambda: self.add_signal.emit())
        self.add_btn.setFixedWidth(70)
        self.edit_btn = PrimaryPushButton('修改', self)
        self.edit_btn.clicked.connect(lambda: self.edit_signal.emit())
        self.edit_btn.setFixedWidth(70)
        self.delete_btn = PrimaryPushButton('删除', self)
        self.delete_btn.clicked.connect(lambda: self.delete_signal.emit())
        self.delete_btn.setFixedWidth(70)
        self.update_btn = PushButton('刷新', self)
        self.update_btn.clicked.connect(lambda: self.update_signal.emit())
        self.update_btn.setFixedWidth(70)
        self.hLayout.addWidget(self.add_btn)
        self.hLayout.addSpacing(5)
        self.hLayout.addWidget(self.edit_btn)
        self.hLayout.addSpacing(5)
        self.hLayout.addWidget(self.delete_btn)
        self.hLayout.addSpacing(5)
        self.hLayout.addWidget(self.update_btn)
        self.setLayout(self.hLayout)

class UsersWidget(SubtitleLabel):

    def __init__(self,text:str,parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.vLayout = QVBoxLayout(self)
        
        self.header = UsersWidgetHeader(self)
        self.header.add_signal.connect(self.handle_add_signal)
        self.header.edit_signal.connect(self.handle_edit_signal)
        self.header.delete_signal.connect(self.handle_delete_signal)
        self.header.update_signal.connect(self.update)
        

        self.table = TableWidget(self)
        self.vLayout.setContentsMargins(10,0,0,0)
        self.vLayout.setSpacing(0)
        self.vLayout.addWidget(self.header)
        self.vLayout.addWidget(self.table)
        self.setLayout(self.vLayout)

        # 启用边框并设置圆角
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)

        self.table.setWordWrap(False)
        self.table.setRowCount(3)
        self.table.setColumnCount(3)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 设置水平表头
        self.table.setHorizontalHeaderLabels(['id', 'username', 'password'])
        self.table.cellActivated

        self.items = []
        self.selectedItems = {'users':[]}
        self.manager = QNetworkAccessManager()
        self.update()

    def update(self):
        url = QUrl(gConfig['server']['spring']['url']+'/user/all')
        request = QNetworkRequest(url)
        self.manager.finished.connect(self.handle_get_all_respose)
        self.manager.get(request)

    def handle_get_all_respose(self,reply:QNetworkReply):
        res = json.loads(reply.readAll().data().decode())
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            self.items = res['data']
            self.table.setRowCount(len(self.items))
            for i, item in enumerate(self.items):
                self.table.setItem(i, 0, QTableWidgetItem(str(item['id'])))
                self.table.setItem(i, 1, QTableWidgetItem(item['username']))
                self.table.setItem(i, 2, QTableWidgetItem(item['password']))
        reply.deleteLater()
        self.manager.finished.disconnect(self.handle_get_all_respose)

    def handle_delete_respose(self,reply:QNetworkReply):
        res = json.loads(reply.readAll().data().decode())
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            InfoBar.success(
                title='删除成功',
                content="",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1000,
                parent=self.window()
            ).show()
        reply.deleteLater()
        self.manager.finished.disconnect(self.handle_delete_respose)
        self.update()

    def handle_add_respose(self,reply:QNetworkReply):
        res = json.loads(reply.readAll().data().decode())
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
        self.manager.finished.disconnect(self.handle_add_respose)
        self.update()

    def handle_add_signal(self):
        res,username,password = RenameDialog.showMessage(self.window())
        if res:
            json_data = json.dumps({'username':username,'password':password}).encode('utf-8')
            url = QUrl(gConfig['server']['spring']['url']+'/user/add')
            request = QNetworkRequest(url)
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
            self.manager.finished.connect(self.handle_add_respose)
            self.manager.post(request,json_data)

    def handle_edit_signal(self):
        pass
    def handle_delete_signal(self):
        self.selectedItems['users'].clear()
        selected_cells = self.table.selectedItems()
        for cell in selected_cells:
            row = cell.row()
            col = cell.column()
            if col==0:
                item = self.table.item(row, col)
                self.selectedItems['users'].append({'id':item.text()})
        json_data = json.dumps(self.selectedItems).encode('utf-8')
        url = QUrl(gConfig['server']['spring']['url']+'/user/delete')
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self.manager.finished.connect(self.handle_delete_respose)
        self.manager.post(request,json_data)

