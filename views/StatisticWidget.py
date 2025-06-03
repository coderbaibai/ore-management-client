from functools import partial
import json
import os
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor
from qfluentwidgets import (BodyLabel, Pivot, ComboBox, StrongBodyLabel, TableWidget,
                            PrimaryPushButton, PushButton, InfoBar, InfoBarPosition,CaptionLabel,RoundMenu,Action,Dialog,LineEdit,MessageBoxBase)
from qfluentwidgets import FluentIcon as FIF

from views.FilesWidgetHeader import FilesWidgetHeader
from OreUtils.S3Utils import s3Utils
from OreUtils.TypeUtils import FileType, UnitTranslator

from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager,QNetworkReply
from config.GConfig import gConfig,cookieJar
from OreUtils.imgprocessor.main import main
from PyQt5.QtChart import (QChartView, QChart, QBarSeries, QBarSet, 
                            QLegend, QBarCategoryAxis, QValueAxis)

class WorkerThread(QThread):
    # 定义一个信号，用于任务完成时传递结果
    finished = pyqtSignal(dict)
    error = pyqtSignal(dict)

    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(result)


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

        self.entries: list[os.DirEntry[str]] = []
        self.curIndex: int = 0
        self.path :str = ""

        self.sizeDict = {}
        self.currentDict = {}
        self.typeDict = {}

        self.sizeClassificationDict = {
            '0-10': lambda i: i<10 and i>=0,
            '10-20': lambda i:i<20 and i>=10,
            '20-30': lambda i:i<30 and i>=20,
            '30以上': lambda i:i>=30
        }

        self.currentClassificationDict = {
            '0-1.0': lambda i:i<1.0 and i>=0,
            '1.0-2.0': lambda i:i<2.0 and i>=1.0,
            '2.0-2.5': lambda i:i<2.5 and i>=2.0,
            '2.5以上': lambda i:i>=2.5
        }

        self.typeClassificationDict = {
            '煤矿': lambda cls:cls=='mei',
            '石矿': lambda cls:cls=='shi',
            '其他': lambda cls:cls!='mei' and cls!='shi'
        }

        for key in self.typeClassificationDict.keys():
            self.typeDict[key] = 0

        self.runningStatisticWidget.setClassificationDict(self.sizeClassificationDict,self.currentClassificationDict,self.typeClassificationDict)

        self.getReply = None
        

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
            self.clear()
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
            parent=self.window()
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
        self.path = gConfig['client']['download-path']+'/'+marketName+str(marketId)+'/'

        self.curIndex = 0
        self.entries = []
        print("process")
        # 清空数据
        self.sizeDict = {}
        self.currentDict = {}
        with os.scandir(self.path) as entries:
            for entry in entries:
                if entry.is_file():
                    self.entries.append(entry)
        self.processOnce()
                    
    def processOnce(self):
        if self.curIndex >= len(self.entries):
            print("数据市场处理完成")
            self.runningStatisticWidget.updateInfo(self.sizeDict,self.currentDict,self.typeDict)
            return
        url = QUrl(gConfig['server']['spring']['url']+'/package/target')
        query = QUrlQuery()
        query.addQueryItem("name", self.entries[self.curIndex].name)
        url.setQuery(query)
        request = QNetworkRequest(url)
        self.getReply = self.manager.get(request)
        handler = partial(self.handle_get_package_respose,zip_path=self.path+self.entries[self.curIndex].name)
        print("发送请求",id(self.getReply))
        self.getReply.finished.connect(lambda: handler())
        
    def handle_get_package_respose(self,zip_path):
        print("回调",id(self.getReply))
        res = json.loads(self.getReply.readAll().data().decode())
        if 'code' not in res:
            print(f"❗ Error Code: {res['status']}\n")
            print(f"❗ Error msg: {res['error']}")
            return
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            # 处理数据
            if res['data']['valid']:
                print("成功查找数据包")
                self.addInfoIntoStatistic(res['data']['zipPackage'])
                # 处理下一个请求
                self.curIndex += 1
                # QTimer.singleShot(2000, self.processOnce)
                self.getReply.deleteLater()
                QTimer.singleShot(10,self.processOnce)
            else:
                print("数据包不存在")
                self.worker = WorkerThread(main, zip_path, 0,200,20)
                handler = partial(self.on_task_finished,zip_path=zip_path)
                self.worker.finished.connect(handler)
                self.worker.error.connect(handler)
                self.worker.start()
        
        
    def on_task_finished(self,post_data:dict,zip_path:str):
        self.getReply.deleteLater()
        post_data['name'] = os.path.basename(zip_path)
        post_data['distribution'] = ",".join(map(str, post_data['distribution']))
        post_data['anomalyList'] = ",".join(map(str, post_data['anomalyList']))
        json_data = json.dumps(post_data).encode('utf-8')
        url = QUrl(gConfig['server']['spring']['url']+'/package/add')
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        # 发送 POST 请求
        new_reply = self.manager.post(request, json_data)
        new_reply.finished.connect(lambda: self.handle_set_package_respose(new_reply))

        self.addInfoIntoStatistic(post_data)
        # 处理下一个请求
        self.curIndex += 1
        QTimer.singleShot(500, self.processOnce)


    def handle_set_package_respose(self,reply:QNetworkReply):
        res = json.loads(reply.readAll().data().decode())
        if 'code' not in res:
            print(f"❗ Error Code: {res['status']}\n")
            print(f"❗ Error msg: {res['error']}")
            return
        if res['code'] == 0:
            print(f"❗ Error {res['msg']}")
        else:
            print("插入成功")
        reply.deleteLater()

    def addInfoIntoStatistic(self,info:dict):
        if isinstance(info['distribution'],str):
            info['distribution'] = map(int,info['distribution'].split(','))
        if isinstance(info['anomalyList'],str):
            info['anomalyList'] = map(int,info['anomalyList'].split(','))
        if isinstance(info['voltage'],str):
            info['voltage'] = float(info['voltage'])
        if isinstance(info['current'],str):
            info['current'] = float(info['current'])
        # 加入物料大小分布
        self.addSizeDict(info)
        # 加入电流电压分布
        self.addCurrentDict(info)
        # 加入物料种类分布
        self.addTypeDict(info)


    def addSizeDict(self,info:dict):
        if info['cls'] not in self.sizeDict:
            self.sizeDict[info['cls']] = {}
            for key in self.sizeClassificationDict.keys():
                self.sizeDict[info['cls']][key] = 0
        for index,cnt in enumerate(info['distribution']):
            for key,classifier in self.sizeClassificationDict.items():
                if classifier(index):
                    self.sizeDict[info['cls']][key] += cnt
                    break

    def addCurrentDict(self,info:dict):
        if info['cls'] not in self.currentDict:
            self.currentDict[info['cls']] = {}
            for key in self.currentClassificationDict.keys():
                self.currentDict[info['cls']][key] = 0
        for key,classifier in self.currentClassificationDict.items():
            if classifier(info['current']):
                self.currentDict[info['cls']][key] += info['cnt']
                break
    
    def addTypeDict(self,info:dict):
        for key,classifier in self.typeClassificationDict.items():
            if classifier(info['cls']):
                self.typeDict[key] += info['cnt']
                break
    
    def clear(self):
        self.sizeDict = {}
        self.currentDict = {}
        self.typeDict = {}
        for key in self.typeClassificationDict.keys():
            self.typeDict[key] = 0
        self.runningStatisticWidget.clear()


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

    def clear(self):
        self.sizeDistrubution.clear()
        self.electricDistrubution.clear()
        # self.numberDistrubution.clear()

    def setClassificationDict(self,sizeDict:dict,currentDict:dict,typeDict:dict):
        self.sizeDistrubution.setClassificationDict(sizeDict)
        self.electricDistrubution.setClassificationDict(currentDict)
        self.numberDistrubution.setClassificationDict(typeDict)

    def updateInfo(self,sizeDict:dict,currentDict:dict,typeDict:dict):
        self.sizeDistrubution.updateInfo(sizeDict)
        self.electricDistrubution.updateInfo(currentDict)
        self.numberDistrubution.updateInfo(typeDict)

