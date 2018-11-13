#本程序建于2018-4-10
#函数是为了取出时间序列中持续超过5秒的时间点及对应的首尾时间
import pandas as pd
import time
import numpy as np
func_stamp = lambda x:time.mktime(time.strptime(x,'%Y-%m-%d %H:%M:%S')) #时间转为时间戳
func_time = lambda x:time.strftime('%Y-%m-%d %H:%M:%S',(time.localtime(x))) #时间戳转为时间
func_revis = lambda x:'2018-5-3 '+x.replace("'","") #special use, can be dropped.
func_duanhao = lambda x:x[:x.index('端')+1]

def ele_fil(list_in,str_in):
    for item in list_in:
        if str_in in item:
            return item

#data_in部分的数据连续时间段筛选，其中time_continuty表示连续时间长度
def dataContinutyCut(data_in,time_continuty=10):
    df_out = pd.DataFrame([])
    df = predata(data_in)
    para = conti_check_v2(df,distance=1)
    for item in para:
        if df.loc[item[1],'timestamp'] - df.loc[item[0],'timestamp'] >= time_continuty:
            df_out = df_out.append(df.loc[item[0]:item[1]])
    return df_out

def port_filter(df_in,para,range_judge):
    #version_2
    #caution:需要保证不会出现同一个时间多个开始结束行
    # col_out = list(df_in.keys())
    df_local = df_in.copy()
    #print(df_local.shape)
    #print(df_local)
    df_local.columns = ['time','state']
    df_local.insert(df_local.shape[1],'stamp',list(map(func_stamp,df_local['time'])))
    df_local = df_local.sort_values(by='stamp',ascending=True).reset_index(drop=True)
    point = func_stamp(para)
    # lenth = df_local.shape[0]
    # df_local['judge'] = df_local['stamp'] - point
    if df_local.iloc[0,2] >= point:
        mid = df_local.ix[0,1]
        return mid[:int(mid.index('端')+1)]
    elif df_local.iloc[-1,2] <= point:
        mid = df_local.iloc[-1,1]
        return mid[:int(mid.index('端') + 1)]
    else:
        before = df_local[df_local['stamp']<=point].sort_values(by='stamp',ascending=True).iloc[-2:]
        #before是dataFrame
        next = df_local[df_local['stamp']>point].sort_values(by='stamp',ascending=True).iloc[:2]
        if len(set(list(map(func_duanhao,before['state']))+list(map(func_duanhao,next['state'])))) == 1:
            # 判断时间节点所处前后时刻是否进行换端操作
            return list(map(func_duanhao,before['state']))[0]
        else:
            before_1 = df_local[df_local['state'].str.contains('结束')]
            next_1 = df_local[df_local['state'].str.contains('开始')]
            if next_1['stamp'].values[0] - point <= range_judge*60:
                return func_duanhao(next_1['state'].values[0])
            else:
                return func_duanhao(before_1['state'].values[0])

