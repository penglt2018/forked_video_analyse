#本程序建于2018-4-10
#函数是为了取出时间序列中持续超过5秒的时间点及对应的首尾时间
import pandas as pd
import time
import numpy as np
func_stamp = lambda x:time.mktime(time.strptime(x,'%Y-%m-%d %H:%M:%S'))

def conti_check_v2(df_in, distance=1):
    """
    this function is made @ 2017/11/23, the latest vision.
    这个函数是为了查找故障时刻的连续性
    :param df_in: 状态判定为非正常的df结构数据,且索引为从0开始的整数序列***@condition must be satisfied.
    :param distance:
    :return: 故障时刻点在df_in中的row索引
    """
    para_conti = []
    time_series = df_in['timestamp'].values
    time_differ = time_series[1:] - time_series[:-1]

    df_differ = pd.DataFrame(time_differ, columns=['timediffer'])
    break_point = df_differ[df_differ['timediffer'] > distance].index.tolist()
    # 以上是选择数组中衡量尺度上不连续的数据点作为异常时刻。
    if len(break_point) != 0:
        for i in range(len(break_point)):
            if i == 0:
                para_conti.append([0, break_point[i]])
            else:
                para_conti.append([break_point[i - 1] + 1, break_point[i]])
        if break_point[-1] != len(time_series) - 1:
            para_conti.append([break_point[-1] + 1, len(time_series) - 1])
    else:
        para_conti.append([df_in.index[0],df_in.index[-1]])
    return para_conti

def predata(data_in):
    #对应数据为时间list
    df = pd.DataFrame(data_in,columns=['time','frame','filename'])
    df['timestamp'] = list(map(func_stamp, df['time']))
    df_out = df.sort_values(by=['timestamp','frame']).reset_index(drop=True)
    return df_out

def select_proper(df_in,para_in):
    """
    本函数取出满足持续时间不超过5秒或者超过5秒的首尾时刻
    :param df_in: 由predata产生的DataFrame
    :param para_in: 由time_Check_v2产生的列表
    :return: 可用时间点序列
    """
    out = []
    col_out = ['time','frame','filename']
    for item in para_in:
        if df_in.ix[item[1],'timestamp'] - df_in.ix[item[0],'timestamp'] >=7:
           element_start = [df_in.ix[item[0],col] for col in col_out]
           element_end = [df_in.ix[item[1],col] for col in col_out] 
           out.append(element_start + element_end)
    #     elif item[1] - item[0] == 0:
    #         out.extend([df_in.ix[item[1],'time']])
    #     else:
    #         out.extend(df_in['time'].loc[item[0]:item[1]].values)
    # out = list(np.unique(out))
    return out

def wrong_head_time_filter(data_in):
    df = predata(data_in)
    para = conti_check_v2(df)
    resu = select_proper(df,para)
    return resu

# if __name__ == '__main__':
#     print(main(['2017-04-10 10:55:55']))
# """test part"""
# filepath = r'C:\Users\chujp\Desktop\ImageData\sql_video\time_Series.txt'
# df = pd.read_csv(filepath,header=None)
# df.columns = ['time']
# df['timestamp'] = list(map(func_stamp,df['time']))
# df_todeal = df.copy()
# df_todeal = df_todeal.sort_values(by='timestamp').reset_index(drop=True)
#
# para = conti_check_v2(df_todeal)
#
# proper = select_proper(df_todeal,para)
