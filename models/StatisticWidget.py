import json
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BodyLabel, Pivot, ComboBox, StrongBodyLabel, TableWidget,
                            PrimaryPushButton, PushButton, InfoBar, InfoBarPosition,CaptionLabel,RoundMenu,Action,Dialog,LineEdit,MessageBoxBase)
from qfluentwidgets import FluentIcon as FIF

from models.FilesWidgetHeader import FilesWidgetHeader
from utils.S3Utils import s3Utils
from utils.TypeUtils import FileType, UnitTranslator

from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager,QNetworkReply
from config.GConfig import gConfig,cookieJar

class StatisticWidget(QWidget):

    market_download_signal = pyqtSignal(int,str)

    def __init__(self,text:str,parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))

        # 数据
        self.marketsName = []
        self.marketsId = []
        self.manager = QNetworkAccessManager()
        self.manager.setCookieJar(cookieJar)

        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        # 顶部导航栏
        self.hLayout = QHBoxLayout()
        self.hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.runningStatisticButton = PrimaryPushButton('运行数据统计',parent=self)
        self.runningStatisticButton.clicked.connect(self.runningStatisticButtonClicked)
        self.datasetExportButton = PrimaryPushButton('数据集定制导出',parent=self)
        self.datasetExportButton.clicked.connect(self.datasetExportButtonClicked)
        self.preprocessButton = PrimaryPushButton('预处理调整',parent=self)
        self.preprocessButton.clicked.connect(self.preprocessButtonClicked)
        self.exceptionDetectButton = PrimaryPushButton('异常图片检测',parent=self)
        self.exceptionDetectButton.clicked.connect(self.exceptionDetectButtonClicked)

        self.comboBox = ComboBox()
        self.comboBox.setFixedWidth(150)
        self.comboBox.currentIndexChanged.connect(self.comboxChangeHandler)
        # 设置提示文本
        self.comboBox.setPlaceholderText("请选择数据市场")

        # 取消选中
        self.comboBox.setCurrentIndex(-1)
        self.isUpdate = False
        self.curMarketId = -1
        self.curMarketName = ""


        self.hLayout.addWidget(self.runningStatisticButton)
        self.hLayout.addWidget(self.datasetExportButton)
        self.hLayout.addWidget(self.preprocessButton)
        self.hLayout.addWidget(self.exceptionDetectButton)
        self.hLayout.addStretch()
        self.hLayout.addWidget(self.comboBox,alignment=Qt.AlignmentFlag.AlignRight)

        # 动态更新区域
        self.stackedArea = QStackedWidget(self)
        self.runningStatisticWidget = RunningStatisticWidget(self)
        self.datasetExportWidget = DatasetExportWidget(self)
        self.preprocessWidget = PreprocessWidget(self)
        self.exceptionDetectWidget = ExceptionDetectWidget(self)
        self.stackedArea.addWidget(self.runningStatisticWidget)
        self.stackedArea.addWidget(self.datasetExportWidget)
        self.stackedArea.addWidget(self.preprocessWidget)
        self.stackedArea.addWidget(self.exceptionDetectWidget)

        self.vLayout.addLayout(self.hLayout)
        self.vLayout.addWidget(self.stackedArea)

    def runningStatisticButtonClicked(self):
        self.stackedArea.setCurrentIndex(0)

    def datasetExportButtonClicked(self):
        self.stackedArea.setCurrentIndex(1)

    def preprocessButtonClicked(self):
        self.stackedArea.setCurrentIndex(2)
        
    def exceptionDetectButtonClicked(self):
        self.stackedArea.setCurrentIndex(3)
    
    def updateMarkets(self):
        url = QUrl(gConfig['server']['spring']['url']+'/market/current')
        request = QNetworkRequest(url)
        self.manager.finished.connect(self.handle_get_market_respose)
        self.manager.get(request)

    def handle_get_market_respose(self,reply:QNetworkReply):
        self.manager.finished.disconnect()
        res = json.loads(reply.readAll().data().decode())
        if 'code' not in res:
            print(f"❗ Error Code: {res['status']}\n")
            print(f"❗ Error msg: {res['error']}")
            return
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            self.marketsName = [dic['name'] for dic in res['data']['markets']]
            self.marketsId = [dic['id'] for dic in res['data']['markets']]
            self.comboBox.clear()
            self.isUpdate = True
            self.comboBox.addItems(self.marketsName)
            self.comboBox.setCurrentIndex(-1)
        reply.deleteLater()

    def comboxChangeHandler(self,index):
        if self.isUpdate:
            self.isUpdate = False
            return
        if index == -1:
            return
        InfoBar.info(
            title='正在下载',
            content="可在传输页面查看进度",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        ).show()
        self.curMarketId = self.marketsId[index]
        self.curMarketName = self.marketsName[index]
        self.market_download_signal.emit(self.marketsId[index],self.marketsName[index])
    
    def showEvent(self, event):
        super().showEvent(event)
        self.updateMarkets()

    def process(self,marketId,marketName):
        if marketId != self.curMarketId:
            return
        pass


class RunningStatisticWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        # 子导航栏
        pivot = Pivot()
        
        # 添加标签项
        pivot.addItem(routeKey="sizeDistrubution", text="物料大小分布", onClick=lambda: self.stackedArea.setCurrentIndex(0))
        pivot.addItem(routeKey="electricDistrubution", text="电流电压分布", onClick=lambda: self.stackedArea.setCurrentIndex(1))
        pivot.addItem(routeKey="numberDistrubution", text="物料个数统计", onClick=lambda: self.stackedArea.setCurrentIndex(2))
        pivot.setCurrentItem("sizeDistrubution")
        pivot.setFixedSize(300,100)
        self.vLayout.addWidget(pivot)

        # 动态更新区域
        self.stackedArea = QStackedWidget(self)
        self.sizeDistrubution = SizeDistrubution(self)
        self.electricDistrubution = ElectricDistrubution(self)
        self.numberDistrubution = NumberDistrubution(self)
        self.stackedArea.addWidget(self.sizeDistrubution)
        self.stackedArea.addWidget(self.electricDistrubution)
        self.stackedArea.addWidget(self.numberDistrubution)
        self.vLayout.addWidget(self.stackedArea)

class SizeDistrubution(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.title = StrongBodyLabel("物料大小分布统计",self)
        self.placeHolder = StrongBodyLabel("物料大小分布图表将显示在这里",self)
        self.placeHolder.setFixedHeight(250)
        self.placeHolder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeHolder.setStyleSheet("background-color: #E5F9E9;")

        self.table = TableWidget(self)
        # 启用边框并设置圆角
        self.table.setBorderVisible(False)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setRowCount(4)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['尺寸范围(mm)', '数量', '百分比'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.tableInfos = [
            ['0-10', '1250', '25%'],
            ['10-20', '1850','37%'],
            ['20-30', '1200','24%'],
            ['30以上', '700','14%'],
        ]
        for i, tableInfo in enumerate(self.tableInfos):
            for j in range(3):
                self.table.setItem(i, j, QTableWidgetItem(tableInfo[j]))

        self.vLayout.addWidget(self.title)
        self.vLayout.addWidget(self.placeHolder)
        self.vLayout.addStretch()
        self.vLayout.addWidget(self.table)

class ElectricDistrubution(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.title = StrongBodyLabel("电流电压分布统计",self)
        self.placeHolder = StrongBodyLabel("电流电压分布图表将显示在这里",self)
        self.placeHolder.setFixedHeight(250)
        self.placeHolder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeHolder.setStyleSheet("background-color: #E5F9E9;")

        self.table = TableWidget(self)
        # 启用边框并设置圆角
        self.table.setBorderVisible(False)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setRowCount(4)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['电流范围(A)', '电压范围(V)', '样本数量', '百分比'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.tableInfos = [
            ['0-50', '220-240', '850', '17%'],
            ['50-100', '220-240', '1200', '24%'],
            ['100-150', '220-240', '1750', '35%'],
            ['150以上', '220-240', '1200', '24%'],
        ]
        for i, tableInfo in enumerate(self.tableInfos):
            for j in range(4):
                self.table.setItem(i, j, QTableWidgetItem(tableInfo[j]))

        self.vLayout.addWidget(self.title)
        self.vLayout.addWidget(self.placeHolder)
        self.vLayout.addStretch()
        self.vLayout.addWidget(self.table)

class NumberDistrubution(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.title = StrongBodyLabel("物料个数统计",self)
        self.placeHolder = StrongBodyLabel("物料类别统计图表将显示在这里",self)
        self.placeHolder.setFixedHeight(250)
        self.placeHolder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeHolder.setStyleSheet("background-color: #E5F9E9;")

        self.table = TableWidget(self)
        # 启用边框并设置圆角
        self.table.setBorderVisible(False)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setRowCount(4)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['物料类别', '数量', '百分比'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.tableInfos = [
            ['A类矿石', '2500', '50%'],
            ['B类矿石', '1500', '30%'],
            ['C类矿石',  '750', '15%'],
            ['D类矿石',  '250', '5%'],
        ]
        for i, tableInfo in enumerate(self.tableInfos):
            for j in range(3):
                self.table.setItem(i, j, QTableWidgetItem(tableInfo[j]))

        self.vLayout.addWidget(self.title)
        self.vLayout.addWidget(self.placeHolder)
        self.vLayout.addStretch()
        self.vLayout.addWidget(self.table)

class DatasetExportWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.title = StrongBodyLabel("数据集定制及导出",self)
        self.info = BodyLabel("按照自定义条件生成符合下游训练的矿石数据集")
        self.hLayouts = []
        self.vLayout.addWidget(self.title)
        self.vLayout.addWidget(self.info)
        
        hLayout = QHBoxLayout()
        hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.elecCurRangeLabel = CaptionLabel("电流范围(A)",self)
        self.elecVolRangeLabel = CaptionLabel("电压范围(V)",self)
        self.sizeRangeLabel = CaptionLabel("物料尺寸范围(mm)",self)
        self.aNumberRangeLabel = CaptionLabel("A类矿石数量",self)
        hLayout.addWidget(self.elecCurRangeLabel)
        hLayout.addStretch(21)
        hLayout.addWidget(self.elecVolRangeLabel)
        hLayout.addStretch(21)
        hLayout.addWidget(self.sizeRangeLabel)
        hLayout.addStretch(17)
        hLayout.addWidget(self.aNumberRangeLabel)
        hLayout.addStretch(5)
        self.hLayouts.append(hLayout)

        hLayout = QHBoxLayout()
        hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.elecCurMinInput = LineEdit(self)
        self.elecCurMinInput.setPlaceholderText("最小值")
        self.elecCurMaxInput = LineEdit(self)
        self.elecCurMaxInput.setPlaceholderText("最大值")
        self.elecVolMinInput = LineEdit(self)
        self.elecVolMinInput.setPlaceholderText("最小值")
        self.elecVolMaxInput = LineEdit(self)
        self.elecVolMaxInput.setPlaceholderText("最大值")
        self.sizeMinInput = LineEdit(self)
        self.sizeMinInput.setPlaceholderText("最小值")
        self.sizeMaxInput = LineEdit(self)
        self.sizeMaxInput.setPlaceholderText("最大值")
        self.aNumberInput = LineEdit(self)
        self.aNumberInput.setPlaceholderText("需要的数量")
        hLayout.addWidget(self.elecCurMinInput)
        hLayout.addWidget(self.elecCurMaxInput)
        hLayout.addWidget(self.elecVolMinInput)
        hLayout.addWidget(self.elecVolMaxInput)
        hLayout.addWidget(self.sizeMinInput)
        hLayout.addWidget(self.sizeMaxInput)
        hLayout.addWidget(self.aNumberInput)
        self.hLayouts.append(hLayout)

        hLayout = QHBoxLayout()
        hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.bNumberRangeLabel = CaptionLabel("B类矿石数量",self)
        self.cNumberRangeLabel = CaptionLabel("C类矿石数量",self)
        self.dNumberRangeLabel = CaptionLabel("D类矿石数量",self)
        self.fomotLabel = CaptionLabel("导出格式",self)
        # hLayout.addStretch()
        hLayout.addWidget(self.bNumberRangeLabel)
        hLayout.addStretch(10)
        hLayout.addWidget(self.cNumberRangeLabel)
        hLayout.addStretch(10)
        hLayout.addWidget(self.dNumberRangeLabel)
        hLayout.addStretch(10)
        hLayout.addWidget(self.fomotLabel)
        hLayout.addStretch(11)
        self.hLayouts.append(hLayout)

        hLayout = QHBoxLayout()
        hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.bNumberInput = LineEdit(self)
        self.bNumberInput.setPlaceholderText("需要的数量")
        self.cNumberInput = LineEdit(self)
        self.cNumberInput.setPlaceholderText("需要的数量")
        self.dNumberInput = LineEdit(self)
        self.dNumberInput.setPlaceholderText("需要的数量")
        self.fomotInput = LineEdit(self)
        self.fomotInput.setPlaceholderText("请输入格式")
        hLayout.addWidget(self.bNumberInput)
        hLayout.addWidget(self.cNumberInput)
        hLayout.addWidget(self.dNumberInput)
        hLayout.addWidget(self.fomotInput)
        self.hLayouts.append(hLayout)

        hLayout = QHBoxLayout()
        hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.genButton = PrimaryPushButton("生成数据集",self)
        self.previewButton = PushButton("预览数据集",self)
        hLayout.addWidget(self.genButton)
        hLayout.addWidget(self.previewButton)
        self.hLayouts.append(hLayout)

        for layout in self.hLayouts:
            self.vLayout.addLayout(layout)



class PreprocessWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.placeHolder = QLabel("PreprocessWidget",self)
        self.placeHolder.setFixedHeight(300)
        self.vLayout.addWidget(self.placeHolder)

class ExceptionDetectWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.placeHolder = QLabel("ExceptionDetectWidget",self)
        self.placeHolder.setFixedHeight(300)
        self.vLayout.addWidget(self.placeHolder)