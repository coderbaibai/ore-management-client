import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加模块所在目录到 sys.path

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from models.ClientMainwindow import ClientMainWindow
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    window.resize(800,600)
    clientMain = ClientMainWindow(parent=window)
    layout = QGridLayout()
    layout.addWidget(clientMain, 0, 0)  # 将子组件放在网格的 (0, 0) 位置
    layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
    layout.setSpacing(0)  # 移除间距
    window.setLayout(layout)
    window.setMinimumWidth(500)
    window.show()
    sys.exit(app.exec_())