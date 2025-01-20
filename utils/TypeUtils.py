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