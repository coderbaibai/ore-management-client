import os
import zipfile
import py7zr
import rarfile


def extract_and_check(zip_file_path):
    # 获取压缩包的基本信息
    folder_name = os.path.splitext(os.path.basename(zip_file_path))[0]
    parent_dir = os.path.dirname(zip_file_path)
    extract_folder = os.path.join(parent_dir, folder_name)

    # 创建解压目录
    os.makedirs(extract_folder, exist_ok=True)

    # 解压文件（支持zip, 7z 和 rar格式）
    if zip_file_path.endswith('.zip'):
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
    elif zip_file_path.endswith('.7z'):
        with py7zr.SevenZipFile(zip_file_path, mode='r') as z:
            z.extractall(path=extract_folder)
    elif zip_file_path.endswith('.rar'):
        with rarfile.RarFile(zip_file_path) as rar_ref:
            rar_ref.extractall(extract_folder)
    else:
        print("不支持的压缩格式")
        return None

    # 检查解压后的文件夹结构
    print(f"解压到：{extract_folder}")

    # 获取解压后文件夹中的所有子文件夹
    subfolders = [f for f in os.listdir(extract_folder) if os.path.isdir(os.path.join(extract_folder, f))]

    # 检查 blank 文件夹
    blank_folder = os.path.join(extract_folder, 'blank')
    if not os.path.exists(blank_folder):
        print("错误：没有找到 blank 文件夹")
        return None

    # 检查 blank 文件夹中的 High 和 Low 子文件夹
    blank_high_folder = os.path.join(blank_folder, 'High')
    blank_low_folder = os.path.join(blank_folder, 'Low')

    if not os.path.exists(blank_high_folder):
        print("错误：blank 文件夹中没有 High 子文件夹")
        return None
    if not os.path.exists(blank_low_folder):
        print("错误：blank 文件夹中没有 Low 子文件夹")
        return None

    # 获取 High 和 Low 文件夹中的图片文件
    blank_high_images = [f for f in os.listdir(blank_high_folder)
                         if os.path.isfile(os.path.join(blank_high_folder, f)) and
                         f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    blank_low_images = [f for f in os.listdir(blank_low_folder)
                        if os.path.isfile(os.path.join(blank_low_folder, f)) and
                        f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    # 检查 High 和 Low 文件夹中是否有图片，且每个文件夹只有一张图片
    if len(blank_high_images) != 1:
        print(f"警告：blank/High 文件夹中图片数量不为1，当前数量为 {len(blank_high_images)}")
    if len(blank_low_images) != 1:
        print(f"警告：blank/Low 文件夹中图片数量不为1，当前数量为 {len(blank_low_images)}")

    # 找到非 blank 文件夹（mei、mu、shi 或 yuan）
    other_folders = [f for f in subfolders if f != 'blank']
    if len(other_folders) != 1:
        print("错误：未找到唯一的非 blank 文件夹")
        return None

    non_blank_folder = other_folders[0]
    """
    允许的物料种类
    """
    valid_folders = ['mei', 'mu', 'shi', 'yuan']

    if non_blank_folder not in valid_folders:
        print(f"错误：非 blank 文件夹名不合法，找到的文件夹名为 {non_blank_folder}")
        return None

    # 检查非 blank 文件夹名称是否存在于压缩包文件名中
    if non_blank_folder not in folder_name:
        print(f"错误：非 blank 文件夹名 {non_blank_folder} 未包含在压缩包文件名中 ({folder_name})")
        return None

    # 检查 High 和 Low 文件夹
    high_folder = os.path.join(extract_folder, non_blank_folder, 'High')
    low_folder = os.path.join(extract_folder, non_blank_folder, 'Low')

    if not os.path.exists(high_folder):
        print(f"错误：{non_blank_folder} 文件夹中没有 High 文件夹")
        return None
    if not os.path.exists(low_folder):
        print(f"错误：{non_blank_folder} 文件夹中没有 Low 文件夹")
        return None

    high_images = [f for f in os.listdir(high_folder) if
                   os.path.isfile(os.path.join(high_folder, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    low_images = [f for f in os.listdir(low_folder) if
                  os.path.isfile(os.path.join(low_folder, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if len(high_images) == 0:
        print(f"错误：{non_blank_folder}/High 文件夹中没有图片")
    if len(low_images) == 0:
        print(f"错误：{non_blank_folder}/Low 文件夹中没有图片")

    if len(high_images) != len(low_images):
        print("警告：High 和 Low 文件夹中的图片数量不一致")
        # 删除多余的文件
        if len(high_images) > len(low_images):
            extra_files = set(high_images) - set(low_images)
            for file in extra_files:
                os.remove(os.path.join(high_folder, file))
                print(f"删除 {file}（在 High 文件夹中，但没有在 Low 文件夹中）")
        elif len(low_images) > len(high_images):
            extra_files = set(low_images) - set(high_images)
            for file in extra_files:
                os.remove(os.path.join(low_folder, file))
                print(f"删除 {file}（在 Low 文件夹中，但没有在 High 文件夹中）")

    print("文件夹检查完成，所有操作已完成。")

    # 返回非 blank 文件夹的名称
    return non_blank_folder


# 调用函数
if __name__ == "__main__":
    zip_file_path = r"D:\output2\202410312222-mei-165kv2.5ma-1\202410312222-mu-165kv2.5ma-1\202410312222-mu-165kv2.5ma-1.zip"
    non_blank_folder = extract_and_check(zip_file_path)
    if non_blank_folder:
        print(f"非 blank 文件夹的名字是：{non_blank_folder}")
