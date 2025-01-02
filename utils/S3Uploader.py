import csv
import os
import threading
from pathlib import Path
import boto3
from config.GConfig import gConfig
from peewee import SqliteDatabase, Model, IntegerField, TextField, AutoField

db = SqliteDatabase(Path.cwd()/gConfig['client']['upload-db-path'])

class UploaderItem(Model):
    id = TextField(primary_key=True)
    sign = TextField(null=True)
    count = IntegerField(null=True)
    local = TextField(null=True)
    bucket = TextField(null=True)
    cloud = TextField(null=True)
    eTag = TextField(null=True)

    class Meta:
        database = db
        table_name = 'tb_uploader'

db.connect()
db.create_tables([UploaderItem])


class S3Uploader:
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
        last = {}
        # 如果找到之前的记录
        items = []
        temps = list(UploaderItem.select().where(
            (UploaderItem.local == self.__local_path) &
            (UploaderItem.bucket == self.__bucket_name) &
            (UploaderItem.cloud == self.__cloud_path)
        ))
        if len(temps) == 0:
            # 如果没有记录
            # 创建记录
            last['sign'] = self.__client.create_multipart_upload(Bucket=self.__bucket_name, Key=self.__cloud_path)['UploadId']
            last['local'] = self.__local_path
            last['bucket'] = self.__bucket_name
            last['cloud'] = self.__cloud_path
            last['count'] = 0
            last['eTag'] = ""
        else:
            for tmp in temps:
                items.append({
                    'sign':tmp.sign,
                    'local':tmp.local,
                    'bucket':tmp.bucket,
                    'cloud':tmp.cloud,
                    'count':tmp.count,
                    'eTag':tmp.eTag
                })
            items.sort(key=lambda key_item: key_item['count'])
            last = items[-1].copy()

        self.__mutex.acquire_lock()
        self.__isPaused = False
        self.__mutex.release_lock()
        # 开始上传
        with open(last['local'], 'rb') as f:
            this_time_size = 0
            cur_size = 0
            file_size = os.stat(last['local']).st_size
            part_size = int(file_size / 100) + 1024
            done = last['count']
            f.seek(part_size * done)
            cur_size += part_size * done
            while True:
                # 获取锁
                self.__mutex.acquire_lock()
                # 如果暂停
                if self.__isPaused:
                    # 写回数据
                    for item in items:
                        UploaderItem.insert_many(item).on_conflict_ignore().execute()
                    self.__mutex.release_lock()
                    break
                self.__mutex.release_lock()
                # 读出数据
                data = f.read(part_size)
                # 如果已经读完
                if not data and data == b"":
                    res = []
                    for item in items:
                        res.append({'PartNumber': item['count'], 'ETag': item['eTag']})
                    self.__client.complete_multipart_upload(
                        Bucket=self.__bucket_name,
                        Key=self.__cloud_path,
                        UploadId=last['sign'],
                        MultipartUpload={'Parts': res}
                    )
                    UploaderItem.delete().where(UploaderItem.sign==last['sign']).execute()
                    break
                # 上传分段
                etag = self.__client.upload_part(Bucket=self.__bucket_name,
                                             Key=self.__cloud_path,
                                             UploadId=last['sign'],
                                             Body=data, PartNumber=last['count'] + 1)
                last['count'] += 1
                last['eTag'] = etag['ETag']
                last['id'] = last['sign']+str(last['count'])
                print("upload"+str(last['count']))
                items.append(last.copy())

                cur_size += len(data)
                this_time_size += len(data)
                # 超过1%时更新process
                if self.__process != int(100 * cur_size / file_size):
                    self.__process = int(100 * cur_size / file_size)
                # 每50M数据自动保存一次
                if this_time_size > gConfig['client']['save-size']:
                    UploaderItem.insert_many(items).on_conflict_ignore().execute()
                    this_time_size  = 0

    def cancel(self):
        # 找到标志
        items = UploaderItem.select().where(
            (UploaderItem.local == self.__local_path) &
            (UploaderItem.bucket == self.__bucket_name) &
            (UploaderItem.cloud == self.__cloud_path)
        )
        UploaderItem.delete().where(
            (UploaderItem.local == self.__local_path) &
            (UploaderItem.bucket == self.__bucket_name) &
            (UploaderItem.cloud == self.__cloud_path)
        ).execute()
        if(len(items)):
            self.__client.abort_multipart_upload(
                Bucket=items[0]['bucket'],
                Key=items[0]['local'],
                UploadId=items[0]['sign']
            )
    def stop(self):
        self.__mutex.acquire_lock()
        self.__isPaused = True
        self.__mutex.release_lock()






