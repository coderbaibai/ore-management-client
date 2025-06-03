import numpy as np
import os
import cv2
import get_mainSize

def intervalStatistic(imagesPath, labelsPath, start, intervalSize, end, mode = 2):
    ''' 标注后，统计文件夹中物体的尺寸分布
    
    :param imagesPath 标注的图片文件夹路径
    :param labelsPath 标注的标签txt文件夹路径
    :param start 统计起点
    :param intervalSize 统计区间间隔
    :param  end 统计终点及以后
    :param mode 指定统计种类 0 第0类 1 第1类 2 全部， 默认 全部
    '''
    # 获取图片的长、宽
    if os.listdir(imagesPath):
        imgFile = os.listdir(imagesPath)[0]
        img = cv2.imread(os.path.join(imagesPath, imgFile))
        size = img.shape
        height, width = size[0],size[1]
    else:
        print("图片为空")
        return
    
    # 创建统计区间列表
    intervalSet = [] 
    # eg. (30, 30, 100) -> intervalSet = [[30,60],[60,90],[90,100]]
    for i in range(start, end, intervalSize):
        if i + intervalSize < end:
            intervalSet.append([i, i+intervalSize])
        else:
            intervalSet.append([i, end])
            
    # 对应统计区间列表，记录各区间的物体数量
    statisticList = np.zeros(len(intervalSet)).tolist()

    # 记录每个物料的size
    all_size_list = []
    
    # 记录每张图片的标签数量dict，key 为图片名称， value 为标签数量
    name_size_dict = {}
    
    s = ''
    for i in os.listdir(labelsPath):
        # 读取label.txt 文件
        #print(labelsPath)
        with open(os.path.join(labelsPath, i),'r') as f:
            pred_info = [line.strip().split(' ') for line in f.readlines()]
        pred_cls = [j[0] for j in pred_info]
        if not pred_cls:
            # 当label.txt为空时跳过
            continue

        name_size_dict[i.replace('.txt', '')] = len(pred_cls)

        # 将 info 转为 xyxy 形式
        pred_xyxy = [[float(x) for x in subinfo[1:]] for subinfo in pred_info]
        #print(i)
        for idx in range(len(pred_xyxy)):

            # 使用短边长度，作为物体尺寸
            minLength = min(pred_xyxy[idx][2] - pred_xyxy[idx][0], pred_xyxy[idx][3] - pred_xyxy[idx][1])

            
            all_size_list.append(int(minLength))

            if mode == 2:
                index = intervalCal(minLength, start, intervalSize, len(statisticList))
                statisticList[index] += 1
                continue
            
        statisticList = [int(i) for i  in statisticList]
        # 将statisticList 转置，便于输出元素
        # statisticList = list(map(list,zip(*statisticList)))

        all_sum = 0
        for j in statisticList:
            all_sum += j
        s = 'all:{:<4} '.format(all_sum)
        for j in range(len(statisticList)):
            if j == len(statisticList)-1:
                s = s + '{}-{}及以上:{:<5}'.format(intervalSet[j][0], intervalSet[j][1], statisticList[j])
            else:
                s = s + '{}-{}:{:<5}'.format(intervalSet[j][0], intervalSet[j][1], statisticList[j])
        # print(title[i].ljust(frm_info_w),s)
    #print("cls:"+ str(mode) + " " + s)
    with open(labelsPath.replace('/labels', '/statistic.txt'), 'a+') as f:
        f.write("cls:"+ str(mode) + " " + s + '\n')

    # 用于记录压缩包物料尺寸分布的list，hash表，长度为 max(list) + 1. eg:list[10] = 2, 意味着长度为 10 的物料有 2 个
    size_hash_list = get_size_hash_list(all_size_list)

    # 计算主体力度
    mainSize = get_mainSize.main(all_size_list)

    return sum(statisticList), size_hash_list, mainSize, name_size_dict, 


def get_size_hash_list(all_size_list):
    maxLen = max(all_size_list)
    size_hash_list = [0] * (maxLen + 1)
    for size in all_size_list:
        size_hash_list[size] += 1
    
    return size_hash_list

def intervalCal(minLength, start, intervalSize, lengthOfStatisticList):
    # 尺寸减去起点值，除以间隔，从而确定对应的区间
    index = int((minLength - start) /intervalSize)
    if index >= lengthOfStatisticList:
        # 超出最大尺寸的，放在最后一个元素列表中
        index = lengthOfStatisticList-1

    return index

if __name__ == '__main__':
    
    imagesPath = 'data/dingwei_mei'
    labelsPath = 'data/modelAnchorTest/dingwei_mei/labels'
    start = 0
    intervalSize = 20
    end = 200
    intervalStatistic(imagesPath, labelsPath, start = start, intervalSize = intervalSize, end = end)

    