def conti_check_v2(df_in, distance=1):
    """
    this function is made @ 2017/11/23, the latest vision.
    这个函数是为了查找故障时刻的连续性
    :param df_in: 状态判定为非正常的df结构数据,且索引为从0开始的整数序列***@condition must be satisfied.
    :param distance:对应时间连续性要求参数
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
        #print(df_in.index)
        para_conti.append([df_in.index[0],df_in.index[-1]])
    return para_conti

def LKJ_pre(df_in,time_jump,row_add):
    #输入数据有两列，一列为时间，1列为速度，时间间隔超过'time_jump'按照首尾节点进行前后5S填充，其他则进行线性插值
    df = df_in.copy()
    #先去掉速度为NAN的行
    # df_v1 = df[df['速度'] != ' nan']#真实读出数据可能需要修改
    # df_v1[['速度']] = df_v1[['速度']].astype(float)#读出数据格式可能不需要修改
    # df_v1['时间'] = list(map(func_revis,df_v1['时间']))#对于特殊
    df.insert(0,'stamp',list(map(func_stamp,df['时间'])))
    df_v2 = df.drop_duplicates('时间').sort_values(by= 'stamp').reset_index(drop=True)
    add_row  = []
    judge = df_v2['stamp'].diff()[1:].astype(int)
    for k,v in enumerate(judge):
        if v != 1:
            if v <= time_jump:
                acc_speed = (df_v2.ix[k+1,'速度'] - df_v2.ix[k,'速度'])/v
                for i in range(1,v):
                    #添加时间戳、时间、速度
                    add_row.append([df_v2.ix[k,'stamp']+i,func_time(df_v2.ix[k,'stamp']+i),acc_speed*i+df_v2.ix[k,'速度']])
            else:
                for i in range(row_add):
                    add_row.append([df_v2.ix[k,'stamp']+i+1,func_time(df_v2.ix[k,'stamp']+i+1),df_v2.ix[k,'速度']])
                    add_row.append([df_v2.ix[k+1, 'stamp'] - i-1, func_time(df_v2.ix[k+1, 'stamp'] - i-1), df_v2.ix[k+1, '速度']])
    df_add = pd.DataFrame(add_row,columns=['stamp','时间','速度'])
    df_out = df_v2.append(df_add)
    df_out = df_out.sort_values(by='stamp')
    df_out = df_out[['时间','速度']]
    return df_out.reset_index(drop=True)

# def predata(data_in):
#     #对应数据为时间list
#     df = pd.DataFrame(data_in,columns=['time'])
#     df['timestamp'] = list(map(func_stamp, df['time']))
#     # df_out = df.sort_values(by='timestamp').reset_index(drop=True)
#     return df

def predata(data_in):
    #对应数据为时间list
    col_add = list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
    #df = pd.DataFrame(data_in,columns=['time','frame','filename'])
    df = pd.DataFrame(data_in, columns=['time', 'frame']+col_add)
    df['timestamp'] = list(map(func_stamp, df['time']))
    df_out = df.sort_values(by=['timestamp','frame']).reset_index(drop=True)
    return df_out

# def select_proper(df_in,para_in,):
#     """
#     本函数取出满足持续时间超过5秒或者超过5秒的首尾时刻
#     :param df_in: 由predata产生的DataFrame
#     :param para_in: 由time_Check_v2产生的列表
#     :return: 可用时间点序列
#     """
#     out = []
#     for item in para_in:
#         if item[1] - item[0] >=4:
#             out.extend([df_in.ix[item[0],'time'],df_in.ix[item[1],'time']])
#         elif item[1] - item[0] == 0:
#             out.extend([df_in.ix[item[1],'time']])
#         else:
#             out.extend(df_in['time'].loc[item[0]:item[1]].values)
#     out = list(np.unique(out))
#     return out

def select_proper(df_in,para_in,col_out, time_range):
    """
    本函数取出满足持续时间不超过5秒或者超过5秒的首尾时刻
    :param df_in: 由predata产生的DataFrame
    :param para_in: 由time_Check_v2产生的列表
    :col_out：输出数据的字段名
    :return: 可用时间点序列
    """
    out = []
    # col_out = ['time','frame','filename']
    for item in para_in:
        if df_in.ix[item[1],'timestamp'] - df_in.ix[item[0],'timestamp'] >= time_range:
           element_start = [df_in.ix[item[0],col] for col in col_out]
           element_end = [df_in.ix[item[1],col] for col in col_out]
           out.append(element_start + element_end)
    #     elif item[1] - item[0] == 0:
    #         out.extend([df_in.ix[item[1],'time']])
    #     else:
    #         out.extend(df_in['time'].loc[item[0]:item[1]].values)
    # out = list(np.unique(out))
    return out

