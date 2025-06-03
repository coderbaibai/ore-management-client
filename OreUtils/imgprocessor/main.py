import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))) # 添加模块所在目录到 sys.path
import data_process
import yolov5.detect
import intervalStatisticForLabel
import anomaly_detection
def main(zip_path, start, end, intervalSize):
    result = {}
    # 1 图像预处理：生成用于目标检测的图像, 并且返回物料种类、电压、电流信息
    imgs_path, result['cls'], result['voltage'], result['current'] = data_process.main(zip_path)

    # 移除命令行参数, 避免目标检测代码进行读入
    sys.argv = [sys.argv[0]]

    # 2 调用目标检测模型，实现定位检测
    labels_path = yolov5.detect.main(data_path = imgs_path, target_path=zip_path.rsplit('.', 1)[0] + '/modelAnchorTest')

    # 3 统计检测结果： 物料总数:int、物料尺寸分布: list, 用于主体粒度计算的中间变量:int、用于异常检测的中间变量：name_size_dict
    result['cnt'], result['distribution'], result['mainSize'], name_size_dict = intervalStatisticForLabel.intervalStatistic(imagesPath=imgs_path, labelsPath=labels_path, 
                                                start = int(start), end = int(end), intervalSize = int(intervalSize))
    
    # 4 异常检测: 是否可靠:bool、异常图片路径:list
    result['anomaly'], result['anomalyList'] = anomaly_detection.main(name_size_dict, labels_path, imgs_path)
    print(result)
    return result

if __name__ == "__main__":
    # 压缩包存储目录
    zip_path = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]
    intervalSize = sys.argv[4]
    main(zip_path, start, end, intervalSize)

    # cmd line: python main.py ./data/20250418-shi-185kv-2.3ma-3-zuobiaozhun9hao-含脏数据.7z 0 200 20
