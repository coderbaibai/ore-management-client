from functools import partial
import json
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BodyLabel, InfoBar, ComboBox, StrongBodyLabel, TableWidget,
                            PrimaryPushButton, PushButton, SubtitleLabel, InfoBarPosition,CaptionLabel,RoundMenu,Action,Dialog,LineEdit,MessageBoxBase)
from qfluentwidgets import FluentIcon as FIF

from views.FilesWidgetHeader import FilesWidgetHeader
from OreUtils.S3Utils import s3Utils
from OreUtils.TypeUtils import FileType, UnitTranslator

from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager,QNetworkReply
from config.GConfig import gConfig,cookieJar
from OreUtils.imgprocessor.main import main
from PyQt5.QtChart import (QChartView, QChart, QBarSeries, QBarSet, 
                            QLegend, QBarCategoryAxis, QValueAxis)

class NewMarketDialog(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent):
        super().__init__(parent)

        self.viewLayout.setContentsMargins(10,10,10,10)
        self.viewLayout.setSpacing(0)
        
        self.titleLabel = SubtitleLabel('新建数据市场')

        self.nameLineEdit = LineEdit(self)
        self.nameLineEdit.setPlaceholderText("请输入数据市场名称")

        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameLineEdit)

        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(350)

class ExportWidget(QWidget):
    def __init__(self,text:str,parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.manager = QNetworkAccessManager()
        self.manager.setCookieJar(cookieJar)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.title = StrongBodyLabel("数据集定制及导出",self)
        self.info = BodyLabel("按照自定义条件生成符合下游训练的矿石数据集")
        self.hLayouts = []
        self.vLayout.addWidget(self.title)
        self.vLayout.addWidget(self.info)
        
        self.hLayout = QHBoxLayout()
        self.hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.vLayout.addLayout(self.hLayout)
        self.leftPlaceHolder = QWidget(self)
        self.rightPlaceHolder = QWidget(self)
        self.hLayout.addWidget(self.leftPlaceHolder,1)
        self.hLayout.addWidget(self.rightPlaceHolder,3)

        leftLayout = QVBoxLayout(self.leftPlaceHolder)
        leftLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.leftPlaceHolder.setLayout(leftLayout)

        leftLayout.addWidget(CaptionLabel("电流范围(mA)",self.leftPlaceHolder))
        tmpLayout = QHBoxLayout()
        self.elecCurMinInput = LineEdit(self.leftPlaceHolder)
        self.elecCurMinInput.setPlaceholderText("最小值")
        self.elecCurMaxInput = LineEdit(self.leftPlaceHolder)
        self.elecCurMaxInput.setPlaceholderText("最大值")
        tmpLayout.addWidget(self.elecCurMinInput)
        tmpLayout.addWidget(self.elecCurMaxInput)
        leftLayout.addLayout(tmpLayout)

        leftLayout.addWidget(CaptionLabel("电压范围(V)",self.leftPlaceHolder))
        tmpLayout = QHBoxLayout()
        self.elecVolMinInput = LineEdit(self.leftPlaceHolder)
        self.elecVolMinInput.setPlaceholderText("最小值")
        self.elecVolMaxInput = LineEdit(self.leftPlaceHolder)
        self.elecVolMaxInput.setPlaceholderText("最大值")
        tmpLayout.addWidget(self.elecVolMinInput)
        tmpLayout.addWidget(self.elecVolMaxInput)
        leftLayout.addLayout(tmpLayout)

        leftLayout.addWidget(CaptionLabel("物料尺寸范围(mm)",self.leftPlaceHolder))
        tmpLayout = QHBoxLayout()
        self.sizeMinInput = LineEdit(self.leftPlaceHolder)
        self.sizeMinInput.setPlaceholderText("最小值")
        self.sizeMaxInput = LineEdit(self.leftPlaceHolder)
        self.sizeMaxInput.setPlaceholderText("最大值")
        tmpLayout.addWidget(self.sizeMinInput)
        tmpLayout.addWidget(self.sizeMaxInput)
        leftLayout.addLayout(tmpLayout)

        tmpLayout = QHBoxLayout()
        self.filterButton = PushButton("筛选",self)
        self.filterButton.clicked.connect(self.on_filter_button_click)
        self.genButton = PrimaryPushButton("生成数据集",self)
        self.genButton.clicked.connect(self.on_gen_button_click)
        tmpLayout.addWidget(self.filterButton)
        tmpLayout.addWidget(self.genButton)
        leftLayout.addLayout(tmpLayout)

        self.conclusion =  StrongBodyLabel(self.leftPlaceHolder)
        leftLayout.addWidget(self.conclusion)

        self.table = TableWidget(self.rightPlaceHolder)
        # 启用边框并设置圆角
        self.table.setBorderVisible(False)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['压缩包ID', '种类','主体大小','电流','电压', '总量','异常数量'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.table.itemSelectionChanged.connect(self.tableSelectionChanged)

        self.cntTable:dict = {}
        self.ids:list[int] = []

        self.packages:list = []
        rightLayout = QVBoxLayout(self.rightPlaceHolder)
        self.rightPlaceHolder.setLayout(rightLayout)
        rightLayout.addWidget(self.table)


    def showEvent(self, event):
        super().showEvent(event)
        self.updatePackages()
    
    def updatePackages(self):
        self.cntTable = {}
        self.ids = []
        self.table.clear()
        self.table.clearSelection()
        url = QUrl(gConfig['server']['spring']['url']+'/package/all')
        request = QNetworkRequest(url)
        reply =  self.manager.get(request)
        reply.finished.connect(lambda: self.package_get_response(reply=reply))

    def package_get_response(self,reply:QNetworkReply):
        res = json.loads(reply.readAll().data().decode())
        reply.deleteLater()
        if 'code' not in res:
            print(f"❗ Error Code: {res['status']}\n")
            print(f"❗ Error msg: {res['error']}")
            return
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            self.packages = res['data']['packages']
            for i in range(len(self.packages)):
                if isinstance(self.packages[i]['anomalyList'],str):
                    self.packages[i]['anomalyList'] = self.packages[i]['anomalyList'].split(',')
                if isinstance(self.packages[i]['current'],str):
                    self.packages[i]['current'] = float(self.packages[i]['current'])
                if isinstance(self.packages[i]['voltage'],str):
                    self.packages[i]['voltage'] = float(self.packages[i]['voltage'])
            self.filterPackages()
            
    def showPackages(self):
        self.table.setRowCount(len(self.packages))
        for i in range(len(self.packages)):
            aCnt = 0
            if isinstance(self.packages[i]['anomalyList'],list):
                aCnt = len(self.packages[i]['anomalyList'])
            self.table.setItem(i, 0, QTableWidgetItem(str(self.packages[i]['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(self.packages[i]['cls']))
            self.table.setItem(i, 2, QTableWidgetItem(str(self.packages[i]['mainSize'])))
            self.table.setItem(i, 3, QTableWidgetItem(str(self.packages[i]['current'])))
            self.table.setItem(i, 4, QTableWidgetItem(str(self.packages[i]['voltage'])))
            self.table.setItem(i, 5, QTableWidgetItem(str(self.packages[i]['cnt'])))
            self.table.setItem(i, 6, QTableWidgetItem(str(aCnt)))

    def filterPackages(self):
        # 获取输入的电流范围
        elecCurMin = float("-inf" if self.elecCurMinInput.text()=="" else self.elecCurMinInput.text())
        elecCurMax = float("inf" if self.elecCurMaxInput.text()=="" else self.elecCurMaxInput.text())
        # 获取输入的电压范围
        elecVolMin = float("-inf" if self.elecVolMinInput.text()=="" else self.elecVolMinInput.text())
        elecVolMax = float("inf" if self.elecVolMaxInput.text()=="" else self.elecVolMaxInput.text())
        # 获取输入的物料尺寸范围
        sizeMin = float("-inf" if self.sizeMinInput.text()=="" else self.sizeMinInput.text())
        sizeMax = float("inf" if self.sizeMaxInput.text()=="" else self.sizeMaxInput.text())
        print(f"筛选条件: 电流范围({elecCurMin}, {elecCurMax}), 电压范围({elecVolMin}, {elecVolMax}), 物料尺寸范围({sizeMin}, {sizeMax})")

        total = 0
        self.table.clear()
        for i in range(len(self.packages)):
            if elecCurMin <= self.packages[i]['current'] <= elecCurMax and \
                elecVolMin <= self.packages[i]['voltage'] <= elecVolMax and \
                sizeMin <= self.packages[i]['mainSize'] <= sizeMax:

                total += 1

        self.table.setRowCount(total)
        self.table.setHorizontalHeaderLabels(['压缩包ID', '种类','主体大小(cm)','电流(mA)','电压(V)', '总量','异常数量'])

        curIndex = 0
        for i in range(len(self.packages)):
            if elecCurMin <= self.packages[i]['current'] <= elecCurMax and \
                elecVolMin <= self.packages[i]['voltage'] <= elecVolMax and \
                sizeMin <= self.packages[i]['mainSize'] <= sizeMax:

                aCnt = 0
                if isinstance(self.packages[i]['anomalyList'],list):
                    aCnt = len(self.packages[i]['anomalyList'])
                self.table.setItem(curIndex, 0, QTableWidgetItem(str(self.packages[i]['id'])))
                self.table.setItem(curIndex, 1, QTableWidgetItem(self.packages[i]['cls']))
                self.table.setItem(curIndex, 2, QTableWidgetItem(str(self.packages[i]['mainSize'])))
                self.table.setItem(curIndex, 3, QTableWidgetItem(str(self.packages[i]['current'])))
                self.table.setItem(curIndex, 4, QTableWidgetItem(str(self.packages[i]['voltage'])))
                self.table.setItem(curIndex, 5, QTableWidgetItem(str(self.packages[i]['cnt'])))
                self.table.setItem(curIndex, 6, QTableWidgetItem(str(aCnt)))
                curIndex += 1 
        
        
    def tableSelectionChanged(self):
        # 获取所有选中的行
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        print("选中的行:", selected_rows)
        self.cntTable = {}
        self.ids = []
        for row in selected_rows:
            if self.table.item(row,1).text() not in self.cntTable:
                self.cntTable[self.table.item(row,1).text()] = 0
            self.cntTable[self.table.item(row,1).text()] += int(self.table.item(row,2).text())
            self.ids.append(str(self.table.item(row,0).text()))
        self.conclusion.setText(f"当前选中: {self.cntTable}")

    def on_filter_button_click(self):
        self.cntTable = {}
        self.ids = []
        self.filterPackages()
    
    def on_gen_button_click(self):
        dialog = NewMarketDialog(self.window())
        if dialog.exec():
            print(dialog.nameLineEdit.text())
            data_to_post = {}
            data_to_post['marketName'] = dialog.nameLineEdit.text()
            data_to_post['ids'] = self.ids
            # 转换为JSON字符串并编码为字节
            json_data = json.dumps(data_to_post).encode('utf-8')

            url = QUrl(gConfig['server']['spring']['url']+'/market/new')
            request = QNetworkRequest(url)
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

            reply = self.manager.post(request, json_data)
            reply.finished.connect(lambda: self.on_gen_response(reply=reply))
    def on_gen_response(self,reply:QNetworkReply):
        res = json.loads(reply.readAll().data().decode())
        reply.deleteLater()
        if 'code' not in res:
            print(f"❗ Error Code: {res['status']}\n")
            print(f"❗ Error msg: {res['error']}")
            return
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            InfoBar.success(
                title='创建成功',
                content="可到数据市场界面查看",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1000,
                parent=self.window()
            ).show()