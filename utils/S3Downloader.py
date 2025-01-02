import csv
import os
import threading
from pathlib import Path
import boto3

from config.GConfig import gConfig
from peewee import SqliteDatabase, Model, IntegerField, TextField, AutoField

class S3Downloader:
    def __init__(self,bucket_name,cloud_path,local_path):
        self.__bucket_name = bucket_name
        self.__cloud_path = cloud_path
        self.__local_path = local_path
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
        self.__mutex = threading.Lock()
        self.__isPaused = False

    def get_process(self):
        return self.__process

    def get_file_size(self):
        return self.__file_size

    def execute(self):
        with open(self.__local_path, 'a') as file:
            pass
        # 获取对象的总大小
        file_size = self.__client.head_object(Bucket=self.__bucket_name, Key=self.__cloud_path)['ContentLength']
        part_size = int(file_size / 100 + 1024)
        cur_size = os.path.getsize(self.__local_path)
        self.__mutex.acquire_lock()
        self.__isPaused = False
        self.__mutex.release()
        with open(self.__local_path, 'ab') as f:
            while True:
                # 获取锁
                self.__mutex.acquire_lock()
                # 如果暂停
                if self.__isPaused:
                    self.__mutex.release()
                    break
                else:
                    self.__mutex.release()
                # 如果完成
                if cur_size >= file_size:
                    break
                # 使用 Range 头下载部分内容
                end = min(cur_size + part_size - 1, file_size - 1)
                response = self.__client.get_object(Bucket=self.__bucket_name, Key=self.__cloud_path,
                                                Range="bytes={0}-{1}".format(cur_size, end))
                f.write(response['Body'].read())

                print("file_size:{0}".format(file_size))
                print("bytes={0}-{1}".format(cur_size, end))

                cur_size = os.path.getsize(self.__local_path)

                if self.__process != int(100 * cur_size / file_size):
                    self.__process = int(100 * cur_size / file_size)

    def cancel(self):
        if os.path.exists(self.__local_path):
            os.remove(self.__local_path)

    def stop(self):
        self.__mutex.acquire_lock()
        self.__isPaused = True
        self.__mutex.release_lock()
