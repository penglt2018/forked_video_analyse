#-*-coding:UTF-8-*-

#摄像头安装在右侧
def wrong_head(data):
    # data = x_test[0]
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
    # elif (data[48] != 0) & (data[45] != 0) & (data[51] != 0) & (data[54] != 0):#全部能看见
    #     return 1

    elif data[15*3] == 0 or data[17*3] == 0: # 看不见右眼，或者看不见右耳
        return 1
    elif data[18*3] != 0: # 能看见左耳
        return 2

    # elif (data[48] == -1) & (data[45] ==-1)  & (data[51] !=-1) & (data[54] !=-1):#只能看见耳朵
    #    return 2
    # elif (data[48] == -1) & (data[45] != -1) & (data[51] != -1) & (data[54] != -1):#只有左眼看不见
    #     return 3
    # elif (data[48] != -1) & (data[45] !=-1) & (data[51] ==-1) &(data[54] !=-1):#只有右耳看不见（左偏头）
    #     return 4
    # elif (data[48] == -1) & (data[45] == -1) & (data[51] != -1) & (data[54] == -1):  # 只看见右耳（左偏头）
    #     return 5

    # elif (data[48] == -1) & (data[45] ==-1) & (data[51] ==-1) & (data[54] != -1):#只看见左耳（右偏头）
    #     return 7
    else:
        return 0

def nap_detect(data):
    #flg = 0
    if data[3*15+1] <= data[3*17+1]:
        return 0
    else:
        return 1
