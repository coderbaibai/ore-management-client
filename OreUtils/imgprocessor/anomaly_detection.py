# 压缩包中异常图片检测
# 算法原理：矿场采集物料，往往是通过人工的方式进行上料。每次上料的数量差不多，并不会产生过大的浮动。因此，可统计压缩包中定位标签的数量分布，若出现过大值，则认为该图片异常。
# 过大值判定依据: 根据统计学原理，利用 IQR 和 z-score 理论进行判定。在本场景中，若 IQR 和 z-score，都未检测出异常，则认定可靠。否则均为不可靠。

import numpy as np
from scipy import stats
import os
import cv2
np.set_printoptions(threshold = np.inf)
def find_outliers_iqr(data):
    values = list(data.values())
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = {}
    for key, value in data.items():
        if value > upper_bound:
            outliers[key] = value
    return outliers

# # 示例使用
# data = {'a': 1, 'b': 2, 'c': 10, 'd': 3}
# outliers = find_outliers_iqr(data)

# for key, value in outliers.items():
#     print(f"key: {key}, val: {value}")

def find_outliers_zscore(data, threshold=3):
    values = list(data.values())
    z_scores = np.abs(stats.zscore(values))
    # print(z_scores)
    outliers = {}
    for (key, value), z_score in zip(data.items(), z_scores):
        if z_score > threshold:
            outliers[key] = value
    return outliers

# # 示例使用
# data = {'a': 1, 'b': 2, 'c': 10, 'd': 3}
# outliers = find_outliers_zscore(data)

# for key, value in outliers.items():
#     print(f"key: {key}, val: {value}")

def find_outliers_baseImg(labels_path, imgs_path):

    anomaly_files_list = []
    # 锚定框内所有元素值相同，则认为出现异常
    label_path_list = [labels_path + '/' + i for i in os.listdir(labels_path)]
    for label_file in label_path_list:
        lbs_data = []
        with open(label_file, 'r') as f:
            lbs_data = f.readlines()
        
        img_file_path = imgs_path + '/' + label_file.rsplit('/', 1)[1].replace('txt', 'png')
        img = cv2.imread(img_file_path, -1)
        img_width, img_height = img.shape[1], img.shape[0]

        cnt = 0
        for lb in lbs_data:
            # 将 yolo 格式的位置转化为 锚定框 左上角、右下角的点坐标： box_src = (x_min, y_min, x_max, y_max)
            parts_src = lb.strip().split()
            cnt += 1
            x1, x2, x3, x4 = map(float, parts_src[1:])

            box_src = [0, 0, 0, 0]
            if x3 - x1 > 1:
                box_src[0] = parts_src[2]
                box_src[1] = parts_src[4]
                box_src[2] = parts_src[1]
                box_src[3] = parts_src[3]
                box_src = [float(x) for x in list(box_src)]
            else:
                x_center, y_center, bbox_width, bbox_height = x1, x2, x3, x4
                box_src[2] = int((x_center - bbox_width / 2) * img_width)
                box_src[0] = int((y_center - bbox_height / 2) * img_height)
                box_src[3] = int((x_center + bbox_width / 2) * img_width)
                box_src[1] = int((y_center + bbox_height / 2) * img_height)
            
            box_src = [int(x) for x in list(box_src)]
            object_name = label_file.replace('.txt', f'_{cnt}.png')
            cropped_image = img[box_src[0] : box_src[1], box_src[2] : box_src[3]] / 255.0

            if cropped_image.shape[0] < 5 or cropped_image.shape[1] < 5:
                continue

            if is_anomaly_box(cropped_image.astype(np.uint8)):
                anomaly_files_list.append(img_file_path.rsplit('/',1)[1].replace('.png',''))
                break
            
    return anomaly_files_list


# 判断锚定框中是否所有元素数值相同
def is_anomaly_box(img):

    gray_bbox = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    _, binary_bbox = cv2.threshold(gray_bbox, 1, 255, cv2.THRESH_BINARY)
    #cv2.imwrite('./b.png', binary_bbox)
    if np.all(np.equal(binary_bbox, binary_bbox[0][0])):
        return True
    else:
        return False

    

def main(data_dict, labels_path, imgs_path):
    # 记录异常图片名称的list
    anomaly_img_list = []

    iqr_outliers = find_outliers_iqr(data_dict)
    zScore_outliers = find_outliers_zscore(data_dict)
    baseImg_outliers = find_outliers_baseImg(labels_path, imgs_path)

    anomaly_img_list.extend(list(iqr_outliers.keys()))
    anomaly_img_list.extend(list(zScore_outliers.keys()))
    
    anomaly_img_list.extend(list(baseImg_outliers))

    #print(anomaly_img_list)
    if anomaly_img_list:
        return True, set(anomaly_img_list)
    else:
        return False, set(anomaly_img_list)

if __name__ == "__main__":
    data_dict = {}
    main(data_dict)
    
 