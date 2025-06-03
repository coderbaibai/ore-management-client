import os
import make_data_yolo as make_hlr_16
from unpack_extract_cls import extract_and_check
import shutil
import re

# input: zip_path, str, 压缩包所在路径
# return: cls, 种类 / kv, 电压 / ma， 电流
def main(zip_path):
    print("正在解压：", zip_path)
    # zip_path 压缩包所在父目录
    dir = zip_path.rsplit('/', 1)[0]
    filename = zip_path.rsplit('/', 1)[1].rsplit('.', 1)[0]
    imgs_path = ''
    # 解压出来的文件夹路径
    unpack_path = dir + '/' + filename
    if os.path.exists(unpack_path):
        shutil.rmtree(unpack_path)
    # 返回物料类别
    cls = extract_and_check(zip_path)

    # 返回压缩包电压，电流
    kv, ma = getVoltageAndCurrent(zip_path)
    print("正在处理：", zip_path, cls)

    print('生成定位图像...')
    
    make_hlr_16.make_hlr(unpack_path, unpack_path + f'/dingwei_{cls}', cls)
    imgs_path = unpack_path + f'/dingwei_{cls}'
    return imgs_path, cls, kv, ma

def getVoltageAndCurrent(zip_path):

    # 定义正则表达式模式
    pattern = r'(\d+)kv\s*-\s*(\d+(?:\.\d+)?)ma'

    # 使用re.search()函数查找匹配项
    match = re.search(pattern, zip_path)

    # 提取匹配到的电压和电流值
    voltage = match.group(1) if match else None
    current = match.group(2) if match else None

    return voltage, current

if __name__ == '__main__':
    print(main('/media/jzth/20TB/data_statistics/data/20250421-shi-175kv-2.3ma-2-youbiaozhun5hao.7z'))

