# 计算主体粒度


import numpy as np

def trimmed_mean(data, trim_percent=0.1):
    """
    计算截尾均值
    
    参数:
        data (list): 输入数据列表
        trim_percent (float): 要截去的百分比(0-0.5)，默认为0.1(10%)
    
    返回:
        float: 截尾均值
    """
    if not data:
        raise ValueError("输入数据不能为空")
    
    if trim_percent < 0 or trim_percent >= 0.5:
        raise ValueError("截尾百分比必须在0到0.5之间")
    
    # 将数据排序
    sorted_data = sorted(data)
    n = len(sorted_data)
    
    # 计算要截去的元素数量
    k = int(n * trim_percent)
    
    # 截去最高和最低的k个元素
    trimmed_data = sorted_data[k:n-k]
    
    # 如果截去后没有数据了（当k >= n-k时），返回0或抛出异常
    if not trimmed_data:
        return 0.0  # 或者可以 raise ValueError("截尾后没有剩余数据")
    
    # 计算剩余数据的平均值
    return int(np.mean(trimmed_data))


def main(data_list):
    # print("原始均值:", np.mean(data_list))
    # print("10%截尾均值:", trimmed_mean(data_list, 0.1))
    # print("20%截尾均值:", trimmed_mean(data_list, 0.2))

    return trimmed_mean(data_list, 0.1)

if __name__ == "__main__":
    # 示例使用
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]  # 包含一个异常值100
    main(data)