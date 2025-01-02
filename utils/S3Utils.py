import boto3

from config.GConfig import gConfig

s3_client  = boto3.client(
            's3',
            aws_access_key_id=gConfig['server']['id'],
            aws_secret_access_key=gConfig['server']['key'],
            endpoint_url=gConfig['server']['url']  # 配置区域
        )

s3_resource  = boto3.resource(
            's3',
            aws_access_key_id=gConfig['server']['id'],
            aws_secret_access_key=gConfig['server']['key'],
            endpoint_url=gConfig['server']['url']  # 配置区域
        )