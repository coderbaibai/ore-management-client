# 使用说明

## 环境配置
- 安装 pytorch 环境，保证目标检测技术(yolov5)的正常运行
- 安装 opencv-python(cv2)

## 如何运行
- 进入 yolov5_data_statistics 目录: cd ./yolov5_data_statistics
- 命令行运行 main.py : python main.py ./data 0 200 20

## 参数意义： python main.py ./data 0 200 20
- ./data :压缩包文件所在目录
- 0 : 大小统计的起点
- 200 : 大小统计的终点
- 20 : 大小统计的间隔

## 查看结果
- 成功执行 main.py 后，mei 压缩包统计结果保存在：./data/modelAnchorTest/dingwei_mei/statistic.txt，shi 同理 

