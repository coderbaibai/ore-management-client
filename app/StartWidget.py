import asyncio
import sys
import tkinter as tk
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from qfluentwidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager,QNetworkReply
import sys
import os
from qasync import QEventLoop, asyncSlot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加模块所在目录到 sys.path
from app.main import Window
from config.GConfig import gConfig


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 设置窗口标题
        self.resize(700, 500)
        self.setMinimumSize(700, 500)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('大数据矿石治理系统')
        self.hLayout = QHBoxLayout(self)
        self.hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.hLayout.addStretch(1)

        self.vLayout = QVBoxLayout()
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.logo = QLabel(self)
        self.pixmap = QPixmap('./resources/icons/login.png')
        self.sPixmap = self.pixmap.scaled(300,200)
        self.logo.setPixmap(self.sPixmap)
        self.loginWidget = LoginWidget(self)
        self.vLayout.addStretch(1)
        self.vLayout.addWidget(self.logo)
        self.vLayout.addWidget(self.loginWidget)
        self.vLayout.addStretch(2)
        self.hLayout.addLayout(self.vLayout)

        self.hLayout.addStretch(1)
        self.w = Window()
        self.setLayout(self.hLayout)
        self.loginWidget.change_signal.connect(self.change)

    def change(self):
        self.hide()
        self.w.show()

    

class LoginWidget(QWidget):
    change_signal = pyqtSignal()
    def __init__(self,parent):
        super().__init__(parent)
        self.initUI()

    def initUI(self):

        self.manager = QNetworkAccessManager()
        # 创建布局
        layout = QVBoxLayout()
        self.setFixedSize(300,200)

        # 用户名标签和输入框
        self.username_label = QLabel('用户名:')
        self.username_input = LineEdit(self)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # 密码标签和输入框
        self.password_label = QLabel('密码:')
        self.password_input = LineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)  # 设置密码输入模式
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # 登录按钮
        self.login_button = PrimaryPushButton('登录', self)
        self.login_button.clicked.connect(self.on_login)  # 绑定点击事件
        layout.addWidget(self.login_button)

        # 设置布局
        self.setLayout(layout)

    def on_login(self):
        # 获取输入的用户名和密码
        username = self.username_input.text()
        password = self.password_input.text()


        # 准备 POST 数据
        post_data = {
            "username": username,
            "password": password
        }

        # 转换为JSON字符串并编码为字节
        json_data = json.dumps(post_data).encode('utf-8')


        # 设置请求头
        url = QUrl(gConfig['server']['spring']['url']+'/user/login')
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        # 发送 POST 请求
        self.manager.finished.connect(self.handle_response)
        self.manager.post(request, json_data)
    
    def handle_response(self,reply):
        # 输出错误信息
        error = reply.error()
        if error != QNetworkReply.NoError:
            print(f"❗ Error {error}: {reply.errorString()}")
        else:
            print("✅ Response:", reply.readAll().data().decode())
            self.hide()
            self.change_signal.emit()
        
        reply.deleteLater()
        
async def main():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    w = LoginWindow()
    w.show()

    with loop:
        sys.exit(loop.run_forever())

        
if __name__ == '__main__':
    asyncio.run(main())