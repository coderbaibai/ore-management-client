class FileType():
    directory = 0
    file = 1

    def getTypeName(input:int):
        if input==FileType.directory:
            return '文件夹'
        elif input==FileType.file:
            return '文件'
        else:
            return 'unknown'
    def getIconPath(input:int):
        if input==FileType.directory:
            return './resources/icons/directory.png'
        elif input==FileType.file:
            return './resources/icons/file.png'
        else:
            return 'unknown'
        
class StateType():
    upload = 0
    download = 1

    def getIconPath(input:int):
        if input==StateType.upload:
            return './resources/icons/trans_upload.png'
        elif input==StateType.download:
            return './resources/icons/trans_download.png'
        else:
            return 'unknown'
        
    def getTypeName(input:int):
        if input==StateType.upload:
            return '上传完成'
        elif input==StateType.download:
            return '下载完成'
        else:
            return 'unknown'
        
class UnitTranslator():
    def convert_bytes(byte_size):
        # 定义单位
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
        
        # 确保字节数是正数
        if byte_size < 0:
            return "字节数不能为负"

        # 获取单位的索引
        i = 0
        while byte_size >= 1024 and i < len(units) - 1:
            byte_size /= 1024.0
            i += 1

        # 返回转换后的值和单位
        return f"{byte_size:.2f} {units[i]}"
 