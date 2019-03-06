#import sys
#import pandas as pd
#sys.path.append('/home/mllabs/edward/edward_workspace/')
# import input_data
# data = input_data.read_data_sets()
# x_test = data.test.pos_keypoints
#y_test =data.test.labels
import numpy as np

#摄像头安装在右后方
def wrong_head(data):
    # data = x_test[0]
    # if data.shape[0]:
    #print(data)
    '''
        右眼: data[15*3], data[15*3+1], data[15*3+2]
        左眼: data[16*3], data[16*3+1], data[16*3+2]
        右耳: data[17*3], data[17*3+1], data[17*3+2]
        左耳: data[18*3], data[18*3+1], data[18*3+2]
    '''
    if (data[45] == -2) :#不止一个人
        return 0
    elif (data[45] == -1 ): # 没有人
        return 0
    elif data[16*3] != 0:   # 能看见左眼
        return 2
    elif data[15*3] == 0 or data[17*3] == 0:   # 看不见右眼或者右耳
        return 3
    else:
        return 0
    #elif (data[48] != 0) & (data[45] != 0) & (data[51] != 0) & (data[54] != 0):#全部能看见
    #    return 1
    # elif (data[45] == -1) & (data[42] !=-1)  & (data[48] !=-1) & (data[51] ==-1):#能看见右耳右眼
    #    return 2
#    elif (data[48] != 0) & (data[51] > 0.1) & (data[45] != 0) & (data[51] != 0)& (data[54] == 0):#只有左耳看不见（右偏头）& (data[47] >= 0.18)
#        return 3
#    elif (data[48] != 0) & (data[45] == 0) & (data[51] == 0) & (data[54] != 0):#能看见左耳左眼
#        return 4
#    elif (data[48] == 0) & (data[45] == 0) & (data[51] == 0) & (data[54] != 0):#只看见左耳（右偏头）
#        return 5
#    elif (data[45] == 0) & (data[48] == 0) & (data[51] == 0) & (data[54] == 0):#全部看不见
#        return 0
#    else:
#        return 0
    # else:
    #     return ('未输入数据')

def wrong_head_co(data):
    # data = x_test[0]
    # if data.shape[0]:
    #print(data)
    '''
        右眼: data[15*3], data[15*3+1], data[15*3+2]
        左眼: data[16*3], data[16*3+1], data[16*3+2]
        右耳: data[17*3], data[17*3+1], data[17*3+2]
        左耳: data[18*3], data[18*3+1], data[18*3+2]
    '''
    if (data[45] == -2) :#不止一个人
        return 0
    elif (data[45] == -1 ): # 没有人
        return 0
    # elif data[18*3] == 0: # 看不见左耳
    #     return 1
    elif data[16*3] != 0 or data[15*3] != 0: # 能看见左眼或右眼
        return 2
    else:
        return 0

def get_angle(data_in):
    data = []
    for j in [1,2,3,4,8]:
        x = data_in[3*j]
        y = data_in[3*j + 1]
        data.append(x)
        data.append(y)
    x = np.array((data[4] - data[2],data[5] - data[3]))
    y = np.array((data[4] - data[6],data[5] - data[7]))
    Lx = np.sqrt(x.dot(x))
    Ly = np.sqrt(y.dot(y))
    cos_angle = x.dot(y)/(Lx*Ly)
    angle = np.arccos(cos_angle) * 360/2/np.pi
    x1 = np.array((data[0] - data[8],data[1] - data[9]))
    y1 = np.array((data[2] - data[4],data[3] - data[5]))
    Lx1 = np.sqrt(x1.dot(x1))
    Ly1 = np.sqrt(y1.dot(y1))
    cos_angle1 = x1.dot(y1)/(Lx1*Ly1)
    angle1 = np.arccos(cos_angle1) * 360/2/np.pi

    if not np.isnan(angle) and not np.isnan(angle1):
        return [int(np.round(angle1)),int(np.round(angle)),data[3],data[7]]

def arm_detect(x_test):
    data_in = x_test
    # if data.shape[0]:
    #print(data)
    flg = 0
    if (data_in[45] == -2) :#不止一个人
        flg = 0
    else:

        for j in [1,2,3,4,8]:
            if data_in[3*j] == -1 or data_in[3*j] == 0: # 手臂躯干识别不完整
                return 0

        list_in = get_angle(data_in)
        if list_in == None or (list_in[0] < 70 and (list_in[1] >= 70 or list_in[1] <=20)) or list_in[2] < list_in[3]:
            flg = 1 #normal
        elif list_in[0] >= 70 and list_in[0] <= 150 and list_in[1] >= 100:
            flg = 2 #point_forward
        elif  list_in[0] >= 70 and list_in[0] <= 120 and list_in[1] >= 30 and  list_in[1] <= 100:
            flg = 3 #fist
        else:
            flg = 4 #other
    return flg

def nap_detect(data):
    #flg = 0
    if data[3*15+1] >= data[3*17+1]:
        return 0
    else:
        return 1