class SizeDistrubution(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.title = StrongBodyLabel("物料大小分布统计",self)
        self.placeHolder = QWidget(self)
        self.placeHolder.setFixedHeight(270)
        tmpLayout = QVBoxLayout(self.placeHolder)
        tmpLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tmpLabel = StrongBodyLabel("物料大小分布图表将显示在这里",self.placeHolder)
        tmpLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tmpLayout.addWidget(tmpLabel)


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

        self.sizeClassificationDict: dict|None = None

        # self.createChart()

    def setClassificationDict(self,sizeDict:dict):
        self.sizeClassificationDict = sizeDict
        self.table.clearContents()
        self.table.setRowCount(len(self.sizeClassificationDict))
        self.table.setColumnCount(3)

    def updateInfo(self,sizeDict:dict):
        if self.sizeClassificationDict is None:
            return
        total = 0
        for index,key in enumerate(self.sizeClassificationDict.keys()):
            self.tableInfos[index][0] = key
            cnt = 0
            for inner_key in sizeDict.keys():
                cnt += sizeDict[inner_key][key]
            self.tableInfos[index][1] = cnt
            total += cnt
        for i in range(len(self.tableInfos)):
            self.tableInfos[i][2] = str(round(float(self.tableInfos[i][1])/total*100,2))+'%'
            self.tableInfos[i][1] = str(self.tableInfos[i][1])
        for i, tableInfo in enumerate(self.tableInfos):
            for j in range(3):
                self.table.setItem(i, j, QTableWidgetItem(tableInfo[j]))
        self.createChart(sizeDict)

    def createChart(self,sizeDict:dict|None = None):
        barSeries = QBarSeries()
        categories:list[str] = []
        maxValue = 0
        for key in self.sizeClassificationDict.keys():
            categories.append(key)
        for cls in sizeDict.keys():
            barSet = QBarSet(cls)
            for index,key in enumerate(self.sizeClassificationDict.keys()):
                barSet.append(sizeDict[cls].values())
            for i in sizeDict[cls].values():
                if i > maxValue:
                    maxValue = i
            barSeries.append(barSet)
        # barSet0 = QBarSet('Jane')
        # barSet1 = QBarSet('Jone')
        # barSet2 = QBarSet('Axel')
        # barSet3 = QBarSet('Mary')
        # barSet4 = QBarSet('Samantha')
        
        # barSet0.append([1, 2, 3, 4, 5, 6])
        # barSet1.append([5, 0, 0, 4, 0, 7])
        # barSet2.append([3, 5, 8, 13, 8, 5])
        # barSet3.append([5, 6, 7, 3, 4, 5])
        # barSet4.append([9, 7, 5, 3, 1, 2])
        
        # #条状图
        # barSeries = QBarSeries()
        # barSeries.append(barSet0)
        # barSeries.append(barSet1)
        # barSeries.append(barSet2)
        # barSeries.append(barSet3)
        # barSeries.append(barSet4)
        
        #创建图表
        chart = QChart()
        chart.addSeries(barSeries)
        chart.setTitle('矿石数量分布统计')
        chart.setAnimationOptions(QChart.SeriesAnimations) #设置成动画显示
        
        #设置横向坐标(X轴)
        # categories = ['一月', '二月', '三月', '四月', '五月', '六月']
        axisX = QBarCategoryAxis()
        axisX.append(categories)
        chart.addAxis(axisX, Qt.AlignBottom)
        barSeries.attachAxis(axisX)
        
        #设置纵向坐标(Y轴)
        axisY = QValueAxis()
        axisY.setRange(0, maxValue)
        axisY.setLabelFormat("%d")
        chart.addAxis(axisY, Qt.AlignLeft)
        barSeries.attachAxis(axisY)
        
        #图例属性
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chart.setMargins(QMargins(0, 0, 0, 0))  # 移除图表边距
        chart.layout().setContentsMargins(0, 0, 0, 0)  # 移除图表布局边距
        #图表视图
        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)
        chartView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.clear_layout()

        layout = self.placeHolder.layout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(chartView)

    def createHolder(self):
        self.clear_layout()
        tmpLabel = StrongBodyLabel("物料大小分布图表将显示在这里",self.placeHolder)
        tmpLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = self.placeHolder.layout()
        layout.addWidget(tmpLabel)

    def clear_layout(self):
        # 检查是否有布局
        if self.placeHolder.layout() is not None:
            # 删除布局中的所有子控件
            while self.placeHolder.layout().count():
                item = self.placeHolder.layout().takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()
    def clear(self):
        self.createHolder()
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['尺寸范围(mm)', '数量', '百分比'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        

class ElectricDistrubution(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.title = StrongBodyLabel("电流电压分布统计",self)

        self.placeHolder = QWidget(self)
        self.placeHolder.setFixedHeight(270)
        tmpLayout = QVBoxLayout(self.placeHolder)
        tmpLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tmpLabel = StrongBodyLabel("电流电压分布图表将显示在这里",self.placeHolder)
        tmpLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tmpLayout.addWidget(tmpLabel)

        self.table = TableWidget(self)
        # 启用边框并设置圆角
        self.table.setBorderVisible(False)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setRowCount(4)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['电流范围(mA)', '样本数量', '百分比'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.tableInfos = [
            ['0-10', '1250', '25%'],
            ['10-20', '1850','37%'],
            ['20-30', '1200','24%'],
            ['30以上', '700','14%'],
        ]

        self.vLayout.addWidget(self.title)
        self.vLayout.addWidget(self.placeHolder)
        self.vLayout.addStretch()
        self.vLayout.addWidget(self.table)
        
        self.currentClassificationDict: dict|None = None

    def setClassificationDict(self,currentDict:dict):
        self.currentClassificationDict = currentDict
        self.table.clearContents()
        self.table.setRowCount(len(self.currentClassificationDict))
        self.table.setColumnCount(3)

    def updateInfo(self,currentDict:dict):
        if self.currentClassificationDict is None:
            return
        total = 0
        for index,key in enumerate(self.currentClassificationDict.keys()):
            self.tableInfos[index][0] = key
            cnt = 0
            for inner_key in currentDict.keys():
                cnt += currentDict[inner_key][key]
            self.tableInfos[index][1] = cnt
            total += cnt
        for i in range(len(self.tableInfos)):
            self.tableInfos[i][2] = str(round(float(self.tableInfos[i][1])/total*100,2))+'%'
            self.tableInfos[i][1] = str(self.tableInfos[i][1])
        for i, tableInfo in enumerate(self.tableInfos):
            for j in range(3):
                self.table.setItem(i, j, QTableWidgetItem(tableInfo[j]))
        self.createChart(currentDict)
    def createChart(self,currentDict:dict|None = None):
        barSeries = QBarSeries()
        categories:list[str] = []
        maxValue = 0
        for key in self.currentClassificationDict.keys():
            categories.append(key)
        for cls in currentDict.keys():
            barSet = QBarSet(cls)
            for index,key in enumerate(self.currentClassificationDict.keys()):
                barSet.append(currentDict[cls].values())
            for i in currentDict[cls].values():
                if i > maxValue:
                    maxValue = i
            barSeries.append(barSet)
        # barSet0 = QBarSet('Jane')
        # barSet1 = QBarSet('Jone')
        # barSet2 = QBarSet('Axel')
        # barSet3 = QBarSet('Mary')
        # barSet4 = QBarSet('Samantha')
        
        # barSet0.append([1, 2, 3, 4, 5, 6])
        # barSet1.append([5, 0, 0, 4, 0, 7])
        # barSet2.append([3, 5, 8, 13, 8, 5])
        # barSet3.append([5, 6, 7, 3, 4, 5])
        # barSet4.append([9, 7, 5, 3, 1, 2])
        
        # #条状图
        # barSeries = QBarSeries()
        # barSeries.append(barSet0)
        # barSeries.append(barSet1)
        # barSeries.append(barSet2)
        # barSeries.append(barSet3)
        # barSeries.append(barSet4)
        
        #创建图表
        chart = QChart()
        chart.addSeries(barSeries)
        chart.setTitle('矿石数量分布统计')
        chart.setAnimationOptions(QChart.SeriesAnimations) #设置成动画显示
        
        #设置横向坐标(X轴)
        # categories = ['一月', '二月', '三月', '四月', '五月', '六月']
        axisX = QBarCategoryAxis()
        axisX.append(categories)
        chart.addAxis(axisX, Qt.AlignBottom)
        barSeries.attachAxis(axisX)
        
        #设置纵向坐标(Y轴)
        axisY = QValueAxis()
        axisY.setRange(0, maxValue)
        axisY.setLabelFormat("%d")
        chart.addAxis(axisY, Qt.AlignLeft)
        barSeries.attachAxis(axisY)
        
        #图例属性
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chart.setMargins(QMargins(0, 0, 0, 0))  # 移除图表边距
        chart.layout().setContentsMargins(0, 0, 0, 0)  # 移除图表布局边距
        #图表视图
        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)
        chartView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.clear_layout()

        layout = self.placeHolder.layout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(chartView)

    def createHolder(self):
        self.clear_layout()
        tmpLabel = StrongBodyLabel("电流电压分布图表将显示在这里",self.placeHolder)
        tmpLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = self.placeHolder.layout()
        layout.addWidget(tmpLabel)

    def clear_layout(self):
        # 检查是否有布局
        if self.placeHolder.layout() is not None:
            # 删除布局中的所有子控件
            while self.placeHolder.layout().count():
                item = self.placeHolder.layout().takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()

    def clear(self):
        self.createHolder()
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['电流范围(mA)', '样本数量', '百分比'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        
class NumberDistrubution(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        # 整体布局
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vLayout)

        self.title = StrongBodyLabel("物料个数统计",self)
        self.placeHolder = StrongBodyLabel("物料类别统计图表将显示在这里",self)
        self.placeHolder.setFixedHeight(270)
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

        self.typeClassificationDict: dict|None = None
    
    def setClassificationDict(self,typeDict:dict):
        self.typeClassificationDict = typeDict

    def updateInfo(self,typeDict:dict):
        if self.typeClassificationDict is None:
            return

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