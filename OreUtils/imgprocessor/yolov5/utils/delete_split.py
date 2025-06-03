import os
import cv2

root_path="/home/jzth/桌面/data/mukuang_mix2"

labels=["mei","shi"]


def read_img():
    for label in labels:
        for dir in os.listdir(root_path+"/"+label):
            split_path=root_path+"/"+label+"/"+dir+"/Mei_/High"
            img_path = root_path+"/"+label+"/"+dir+"/mei"
            imgs=os.listdir(img_path)
            for split in os.listdir(split_path):
                img_split=cv2.imread(split_path+"/"+split,-1)
                if()


# if __name__ == "__main__":
#     path=root_path+