def model_time_exclude(data1,data2,time_range):
    #data1: main data, left side
    #col_data = ['time']+['col_%s'%i for i in range(len(data1[0])-1)]
    #df1 = pd.DataFrame(data1,columns=col_data)
    #df2 = pd.DataFrame(data2, columns=col_data)
    df1 = data1.copy()
    df2 = data2.copy()
    df1.insert(0,'timestamp',list(map(func_stamp,df1['时间'])))
    df2.insert(0, 'timestamp', list(map(func_stamp, df2['时间'])))
    time_back = df1['timestamp'].unique().tolist()
    time_comp = df2['timestamp'].unique()
    filt_time = []
    for item in time_back:
        if min(np.abs(time_comp-item)) > time_range:
            filt_time.append(item)
    return df1[df1['timestamp'].isin(filt_time)].iloc[:,1:]#[col_data]
    
def lkj_time_filter(data_in,data_lkj,speed_thresh=1,time_jump=120,row_add=5, time_range=3):
    # print(data_lkj)
    """
    :param data_in:输入数据，为多维列表
    :param data_lkj:lkj数据，与data_in进行时间关联
    :param speed_thresh:限制速度阈值，作为筛选结果之用
    :param time_jump:lkj填充参数，对应的
    :param row_add:
    :param time_range:
    :return:
    """
    df = predata(data_in)
    col_data = ['time', 'frame']+list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
    df_lkj = LKJ_pre(data_lkj,time_jump,row_add)
    df = pd.merge(df,df_lkj,how='inner',left_on='time',right_on='时间')
    df = df[df['速度']>=speed_thresh].sort_values(by='timestamp').reset_index(drop=True)
    if df.shape[0] > 0:
        para = conti_check_v2(df)
        resu = select_proper(df,para,col_data,time_range)
    else:
        resu =[]
    return resu

def lkj_double_person(data_in,data_lkj,time_range=3,distance_add=30,time_continuty=10):
    # edited by chujp@20180911,主要进行'出站','进站'时刻数据的关联；
    """
    :param data_in:DataFrame,'时间， 帧号， 文件名，标签'，主数据源
    :param data_lkj:lkj数据，需要进行时间填充，副数据源
    :param time_range:持续时间阈值
    :param time_continuty:表示data_in的连续时间持续阈值
    :return:data_in和lkj联合后数据，数据列同'lkj_time_filter'结果，根据需要，后续可以通过添加：'出站'、'进站'的标签
    """
    # df = predata(data_in)
    df = dataContinutyCut(data_in,time_continuty=time_continuty)
    resu_gather = []
    if df.shape[0] > 0:
        col_data = ['time', 'frame']+list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
        names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
                 '前后', '管压', '缸压', '转速电流', '均缸1','均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
        # for item in '出站':
        for item in ['出站','进站']:
            if item == '出站':
                data_part = data_lkj[data_lkj['事件']==item]
                if data_part.shape[0] >= 2:
                    st_time = data_part.iloc[0,names.index('时间')]
                    ed_time = data_part.iloc[1,names.index('时间')]
                    df_lkj1 = pd.DataFrame(np.arange(func_stamp(st_time),func_stamp(ed_time)+1).reshape(-1,1),columns=['timestamp'])
            else:
                data_part = data_lkj[data_lkj['事件'] == item]
                if data_part.shape[0] >= 2:
                    st_time = data_part.iloc[-2, names.index('时间')]
                    ed_time = data_part.iloc[-1, names.index('时间')]
                    df_lkj1 = pd.DataFrame(np.arange(func_stamp(st_time), func_stamp(ed_time) + 1).reshape(-1, 1),columns=['timestamp'])
            try:
                df1 = pd.merge(df,df_lkj1,how='inner',on='timestamp')
                df1 = df1.sort_values(by=['timestamp','frame']).reset_index(drop=True)
                if df1.shape[0] > 0:
                    para = conti_check_v2(df1,distance=distance_add)#修改之处
                    resu1 = select_proper(df1,para,col_data,time_range)
                else:
                    resu1 = []
            except:
                resu1 = []
            resu_gather = resu_gather+resu1
    return resu_gather

