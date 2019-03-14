#import sys
#import pandas as pd
#sys.path.append('/home/mllabs/edward/edward_workspace/')
# import input_data
# data = input_data.read_data_sets()
# x_test = data.test.pos_keypoints
#y_test =data.test.labels


#摄像头安装在后方
def wrong_head(x_test):
    data = x_test[0]
    # if data.shape[0]:
    #print(data)
    if (data[48] != -1) & (data[45] != -1) & (data[51] != -1) & (data[54] != -1):#全部看得到
        return 1
    elif (data[48] != -1) & (data[45] != -1) & (data[51] == -1) & (data[54] == -1):  # 看得到眼睛，看不见耳朵
        return 2
    elif (data[48] != -1) & (data[45] == -1) & (data[51] == -1) & (data[54] != -1):#看得到左眼及左耳，看不到右耳右眼
        return 3
    elif (data[48] == -1) & (data[45] == -1) & (data[51] == -1) & (data[54] != -1):  # 只看得到左耳
        return 4
    elif (data[48] == -1) & (data[45] != -1) & (data[51] != -1) & (data[54] == -1):#看不到左眼及左耳，看得到右耳右眼
        return 5
    elif (data[48] == -1) & (data[45] == -1) & (data[51] != -1) & (data[54] == -1):#只看得到右耳
        return 6
    # elif (data[45] == -1) & (data[42] == -1) & (data[48] != -1) & (data[51] != -1):#只能看见耳朵
    #     return 0
    elif (data[48] == -1) & (data[45] == -1) & (data[51] == -1) & (data[54] == -1):  # 全部看不见
        return 0
    elif (data[45] == -2) :#不止一个人
        return 0
    else:
        return 0
    # else:
    #     return ('未输入数据')
