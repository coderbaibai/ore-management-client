import csv
from datetime import datetime
import math
import os
import threading
from pathlib import Path
import boto3

from config.GConfig import gConfig
from peewee import SqliteDatabase, Model, IntegerField, TextField, AutoField
from PyQt5.QtCore import *
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager,QNetworkReply

from OreUtils.SqliteUtils import TransportRecord
from OreUtils.TypeUtils import FileType, StateType
from OreUtils.S3Utils import s3Utils

class S3Downloader():
    def __init__(self,id=None):
        self.id = id
        self.curSize = 0
        self.lastSize = 0
        self.canCalculateRate = False
        # 初始化客户端
        self.client  = boto3.client(
            's3',
            aws_access_key_id=gConfig['server']['minio']['id'],
            aws_secret_access_key=gConfig['server']['minio']['key'],
            endpoint_url=gConfig['server']['minio']['url']  # 配置区域
        )
        self.source = boto3.resource(
            's3',
            aws_access_key_id=gConfig['server']['minio']['id'],
            aws_secret_access_key=gConfig['server']['minio']['key'],
            endpoint_url=gConfig['server']['minio']['url']  # 配置区域
        )
        self.isFinished = False
        self.process = 0
        self.totalSize = 0
        self.mutexPause = threading.Lock()
        self.mutexProcess = threading.Lock()
        self.mutexFinished = threading.Lock()
        self.isPaused = False
    
    def get_process(self):
        self.mutexProcess.acquire_lock()
        ret = self.process
        self.mutexProcess.release_lock()
        return ret
    
    def get_file_size(self):
        return self.totalSize
    
    def get_id(self):
        return self.id
    
    def is_finished(self):
        res = False
        self.mutexFinished.acquire_lock()
        res = self.isFinished
        self.mutexFinished.release_lock()
        return res
    
    def get_delta(self):
        if self.canCalculateRate:
            res = self.curSize-self.lastSize
            self.lastSize = self.curSize
            return res
        else:
            return 0

    def stop(self):
        self.mutexPause.acquire_lock()
        self.isPaused = True
        self.mutexPause.release_lock()

    def start():
        pass

    def execute(self):
        pass

    def cancel(self):
        pass

class S3FileDownloader(S3Downloader):
    def __init__(self,bucket_name,cloud_path,local_path,id=None):
        super().__init__(id)
        self.bucketName = bucket_name
        self.cloudPath = cloud_path
        self.localPath = local_path
    
    def start(bucket,path,local,file_type=FileType.file) ->bool:
        # 检查重复下载
        if os.path.exists(local):
            return False
        res = list(TransportRecord.select().where(
            (TransportRecord.local == local) &
            (TransportRecord.bucket == bucket) &
            (TransportRecord.cloud == path) &
            (TransportRecord.finish == 0)
        ))
        if len(res) != 0:
            return False
        else:
            localPath = Path(local)
            size_local = s3Utils.getFileSize(bucket,path,file_type)
            TransportRecord.insert({
                'name' :localPath.name,
                'type' : file_type,
                'size' : size_local,
                'state' : StateType.download,
                'time' : datetime.now().strftime('%Y.%m.%d'),
                'local' : local,
                'bucket' : bucket,
                'cloud' : path,
                'finish' : 0
            }).execute()
            return True
        
    def execute(self):
        with open(self.localPath, 'a') as file:
            pass
        # 获取对象的总大小
        self.fileSize = self.client.head_object(Bucket=self.bucketName, Key=self.cloudPath)['ContentLength']
        part_size = int(self.fileSize / 100 + 1024)
        self.curSize = os.path.getsize(self.localPath)
        self.mutexPause.acquire_lock()
        self.isPaused = False
        self.mutexPause.release()
        with open(self.localPath, 'ab') as f:
            while True:
                # 获取锁
                self.mutexPause.acquire_lock()
                # 如果暂停
                if self.isPaused:
                    self.mutexPause.release()
                    break
                else:
                    self.mutexPause.release()
                # 如果完成
                if self.curSize >= self.fileSize:
                    self.mutexFinished.acquire_lock()
                    self.isFinished = True
                    self.mutexFinished.release_lock()
                    break
                # 使用 Range 头下载部分内容
                end = min(self.curSize + part_size - 1, self.fileSize - 1)
                response = self.client.get_object(Bucket=self.bucketName, Key=self.cloudPath,
                                                Range="bytes={0}-{1}".format(self.curSize, end))
                f.write(response['Body'].read())

                print("file_size:{0}".format(self.fileSize))
                print("bytes={0}-{1}".format(self.curSize, end))

                self.curSize = os.path.getsize(self.localPath)
                self.canCalculateRate = True

                self.mutexProcess.acquire_lock()
                if self.process != int(100 * self.curSize / self.fileSize):
                    self.process = int(100 * self.curSize / self.fileSize)
                self.mutexProcess.release_lock()

    def cancel(self):
        if os.path.exists(self.localPath):
            os.remove(self.localPath)

