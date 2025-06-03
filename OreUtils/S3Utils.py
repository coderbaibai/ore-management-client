import asyncio
from functools import partial
import os
import threading
import boto3

from config.GConfig import gConfig
from OreUtils.TypeUtils import FileType

class S3Utils:
    def __init__(self):
        # 初始化客户端
        self.__client  = boto3.client(
            's3',
            aws_access_key_id=gConfig['server']['minio']['id'],
            aws_secret_access_key=gConfig['server']['minio']['key'],
            endpoint_url=gConfig['server']['minio']['url']  # 配置区域
        )
        self.__source = boto3.resource(
            's3',
            aws_access_key_id=gConfig['server']['minio']['id'],
            aws_secret_access_key=gConfig['server']['minio']['key'],
            endpoint_url=gConfig['server']['minio']['url']  # 配置区域
        )
        self.is_rename_idle = True
        self.rename_mutex = threading.Lock()

    def getItems(self,pathList:list[str]):
        if len(pathList)<=0:
            print('path error')
            return
        elif len(pathList)==1:
            buckets = self.__client.list_buckets()['Buckets']
            return buckets
        else:
            pathStr = '/'.join(pathList[2:])
            if pathStr!='':
                pathStr = pathStr+'/'
            res = self.__client.list_objects_v2(
                Bucket=pathList[1],
                Prefix=pathStr,
                Delimiter='/'
            )
            return res
    

    async def rename(self,bucket_name,old_key,new_key):
        with self.rename_mutex:
            if self.is_rename_idle:
                self.is_rename_idle = False
            else:
                return False, '正在重命名中'
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None,partial(
            self.__client.copy_object,
            CopySource={'Bucket': bucket_name, 'Key': old_key},
            Bucket=bucket_name,
            Key=new_key
        ))
        await loop.run_in_executor(None,partial(
            self.__client.delete_object,
            Bucket=bucket_name,
            Key=old_key
        ))
        with self.rename_mutex:
            self.is_rename_idle = True
            return True, '重命名成功'

    def search(self,bucket_name, keyword):
        """
        列出存储桶中所有包含关键字的 Key
        :param bucket_name: 存储桶名称
        :param keyword: 需要匹配的关键字
        :return: 包含关键字的 Key 列表
        """
        keys_with_keyword = []  # 用于存储匹配的 Key
        continuation_token = None  # 用于分页的 ContinuationToken

        while True:
            # 如果有 ContinuationToken，则添加到请求参数中
            if continuation_token:
                response = self.__client.list_objects_v2(
                    Bucket=bucket_name,
                    ContinuationToken=continuation_token
                )
            else:
                response = self.__client.list_objects_v2(
                    Bucket=bucket_name
                )

            # 遍历返回的对象列表
            if 'Contents' in response:
                for obj in response['Contents']:
                    fName = os.path.basename(os.path.normpath(obj['Key']))
                    key = obj['Key']
                    idx = fName.find(keyword,0)
                    if idx != -1:  # 检查 Key 是否包含关键字
                        keys_with_keyword.append({
                            'key':key,
                            'idx':idx,
                            'modify':obj['LastModified'],
                            'size':obj['Size']
                        })

            # 检查是否还有更多数据
            if response.get('NextContinuationToken'):
                continuation_token = response['NextContinuationToken']
            else:
                break  # 没有更多数据，退出循环

        return keys_with_keyword

        
    def copyFile(self,sourceBucket,sourceKey,targetBucket,targetKey):
        copy_source = {'Bucket': sourceBucket, 'Key': sourceKey}
        self.__client.copy_object(CopySource=copy_source,Bucket=targetBucket,Key=targetKey)

    def cutFile(self,sourceBucket,sourceKey,targetBucket,targetKey):
        copy_source = {'Bucket': sourceBucket, 'Key': sourceKey}
        self.__client.copy_object(CopySource=copy_source,Bucket=targetBucket,Key=targetKey)
        self.__client.delete_object(Bucket=sourceBucket,Key=sourceKey)

    def deleteFile(self,bucket,key):
        response = self.__client.list_objects_v2(Bucket=bucket, Prefix=key)
        for obj in response['Contents']:
            self.__client.delete_object(Bucket=bucket,Key=obj['Key'])
    
    def getFileSize(self,bucket,path,file_type):
        if file_type == FileType.file:
            return self.__client.head_object(Bucket=bucket, Key=path)['ContentLength']
        else:
            pass


s3Utils = S3Utils()