def lkj_port_shift(data_in,data_lkj,st_in,et_in,time_range=20):
    #added by chujp @20180914
    """
    :param data_in:类似于yolo_event_relate中的第一个输入；
    :param data_lkj: pd.DataFrame,需要按照给出条件进行数据筛选
    :param time_range: 端变化情况下最短聚合时间
    :param st_in,et_in:表示对应的lkj检测事件范围，只对该时间段内的数据进行判断；
    :return: 若3中小于阈值，返回LKJ['时间', '其他']，时间为端结束时间
    """
    names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
             '前后', '管压', '缸压', '转速电流', '均缸1', '均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
    #names表示对应data_lkj的字段名
    df = predata(data_in)
    # col_data = ['time', 'frame']+list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
    resu_out = []
    #lkj数据有效性筛选
    data_lkj.insert(data_lkj.shape[1],'timestamp',list(map(func_stamp,data_lkj['时间'])))
    data_lkj = data_lkj[(data_lkj['timestamp'] > func_stamp(st_in)) & (data_lkj['timestamp'] < func_stamp(et_in))]
    end_reverse = ['I端开始','I端结束','II端开始','II端结束']
    data_lkj_fil1 = data_lkj[data_lkj['其他'].isin(end_reverse)]
    i = 0
    while i < data_lkj_fil1.shape[0]-1:
        try:
            if [data_lkj_fil1.iloc[i,names.index('其他')],data_lkj_fil1.iloc[i+1,names.index('其他')]] \
                in [['I端结束','II端开始'],['II端结束','I端开始']]:
                other_record = data_lkj_fil1.iloc[i,names.index('其他')]
                st_time = data_lkj_fil1.iloc[i,names.index('时间')]
                ed_time = data_lkj_fil1.iloc[i+1,names.index('时间')]
                df_lkj1 = pd.DataFrame(np.arange(func_stamp(st_time), func_stamp(ed_time) + 1).reshape(-1, 1),\
                                       columns=['timestamp'])
                df1 = pd.merge(df, df_lkj1, how='inner', on='timestamp')
                if df1.shape[0] < time_range:
                    resu_out.append([st_time,other_record])
            i +=1
        except:
            i += 1
    return resu_out

def yolo_speed_filter(data_in,data_lkj,speed_thresh=1,time_jump=120,row_add=5,i=1):
    # print(data_lkj)
    df = predata(data_in)
    col_data = ['time', 'frame']+list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
    motion = np.unique(df['col_'+str(i)])
    df_lkj = LKJ_pre(data_lkj,time_jump,row_add)
    df = pd.merge(df,df_lkj,how='inner',left_on='time',right_on='时间')
    df = df[df['速度']>=speed_thresh]#.sort_values(by='timestamp').reset_index(drop=True)
    out = []
    for item in motion:
        df_tocheck = df[df['col_'+str(i)]==item].sort_values(by='timestamp').reset_index(drop=True)
        if df_tocheck.shape[0] > 0:
            para = conti_check_v2(df_tocheck)
            resu = select_proper(df_tocheck,para,col_data)
            if len(resu) > 0:
                out = out+resu
    return out

# def time_filter(data_in):
#     df = predata(data_in)
#     para = conti_check_v2(df)
#     resu = select_proper(df,para)
#     return resu

# if __name__ == '__main__':
#     print(main(['2017-04-10 10:55:55']))
# # """test part"""
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



# df = pd.read_csv(r'C:\Users\chujp\Desktop\ImageData\sql_video\LKJ_data.txt',header=None)
# df.columns= ['时间','速度']
# test = LKJ_pre(df,120,5)

#yolo 数据结构：时间，帧号，文件名,动作
#lkj数据：时间，信号：绿灯、绿黄


