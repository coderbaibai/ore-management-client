# file_uploader.py MinIO Python SDK example
from threading import Thread
import threading
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加模块所在目录到 sys.path

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import *
from utils.S3Uploader import S3Uploader
from utils.S3Downloader import S3Downloader

from utils.S3Utils import s3_client

app = QApplication(sys.argv)
window = QWidget()
page_1 = QWidget(window)
page_2 = QWidget(window)

pb_up = ProgressBar(page_1)
btn_up_multi = PushButton(page_1)
pause_up = PushButton(page_1)
cancel_up = PushButton(page_1)

pb_down = ProgressBar(page_1)
btn_down_multi = PushButton(page_1)
pause_down = PushButton(page_1)
cancel_down = PushButton(page_1)

btn_shift = PushButton(window)
btn_show = PushButton(window)

info_table = QWidget(page_2)
info_layout = QVBoxLayout()
current_bucket = ''
current_path = ''
table_items = []

cur_page = 1

uploader = S3Uploader("python-test-bucket","cloud_temp_1GB.txt","/home/bhx/tmp/temp_1GB.txt")
downloader = S3Downloader("python-test-bucket","cloud_temp_1GB.txt","/home/bhx/tmp/download_temp_1GB.txt")


def clear_layout(target):
    """
    清空布局中的所有子控件
    """
    while target.count():  # 检查布局中是否还有控件
        item = target.takeAt(0)  # 从布局中取出第一个控件项
        widget = item.widget()  # 获取控件
        if widget is not None:
            widget.deleteLater()  # 删除控件（延迟删除，防止立即崩溃）
        else:
            # 如果是嵌套布局，需要递归处理
            sub_layout = item.layout()
            if sub_layout is not None:
                clear_sub_layout(sub_layout)


def clear_sub_layout(target):
    """
    递归清空嵌套布局
    """
    while target.count():
        item = target.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            sub_layout = item.layout()
            if sub_layout is not None:
                clear_sub_layout(sub_layout)


class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = ''

    def setText(self, a0) -> None:
        super().setText(a0)
        self._name = a0

    def mousePressEvent(self, event):
        global current_bucket, current_path
        # 如果是在bucket阶段
        if (current_bucket == ''):
            current_bucket = self._name
        else:
            current_path = self._name

        newItems = []
        response = s3_client.list_objects_v2(
            Bucket=current_bucket,
            Prefix=current_path,
            Delimiter='/'
        )
        # 清空布局
        clear_layout(info_layout)

        if 'Contents' in response:
            for obj in response['Contents']:
                item = TableItem(info_table)
                item.setFileName(obj['Key'])
                item.setCreateDate(obj['LastModified'].strftime('%Y %m %H:%M:%S'))
                item.setMore("更多")
                info_layout.addWidget(item._main_window)
                newItems.append(item)

        if 'CommonPrefixes' in response:
            for common_prefix in response['CommonPrefixes']:
                item = TableItem(info_table)
                item.setFileName(common_prefix['Prefix'])
                item.setCreateDate('')
                item.setMore("更多")
                info_layout.addWidget(item._main_window)
                newItems.append(item)

        global table_items
        table_items = newItems

        for i in table_items:
            print(i._file_name.text())


class TableItem():
    def __init__(self, parent) -> None:
        self._main_window = QWidget(parent)
        self._layout = QHBoxLayout()

        self._file_name = ClickableLabel(self._main_window)
        self._create_date = QLabel(self._main_window)
        self._more = QLabel(self._main_window)

        self._file_name.setFixedWidth(300)
        self._create_date.setFixedWidth(200)
        self._more.setFixedWidth(200)

        self._file_name.mousePressEvent
        self._file_name.setCursor(Qt.CursorShape.PointingHandCursor)

        self._layout.addWidget(self._file_name)
        self._layout.addWidget(self._create_date)
        self._layout.addWidget(self._more)
        self._layout.setSpacing(50)

        self._main_window.setLayout(self._layout)

    def setFileName(self, fileName: str):
        self._file_name.setText(fileName)

    def setCreateDate(self, createDate: str):
        self._create_date.setText(createDate)

    def setMore(self, more: str):
        self._more.setText(more)

    # def clickFileName(self):


def async_upload_multi():

    up_thread = Thread(target=uploader.execute)
    up_thread.start()

def async_download_multi():
    up_thread = Thread(target=downloader.execute)
    up_thread.start()


def pause_up_clicked():
    uploader.stop()


def pause_down_clicked():
    downloader.stop()


def cancel_up_clicked():
    uploader.cancel()


def cancel_down_clicked():
    downloader.cancel()


def showWindow():
    window.setGeometry(100, 100, 800, 800)
    pb_up.setFixedSize(700, 5)
    pb_up.setRange(0, 100)
    pb_up.setFormat("%p%")
    pb_up.move(50, 20)
    btn_up_multi.setText("分片上传")
    btn_up_multi.move(300, 100)
    pause_up.setText("暂停上传")
    pause_up.move(450, 100)
    cancel_up.setText("取消上传")
    cancel_up.move(600, 100)
    btn_up_multi.clicked.connect(async_upload_multi)
    pause_up.clicked.connect(pause_up_clicked)
    cancel_up.clicked.connect(cancel_up_clicked)

    pb_down.setFixedSize(700, 5)
    pb_down.setRange(0, 100)
    pb_down.setFormat("%p%")
    pb_down.move(50, 220)
    btn_down_multi.setText("分片下载")
    btn_down_multi.move(300, 300)
    pause_down.setText("暂停下载")
    pause_down.move(450, 300)
    cancel_down.setText("取消下载")
    cancel_down.move(600, 300)
    btn_down_multi.clicked.connect(async_download_multi)
    pause_down.clicked.connect(pause_down_clicked)
    cancel_down.clicked.connect(cancel_down_clicked)

    info_table.setFixedSize(800, 500)
    info_table.move(50, 50)
    info_table.setLayout(info_layout)
    # info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    page_1.setGeometry(0, 0, 800, 600)
    page_2.setGeometry(0, 0, 800, 600)
    page_2.setVisible(False)

    btn_shift.move(350, 700)
    btn_shift.setText("切换")
    btn_shift.clicked.connect(change_page)
    btn_show.move(500, 700)
    btn_show.setText("展示")
    btn_show.clicked.connect(show_buckets)

    window.setWindowTitle("PyQt5")
    window.show()


def show_buckets():
    buckets = s3_client.list_buckets()['Buckets']
    for bucket in buckets:
        item = TableItem(info_table)
        item.setFileName(bucket['Name'])
        item.setCreateDate(bucket['CreationDate'].strftime('%Y %m %H:%M:%S'))
        item.setMore("更多")
        info_layout.addWidget(item._main_window)
        table_items.append(item)


def change_page():
    global cur_page
    if (cur_page == 1):
        page_1.setVisible(False)
        page_2.setVisible(True)
        cur_page = 2
    else:
        page_2.setVisible(False)
        page_1.setVisible(True)
        cur_page = 1


def main():
    showWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()