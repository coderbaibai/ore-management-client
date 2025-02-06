import csv
import datetime
import os
import threading
from pathlib import Path
import boto3

from config.GConfig import gConfig
from peewee import SqliteDatabase, Model, IntegerField, TextField, AutoField

from utils.SqliteUtils import TransportRecord
from utils.TypeUtils import FileType, StateType

class S3Downloader:
    def __init__(self,bucket_name,cloud_path,local_path,id=None):
        self.__bucket_name = bucket_name
        self.__cloud_path = cloud_path
        self.__local_path = local_path
        self.__id = id
        self.__isFinished = False
        self.__cur_size = 0
        self.__last_size = 0
        self.__can_calculate_rate = False
        # 初始化客户端
        self.__client  = boto3.client(
            's3',
            aws_access_key_id=gConfig['server']['id'],
            aws_secret_access_key=gConfig['server']['key'],
            endpoint_url=gConfig['server']['url']  # 配置区域
        )
        self.__source = boto3.resource(
            's3',
            aws_access_key_id=gConfig['server']['id'],
            aws_secret_access_key=gConfig['server']['key'],
            endpoint_url=gConfig['server']['url']  # 配置区域
        )
        # 初始化上传项目文件
        self.__process = 0
        self.__file_size = 0

        # 传输控制
        self.__mutex_pause = threading.Lock()
        self.__mutex_process = threading.Lock()
        self.__isPaused = False

    def get_process(self):
        self.__mutex_process.acquire_lock()
        ret = self.__process
        self.__mutex_process.release_lock()
        return ret

    def get_file_size(self):
        return self.__file_size
    
    def get_id(self):
        return self.__id
    
    def start(bucket,path,local) ->bool:
        # 检查重复上传
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
            TransportRecord.insert({
                'name' :localPath.name,
                'type' : FileType.file,
                'size' : os.stat(local).st_size,
                'state' : StateType.download,
                'time' : datetime.now().strftime('%Y.%m.%d'),
                'local' : local,
                'bucket' : bucket,
                'cloud' : path,
                'finish' : 0
            }).execute()
            return True
        
    def execute(self):
        with open(self.__local_path, 'a') as file:
            pass
        # 获取对象的总大小
        file_size = self.__client.head_object(Bucket=self.__bucket_name, Key=self.__cloud_path)['ContentLength']
        part_size = int(file_size / 100 + 1024)
        self.__cur_size = os.path.getsize(self.__local_path)
        self.__mutex_pause.acquire_lock()
        self.__isPaused = False
        self.__mutex_pause.release()
        with open(self.__local_path, 'ab') as f:
            while True:
                # 获取锁
                self.__mutex_pause.acquire_lock()
                # 如果暂停
                if self.__isPaused:
                    self.__mutex_pause.release()
                    break
                else:
                    self.__mutex_pause.release()
                # 如果完成
                if self.__cur_size >= file_size:
                    self.__isFinished = True
                    break
                # 使用 Range 头下载部分内容
                end = min(self.__cur_size + part_size - 1, file_size - 1)
                response = self.__client.get_object(Bucket=self.__bucket_name, Key=self.__cloud_path,
                                                Range="bytes={0}-{1}".format(self.__cur_size, end))
                f.write(response['Body'].read())

                print("file_size:{0}".format(file_size))
                print("bytes={0}-{1}".format(self.__cur_size, end))

                self.__cur_size = os.path.getsize(self.__local_path)
                self.__can_calculate_rate = True

                self.__mutex_process.acquire_lock()
                if self.__process != int(100 * self.__cur_size / file_size):
                    self.__process = int(100 * self.__cur_size / file_size)
                self.__mutex_process.release_lock()

    def cancel(self):
        if os.path.exists(self.__local_path):
            os.remove(self.__local_path)

    def is_finished(self):
        return self.__isFinished
    
    def get_delta(self):
        if self.__can_calculate_rate:
            res = self.__cur_size-self.__last_size
            self.__last_size = self.__cur_size
            return res
        else:
            return 0

    def stop(self):
        self.__mutex_pause.acquire_lock()
        self.__isPaused = True
        self.__mutex_pause.release_lock()
