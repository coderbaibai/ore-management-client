import boto3

from config.GConfig import gConfig

class S3Utils:
    def __init__(self):
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


s3Utils = S3Utils()