# def yolo_signal_filter(data_yolo,df_lkj,motion_yolo,*lkj_condi):
#     col_yolo = ['time', 'frame', 'filename', 'motion'] + ['col_%s' % i for i in range(len(data_yolo[0]) - 4)]
#     df_yolo = pd.DataFrame(data_yolo,columns=col_yolo)
#     df_yolo.insert(0,'timestamp',list(map(func_stamp,df_yolo['time'])))
#     df_lkj.columns = ['time','signal']
#     df_lkj.insert(0,'timestamp',list(map(func_stamp,df_lkj['time'])))
#     able_lkj = []
#     for i in range(df_lkj.shape[0]):
#         if df_lkj.iloc[i,2] in lkj_condi:
#             able_lkj.extend([df_lkj.iloc[i,0]+j for j in range(-5,6)])
#     able_lkj_filter = list(np.unique(able_lkj))
#     df_yolo_fil1 = df_yolo[df_yolo['motion']==motion_yolo]
#     df_yolo_out = df_yolo_fil1[df_yolo_fil1['timestamp'].isin(able_lkj_filter)==False]
#     return df_yolo_out[col_yolo].values.tolist()
	

def lkj_event_exclude(data_in,data_lkj,eve_st,eve_ed,video_tm_range,time_range=1,time_thresh=5):
    """
    edited by chujp@20181009,对data_in和data_lkj进行数据关联：
    step1:对data_in时间进行前后拓宽，拓宽长度为time_range
    step2:筛选规则是选取lkj中进站、出站数据段,可能有多段
    step3:对step2中每段数据与step1处理数据进行集合做差，给出lkj多余时间超过5S的起始进站时间
    :param data_in:DataFrame,'时间， 帧号， 文件名，标签'，主数据源，对时间需要进行时间填充
    :param data_lkj:lkj数据，需要进行时间填充，输出结果数据源
    :param time_range:data_in补充时间长度
    :param time_thresh:lkj中多余时间点数约束阈值
    :param video_tm_range: 视屏时间范围，用于约束lkj时间范围
    :return:符合step3输出结果的符合条件的行：时间、事件、信号--列数据
    """
    resu_out = []
    df_lkj = data_lkj.copy()
    df_data = predata(data_in)
    st_time = func_stamp(video_tm_range[0])
    ed_time = func_stamp(video_tm_range[1])
    col_out = ['时间','事件','信号']
    names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
             '前后', '管压', '缸压', '转速电流', '均缸1', '均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
    time_data = df_data['timestamp'].values.tolist()
    time_data = [list(range(int(item)-time_range,int(item)+time_range+1)) for item in time_data]
    data_time_list = set(np.unique(sum(time_data,[])))
    df_lkj.insert(0,'timestamp',list(map(func_stamp,df_lkj['时间'])))
    df_lkj = df_lkj[(df_lkj['timestamp']>=st_time) &(df_lkj['timestamp']<=ed_time)]
    df_lkj = df_lkj.sort_values(by='timestamp').reset_index(drop=True)
    while df_lkj.shape[0] >0:
        if eve_st in df_lkj['事件'].unique() and eve_ed in df_lkj['事件'].unique():
            st_index = df_lkj[df_lkj['事件']==eve_st].index[0]
            et_index = df_lkj[df_lkj['事件']==eve_ed].index[0]
            df_part = df_lkj.loc[st_index:et_index]
            if len(set(df_part['timestamp'].values) - data_time_list) > time_thresh:
                resu_out.append(df_lkj.loc[st_index,col_out].values.tolist())
            df_lkj = df_lkj.loc[et_index+1:]
        else:
            break
    return resu_out