class S3MarketDownloader(S3Downloader):
    def __init__(self,marketId,marketItemList,marketName,totalSize,id=None):
        super().__init__(id)
        self.fileSize = totalSize
        self.marketId = marketId
        self.marketName = marketName
        self.marketItemList = marketItemList
        self.prefix = gConfig['client']['download-path']+'/'+self.marketName+str(self.marketId)+'/'
        

    def start(marketId,marketName,totalSize):
        marketPath = gConfig['client']['download-path']+'/'+marketName+str(marketId)
        if not os.path.exists(marketPath):
            os.makedirs(marketPath)
            print(f"目录已创建: {marketPath}")
        else:
            print(f"目录已存在: {marketPath}")

        res = list(TransportRecord.select().where(
            (TransportRecord.market_id == marketId) &
            (TransportRecord.finish == 0)
        ))
        if len(res) != 0:
            return False
        else:
            TransportRecord.insert({
                'name' :marketName,
                'type' : FileType.directory,
                'size' : totalSize,
                'state' : StateType.download,
                'time' : datetime.now().strftime('%Y.%m.%d'),
                'local' : marketPath,
                'bucket' : '-',
                'cloud' : '-',
                'finish' : 0,
                'market_id': marketId
            }).execute()
            return True
        
    def execute(self):
        self.curSize = 0
        for item in self.marketItemList:
            pathName = self.prefix + item['name'].replace("/", "_")
            with open(pathName, 'a') as file:
                pass
            itemSize = self.client.head_object(Bucket=item['bucketName'], Key=item['path'])['ContentLength']
            partSize = math.ceil(itemSize / 100)
            curItemSize = os.path.getsize(pathName)
            self.mutexPause.acquire_lock()
            self.isPaused = False
            self.mutexPause.release()
            with open(pathName, 'ab') as f:
                while True:
                    # 获取锁
                    self.mutexPause.acquire_lock()
                    # 如果暂停
                    if self.isPaused:
                        self.mutexPause.release()
                        break
                    else:
                        self.mutexPause.release()
                    # 如果完成
                    if curItemSize >= itemSize:
                        self.curSize = self.curSize + itemSize
                        f.flush()
                        break
                    # 使用 Range 头下载部分内容
                    end = min(curItemSize + partSize - 1, itemSize - 1)
                    response = self.client.get_object(Bucket=item['bucketName'], Key=item['path'],
                                                    Range="bytes={0}-{1}".format(curItemSize, end))
                    f.write(response['Body'].read())

                    # print("file_size:{0}".format(self.fileSize))
                    # print("bytes={0}-{1}".format(self.curSize, end))

                    curItemSize = end+1
                    self.canCalculateRate = True

                    self.mutexProcess.acquire_lock()
                    if self.process != int(100 * (self.curSize+curItemSize) / self.fileSize):
                        self.process = int(100 * (self.curSize+curItemSize) / self.fileSize)
                    self.mutexProcess.release_lock()
            self.mutexPause.acquire_lock()
            # 如果暂停
            if self.isPaused:
                self.mutexPause.release()
                self.curSize = 0
                return
            else:
                self.mutexPause.release()
        self.mutexFinished.acquire_lock()
        self.isFinished = True
        self.mutexFinished.release_lock()

    def cancel(self):
        pass