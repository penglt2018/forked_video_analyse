#-*-coding:UTF-8-*-

#摄像头安装在右侧
def wrong_head(x_test):
    data = x_test[0]
    if (data[48] != -1) & (data[45] != -1) & (data[51] != -1) & (data[54] != -1):#全部能看见
        return 1
    elif (data[48] == -1) & (data[45] ==-1)  & (data[51] !=-1) & (data[54] !=-1):#只能看见耳朵
       return 2
    elif (data[48] == -1) & (data[45] != -1) & (data[51] != -1) & (data[54] != -1):#只有左眼看不见
        return 3
    elif (data[48] != -1) & (data[45] !=-1) & (data[51] ==-1) &(data[54] !=-1):#只有右耳看不见（左偏头）
        return 4
    elif (data[48] == -1) & (data[45] == -1) & (data[51] != -1) & (data[54] == -1):  # 只看见右耳（左偏头）
        return 5
    elif (data[48] != -1) & (data[45] !=-1) & (data[51] !=-1) & (data[54] == -1) & (data[50] >= 0.7):#只有左耳看不见（右偏头）
        return 6
    elif (data[48] == -1) & (data[45] ==-1) & (data[51] ==-1) & (data[54] != -1):#只看见左耳（右偏头）
        return 7
    # elif (data[45] == -1) & (data[42] !=-1) & (data[44] < 0.7) & (data[48] !=-1)& (data[51] == -1):#能看见右耳右眼，往左微微偏
    #     return 8
    elif (data[45] == -1) & (data[48] ==-1) & (data[51] ==-1) & (data[54] ==-1):#全部看不见
        return 0
    elif (data[45]==-2): #不止一个人
        return 0
    else:
        return 0