def arm_detect_filter(data_yolo,df_lkj_input,time_range,tm_bx_st,tm_bx_ed,motion_yolo,event_list,lkj_condi,speed_thresh):
    #motion_yolo为列表或者tuple
    df_lkj = df_lkj_input.copy()
    #print(data_yolo)
    col_yolo = ['time', 'frame', 'filename', 'motion'] + ['col_%s' % i for i in range(len(data_yolo[0]) - 4)]
    df_yolo = pd.DataFrame(data_yolo,columns=col_yolo)
    df_yolo.insert(0,'timestamp',list(map(func_stamp,df_yolo['time'])))
    if motion_yolo != []:
        df_yolo_fil = df_yolo[df_yolo['motion'].isin(motion_yolo)]
    else:
        df_yolo_fil = df_yolo
    df_lkj.columns = ['time','signal','event','speed']
    df_lkj.insert(0,'timestamp',list(map(func_stamp,df_lkj['time'])))
    st_time = func_stamp(time_range[0])
    ed_time = func_stamp(time_range[1])
    df_lkj_1 = df_lkj[(df_lkj['timestamp']>=st_time) &(df_lkj['timestamp']<=ed_time)]
    #print(event_list)
    if event_list != []:
        df_lkj_1 = df_lkj_1[df_lkj_1['event'].isin(event_list)].reset_index(drop=True)
    else:
        df_lkj_1 = df_lkj_1.reset_index(drop=True)
    df_lkj_fil = df_lkj_1[(df_lkj_1['signal'].isin(lkj_condi)) & (df_lkj_1['speed'] > speed_thresh)]
    #print(df_lkj_fil)
    
    #calcu the effect lkj continuous time
    lkj_list = df_lkj_fil['timestamp'].values.tolist()

    #out_lkj为对应不在yolo一定距离内的时间
    out_lkj = []
    for item in lkj_list:
        if df_yolo_fil[df_yolo_fil['timestamp'].isin([item+j for j in range(-tm_bx_st,tm_bx_ed)])].shape[0] == 0:
            out_lkj.append(item)

    df_lkj_out = df_lkj_fil[df_lkj_fil['timestamp'].isin(out_lkj)]
    #print(df_lkj_out)
    df_lkj_resu = df_lkj_out.drop_duplicates()
    return df_lkj_resu[['time','signal','event','speed']].values.tolist()


def arm_detect_include_filter(data_yolo,df_lkj_input,time_range,tm_bx_st,tm_bx_ed,motion_yolo,event_list,lkj_condi,speed_thresh):
    #motion_yolo为列表或者tuple
    df_lkj = df_lkj_input.copy()
    col_yolo = ['time', 'frame', 'filename', 'motion'] + ['col_%s' % i for i in range(len(data_yolo[0]) - 4)]
    df_yolo = pd.DataFrame(data_yolo,columns=col_yolo)
    df_yolo.insert(0,'timestamp',list(map(func_stamp,df_yolo['time'])))
    if motion_yolo != []:
        df_yolo_fil = df_yolo[df_yolo['motion'].isin(motion_yolo)]
    else:
        df_yolo_fil = df_yolo
    df_lkj.columns = ['time','signal','event','speed']
    df_lkj.insert(0,'timestamp',list(map(func_stamp,df_lkj['time'])))
    st_time = func_stamp(time_range[0])
    ed_time = func_stamp(time_range[1])
    df_lkj_1 = df_lkj[(df_lkj['timestamp']>=st_time) &(df_lkj['timestamp']<=ed_time)]
    if event_list != []:
        df_lkj_1 = df_lkj_1[df_lkj_1['event'].isin(event_list)].reset_index(drop=True)
    else:
        df_lkj_1 = df_lkj_1.reset_index(drop=True)

    df_lkj_fil = df_lkj_1[(df_lkj_1['signal'].isin(lkj_condi)) & (df_lkj_1['speed'] > speed_thresh)]
    #calcu the effect lkj continuous time
    lkj_list = df_lkj_fil['timestamp'].values.tolist()

    #out_lkj为对应不在yolo一定距离内的时间
    out_lkj = []
    for item in lkj_list:
        if df_yolo_fil[df_yolo_fil['timestamp'].isin([item+j for j in range(-tm_bx_st,tm_bx_ed)])].shape[0] > 0:
            out_lkj.append(item)

    df_lkj_out = df_lkj_fil[df_lkj_fil['timestamp'].isin(out_lkj)]

    df_lkj_resu = df_lkj_out.drop_duplicates()
    return df_lkj_resu[['time','signal','event','speed']].values.tolist()
