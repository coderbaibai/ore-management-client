import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加模块所在目录到 sys.path
from OreUtils.SqliteUtils import TransportRecord
from OreUtils.TypeUtils import *

data_finish = {
    'name' :'测试文件',
    'type' : FileType.file,
    'size' : 1024,
    'state' : StateType.download,
    'time' : '2025.1.19',
    'local' : '/home/bhx/tmp',
    'bucket' : 'python-test-bucket',
    'cloud' : 'xwechat_files/cloud_temp_1GB.txt',
    'finish' : 1
}
data_up = {
    'name' :'测试文件',
    'type' : FileType.file,
    'size' : 1024,
    'state' : StateType.upload,
    'time' : '2025.1.19',
    'local' : '/home/bhx/tmp',
    'bucket' : 'python-test-bucket',
    'cloud' : 'xwechat_files/cloud_temp_1GB.txt',
    'finish' : 0
}

TransportRecord.insert(data_finish).execute()
TransportRecord.insert(data_up).execute()
TransportRecord.delete_by_id(3)