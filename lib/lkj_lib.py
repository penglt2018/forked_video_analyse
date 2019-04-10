#本程序建于2018-4-10
#函数是为了取出时间序列中持续超过5秒的时间点及对应的首尾时间
import pandas as pd
import time
import numpy as np
func_stamp = lambda x:time.mktime(time.strptime(x,'%Y-%m-%d %H:%M:%S')) #时间转为时间戳
func_time = lambda x:time.strftime('%Y-%m-%d %H:%M:%S',(time.localtime(x))) #时间戳转为时间
func_revis = lambda x:'2018-5-3 '+x.replace("'","") #special use, can be dropped.
func_duanhao = lambda x:x[:x.index('端')+1]

names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '前后',
         '牵引', '管压', '缸压', '转速电流', '均缸1','均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']

def predata(data_in):
    """
    :data_in:2d-list
    [ [标准时间2, 帧号2, ...],
      [标准时间1, 帧号1, ...],
                      ...
    ]

    :return: DataFrame, 按timestamp和帧号进行升序排列的索引为0开始，step为1的增长序列
        e.g. [ [标准时间1, 帧号1, ..., 时间戳1],
               [标准时间2, 帧号2, ..., 时间戳2],
                ...
             ]
    """
    col_add = list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
    #df = pd.DataFrame(data_in,columns=['time','frame','filename'])
    df = pd.DataFrame(data_in, columns=['time', 'frame']+col_add)
    df['timestamp'] = list(map(func_stamp, df['time']))
    df_out = df.sort_values(by=['timestamp','frame']).reset_index(drop=True)
    return df_out





#对data_in中数据连续时间段筛选，其中time_continuty表示连续时间长度
def dataContinutyCut(data_in,time_continuty=10):
    """
    选取持续时间超过time_continuty的时间段。
    :param data_in: 2d-list
                    [ [标准时间1, x1, ...],
                        ...
                      [标准时间10, x10, ...]
                      [标准时间11, x11, ...],
                      [标准时间13, x13, ...],
                      [标准时间14, x14, ...]
                    ]
    :param time_continuty:持续时间条件阈值(秒)；
    :return: DataFrame：
                    [ [标准时间1, x1, ...],
                        ...
                      [标准时间10, x10, ...]
                      [标准时间11, x11, ...]
                    ]
    """
    df_out = pd.DataFrame([])
    df = predata(data_in)
    para = conti_check_v2(df,distance=1)
    for item in para:
        if df.loc[item[1],'timestamp'] - df.loc[item[0],'timestamp'] >= time_continuty:
            df_out = df_out.append(df.loc[item[0]:item[1]])
    return df_out

def channel_filter(df_in,para,range_judge):
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
        before_t = df_local[df_local['stamp']<=point].sort_values(by='stamp',ascending=True).iloc[-2:]
        #before是dataFrame
        next_t = df_local[df_local['stamp']>point].sort_values(by='stamp',ascending=True).iloc[:2]
        if len(set(list(map(func_duanhao,before_t['state']))+list(map(func_duanhao,next_t['state'])))) == 1:
            # 判断时间节点所处前后时刻是否进行换端操作
            return list(map(func_duanhao,before_t['state']))[0]
        else:
            before_tt = before_t[before_t['state'].str.contains('结束')]
            next_tt = next_t[next_t['state'].str.contains('开始')]
            if next_tt['stamp'].values[0] - point <= range_judge*60:
                return func_duanhao(next_tt['state'].values[0])
            else:
                return func_duanhao(before_tt['state'].values[0])

def get_lkj_ab(df_lkj_in):
    """
    判断视频数据端号----适用于带A\B节的车
    param df_lkj_in: 输入为lkj的DataFrame,其中列名为names；
    return: 机车号所在行的“其他”最后一个元素
    """

    ele_out = df_lkj_in.loc[df_lkj_in['事件']=='机车号','其他'].values.tolist()
    if len(np.unique(ele_out)) != 1:
        return False
    else:
        if str(ele_out[0])[-1].isalpha():
            return str(ele_out[0])[-1]
        else:
            return False


def conti_check_v2(df_in, distance=1):
    """
    this function is made @ 2017/11/23, the latest vision.
    这个函数可以用于解决报违章间隔过短的问题。
    :param df_in: DataFrame,且索引为从0开始的整数序列***@condition must be satisfied.类似于
                    [ [tiemstamp1, x1, ...],
                      [timestamp2, x2, ...],
                      ...
                    ]
    :param distance:对应tiemstamp连续性阈值，决定断点多长时间算断开，若小于该时间，则算连续;
                    取值按照timestamp的精度；
    :return: list,每个元素对应包含df_in中一个连续段的起始和终止索引。
             eg.[[0, 10],
                  [11, 19],
                  ...]第一个元素表示：df_in的第0行到第10行为tiemstamp连续的。
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
    """
    df_in:DataFrame,
    time_jump：阈值，当lkj中时间跳跃过大时，则仅补齐端点前后row_add行；否则对缺失时间LKJ数据进行线性差值补齐
    row_add:由于Lkj和视频时间存在一定的偏差，row_add即为对Lkj补齐
    return:DataFrame:
        e.g. 若输入： time_jump = 3, row_add = 2        
            df_in列名：时间， 速度, x, y
            [[    时间1,    1,    ...],
             [    时间2,    5,    ...],
             [    时间4,    15, ...],
             [    时间10,    30,    ...]
            ]
        返回
            [[    时间1,    1,    ...],
             [    时间2,    5,    ...],
             [    时间3,    5+(15-5)/(4-2), ...],
             [    时间4,    15, ...],
             [    时间5,    15, ...],
             [    时间6,    15, ...],
             [    时间8,    30, ...],
             [    时间9,    30,    ...],
             [    时间10,    30,    ...]
            ]
    """
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

def select_proper(df_in,para_in,col_out, time_range, Mode_in = 'Situ1'):

    """
    @revised records:20190312
    本函数取出df_in中满足持续时间>=time_range秒的首尾时刻的col_out列数据
    :param df_in: Lkj与模型结果按照时间关联的2D-DataFrame
                e.g. df [[timestamp1，frame1, x, y, ...],
                         [timestamp2, frame2, x, y, ...],
                         ...
                        ]
    :param para_in: 对df_in的timestamp列进行conti_Check_v2产生的列表
                e.g. 2-list
                    eg.[[0, 10],
                         [11, 12],
                         ...
                        ]
    :param col_out：1-D list: 输出数据的字段名。
    :param time_range: int: 持续时间阈值，单位秒。
    :param Mode_in: 默认是按照20190313之前的逻辑运算，mode_in进行赋值时，则为选出其中前述条件的DF数据段，并进行关联。
    :return: 2-D list: 在df_in中取para_in中对应index的timestamp差满足连续时间阈值的time_range
                       条件的col_out列。
                    e.g. 若 time_range = 2,
                         [[timestamp1, frame1, x1, y1, ..., timestamp11, frame11, x11, y11...],
                         ...
                         ]
    """
    if Mode_in == 'Situ1':
        out = []
        # col_out = ['time','frame','filename']
        for item in para_in:
            if df_in.ix[item[1],'timestamp'] - df_in.ix[item[0],'timestamp'] >= time_range:
               element_start = [df_in.ix[item[0],col] for col in col_out]
               element_end = [df_in.ix[item[1],col] for col in col_out]
               out.append(element_start + element_end)
    else:
        out = pd.DataFrame([])
        for item in para_in:
            if df_in.ix[item[1],'timestamp'] - df_in.ix[item[0],'timestamp'] >= time_range:
                out = out.append(df_in.loc[item[0]:item[1]])
        out = out.sort_values(by='timestamp').reset_index(drop=True)
    return out

def model_time_exclude(data1,data2,time_range):
    """
    去掉data1中时间与data2相等的行，时间相等由time_range决定。
    param data1:带时间列的lkj DF
    param data2:带有时间列的DF
    param time_range: 计算多少差值算相等。
    return: 与data2中时间不相等(不相等由time_range决定)的行
    """
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

def time_filter(data_in,data_lkj,speed_thresh=1,time_jump=120,row_add=5, time_range=3):
    # print(data_lkj)
    """
    :param data_in:2d-list
            [ [标准时间2, 帧号2, ...],
              [标准时间1, 帧号1, ...],
                              ...
            ]
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
        #resu = select_proper(df,para,col_data,time_range)
        resu = select_proper(df, para, ['time', 'frame', '速度'], time_range)
    else:
        resu =[]
    return resu

def single_person(data_in,data_lkj,time_range=3,distance_add=30,time_continuty=10):
    # edited by chujp@20190313,主要进行'出站','进站'时刻数据的关联；
    """
        列车运行要求第一个出站到第二个出站；以及倒数第二个进站到最后一个进站要求双人值乘，
        本函数找出要求中只有一个人值乘的违章。
    :param data_in: 2-D DataFrame,'时间， 帧号， 文件名，标签'，主数据源
                   e.g.  [ [标准时间2, 帧号2, ...],
                             [标准时间1, 帧号1, ...],
                              ...
                         ]
    :param data_lkj: 2-D DataFrame: lkj完整数据，带列名，需要进行时间填充。
    :param time_range:int: 用于选出违章结束-起始时间大于time_range。
    :param distance_add:int: 对应tiemstamp连续性阈值，决定报违章断点多长时间算断开，若小于该时间，则算连续。
                        e.g. 若distance_add = 10, time_range = 3，
                             1,2,3,7,8,9 秒均报违章，则最终只会报1-9秒一条违章。
    :param time_continuty:int: 用于对模型报出结果进行连续型筛选，滤除模型报出的毛刺。
                        e.g. 选出模型结果持续报time_continuty以上的数据。

    :return: 2-D list: select_proper函数返回结果。 
                    e.g. [[timestamp1, frame1, x1, y1, ..., timestamp11, frame11, x11, y11...],
                         ...
                         ]
    """
    # df = predata(data_in)
    df = dataContinutyCut(data_in,time_continuty=time_continuty)    # 要求data_in中相同违章连续报相同违章超过time_continuty秒，才算违章。
    resu_gather = []
    if df.shape[0] > 0:
        col_data = ['time', 'frame']+list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
        # names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
        # #          '前后', '管压', '缸压', '转速电流', '均缸1','均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
        # names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '前后',
        #          '牵引', '管压', '缸压', '转速电流', '均缸1','均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
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
                    
                     #修改之处
                    resu_local = select_proper(df1,para,col_data,time_range, Mode_in = 'Situ2')
                    para = conti_check_v2(resu_local,distance=distance_add)
                    resu1 = [[resu_local.ix[item[0],col] for col in col_data]+ [resu_local.ix[item[1],col] for col in col_data] for item in para]
                else:
                    resu1 = []
            except:
                resu1 = []
            resu_gather = resu_gather+resu1
    return resu_gather

# def single_person(data_in,data_lkj,time_range=3,distance_add=30,time_continuty=10):
#     # edited by chujp@20180911,主要进行'出站','进站'时刻数据的关联；
#     """
#         列车运行要求第一个出站到第二个出站；以及倒数第二个进站到最后一个进站要求双人值乘，
#         本函数找出要求中只有一个人值乘的违章。
#     :param data_in: 2-D DataFrame,'时间， 帧号， 文件名，标签'，主数据源
#                    e.g.  [ [标准时间2, 帧号2, ...],
#                              [标准时间1, 帧号1, ...],
#                               ...
#                          ]
#     :param data_lkj: 2-D DataFrame: lkj完整数据，带列名，需要进行时间填充。
#     :param time_range:int: 违章起始结束时间大于time_range。
#     :param time_continuty:表示data_in的连续时间持续阈值
#     :return:data_in和lkj联合后数据，数据列同'time_filter'结果，根据需要，后续可以通过添加：'出站'、'进站'的标签
#     """
#     # df = predata(data_in)
#     df = dataContinutyCut(data_in,time_continuty=time_continuty)    # 要求data_in中相同违章连续报相同违章超过time_continuty秒，才算违章。
#     resu_gather = []
#     if df.shape[0] > 0:
#         col_data = ['time', 'frame']+list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
#         names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
#                  '前后', '管压', '缸压', '转速电流', '均缸1','均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
#         # for item in '出站':
#         for item in ['出站','进站']:
#             if item == '出站':
#                 data_part = data_lkj[data_lkj['事件']==item]
#                 if data_part.shape[0] >= 2:
#                     st_time = data_part.iloc[0,names.index('时间')]
#                     ed_time = data_part.iloc[1,names.index('时间')]
#                     df_lkj1 = pd.DataFrame(np.arange(func_stamp(st_time),func_stamp(ed_time)+1).reshape(-1,1),columns=['timestamp'])
#             else:
#                 data_part = data_lkj[data_lkj['事件'] == item]
#                 if data_part.shape[0] >= 2:
#                     st_time = data_part.iloc[-2, names.index('时间')]
#                     ed_time = data_part.iloc[-1, names.index('时间')]
#                     df_lkj1 = pd.DataFrame(np.arange(func_stamp(st_time), func_stamp(ed_time) + 1).reshape(-1, 1),columns=['timestamp'])
#             try:
#                 df1 = pd.merge(df,df_lkj1,how='inner',on='timestamp')
#                 df1 = df1.sort_values(by=['timestamp','frame']).reset_index(drop=True)
#                 if df1.shape[0] > 0:

#                     para = conti_check_v2(df1,distance=distance_add) #修改之处
#                     resu1 = select_proper(df1,para,col_data,time_range)
#                 else:
#                     resu1 = []
#             except:
#                 resu1 = []
#             resu_gather = resu_gather+resu1
#     return resu_gather

def channel_shift(data_in,lkj_data,st_in,et_in,time_range=20):
    #added by chujp @20180914
    """
    data_in为司机室只有一个司机的数据，若换端过程中司机室单人值乘状态持续时间少于time_range秒，则报出对应的lkj中X端结束的时间及"其他"列
    :param data_in:类似于yolo_event_relate中的第一个输入；
    :param data_lkj: pd.DataFrame,需要按照给出条件进行数据筛选
    :param time_range: 端变化情况下最短聚合时间
    :param st_in,et_in:表示对应的lkj检测时间范围，只对该时间段内的数据进行判断；
    :return: 2D-list, 若3中小于阈值，返回LKJ['时间', '其他']，时间为端结束时间
    """
    # names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
    #          '前后', '管压', '缸压', '转速电流', '均缸1', '均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
    #names表示对应data_lkj的字段名
    df = predata(data_in)
    # col_data = ['time', 'frame']+list(map(lambda x:'col_'+str(x),range(len(data_in[0])-2)))
    resu_out = []
    #lkj数据有效性筛选
    data_lkj = lkj_data.copy()
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
    """


    """
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
   
    本程序用于检测副司机未立岗。
    data_in 为副司机立岗模型返回结果。
    data_lkj 经过操作后，为每一段进出站时间数据。
    若副司机全程立岗，则lkj进出站全程时间 - 副司机立岗时间 = 0
    time_thresh 用于判断lkj进出站全程时间 - 副司机立岗时间 > time_thresh秒则认为未立岗。

    :param data_in:DataFrame,'时间， 帧号， 文件名，标签'，副司机立岗检测结果
    :param data_lkj:lkj数据，需要进行时间填充，输出结果数据源
    :param time_range:检测结果的有效时间(也就是单条检测结果的持续时间)
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
    # names = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
    #          '前后', '管压', '缸压', '转速电流', '均缸1', '均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
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

def arm_detect_filter(model_data, df_lkj_input, time_range, motion, event_list, lkj_condi,
                      speed_thresh, distance_thresh):
    """
    该函数用于检测手比相关动作。 motion用于筛选模型返回手比动作（e.g. 手比、握拳），event_list用于筛选lkj事件（e.g. 过分相、进出站），lkj_condi用于
    筛选lkj信号灯，distance_thresh 用于判断距离event_list事件点的距离。

    函数返回在距离event_list事件点前distance_thresh米内的未作手比的lkj事件时间点与lkj信息（时间、信号、事件、距离）。

    进行lkj和yolo结果的数据关联，分为两部分数据：
    YOLO：转为DataFrame，进行motion过滤
    LKJ：首先对lkj数据：“事件”进行event_list查找，按照里程和速度进行数据段筛选，找出各数据段起始时间和结束事件，
    对model_data时间列进行筛选，筛选后数据行数==0的输出对应的LKJ事件时间；
    :param model_data:2d-list,yolo 检测结果数据
    :param df_lkj_input:lkj输入数据,全字段数据
    :param time_range:1d-list,含函数关注的lkj数据时间范围，e.g. ['2019-3-15 09:56:10', '2019-3-15 15:05:00']
    :param motion_yolo:1d-list, yolo检测动作list, 用于model_data 筛选
    :param event_list:1d-list, lkj事件筛选集合
    :param lkj_condi:1d-list, lkj信号筛选条件
    :param speed_thresh:float, lkj速度筛选条件
    :param distance_thresh:离程限制,单位为m
    :return:与yolo过滤后数据时间匹配不上的lkj事件所在行集合
    """
    # motion为列表或者tuple
    # name_lkj = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
    #              '前后', '管压', '缸压', '转速电流', '均缸1','均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
    out_col = ['时间', '信号', '事件', '距离']
    # print(model_data)
    col_yolo = ['time', 'frame', 'motion'] + ['col_%s' % i for i in range(len(model_data[0]) - 4)]
    df_yolo = pd.DataFrame(model_data, columns=col_yolo)
    df_yolo.insert(0, 'timestamp', list(map(func_stamp, df_yolo['time'])))
    if motion != []:
        df_yolo_fil = df_yolo[df_yolo['motion'].isin(motion)]
    else:
        df_yolo_fil = df_yolo
    df_lkj_cp = df_lkj_input.copy()
    df_lkj = pd.DataFrame(df_lkj_cp, columns=names)
    df_lkj.insert(0, 'timestamp', list(map(func_stamp, df_lkj['时间'])))
    st_time = func_stamp(time_range[0])
    ed_time = func_stamp(time_range[1])
    df_lkj = df_lkj[(df_lkj['timestamp'] >= st_time) & (df_lkj['timestamp'] <= ed_time)].sort_values(by='timestamp')\
        .reset_index(drop=True)
    # print(event_list)
    #start to calcu the out lkj row
    out_lkj = []
    lkj_end_list = df_lkj[df_lkj['事件'].isin(event_list) & (df_lkj['信号'].isin(lkj_condi))].index.tolist()
    for key,item in enumerate(lkj_end_list):
        if item != 0:
            if key == 0:
                df_lkj_part = df_lkj.loc[0:item]


                df_lkj_part = df_lkj_part.loc[pd.notnull(df_lkj_part['里程']).index.tolist()]
                df_lkj_part.insert(df_lkj_part.shape[1],'distanceToInitial',np.abs(df_lkj_part['里程']-df_lkj_part.loc[item,'里程'])*1000)
                df_lkj_part.insert(df_lkj_part.shape[1],'distance_judge',df_lkj_part['distanceToInitial']-distance_thresh)

                ##通过event_list选择第一个终止行
                df_lkj_addix = df_lkj_part.iloc[:-1]
                index_stop = df_lkj_addix[df_lkj_addix['事件'].isin(event_list)].index.tolist()
                if len(index_stop) == 0:
                    row_stop = 0
                else:
                    row_stop = index_stop[-1]

                df_lkj_part2 = df_lkj_part[df_lkj_part['distance_judge']>=0]
                if df_lkj_part2.shape[0] != 0:
                    row_select = df_lkj_part2[df_lkj_part2['distance_judge']==df_lkj_part2['distance_judge'].min()].index.tolist()[0]
                else:
                    row_select = 0

                row_select = max(row_stop,row_select)

                df_lkj_fil_1 = df_lkj_part.loc[row_select:item]
                df_lkj_fil_2 = df_lkj_fil_1[df_lkj_fil_1['速度'] > speed_thresh]
                if df_lkj_fil_2.shape[0]>0:
                    st_time_local = df_lkj_fil_2['timestamp'].min()
                    ed_time_local = df_lkj_fil_2['timestamp'].max()
                    if df_yolo_fil[(df_yolo_fil['timestamp'] >= st_time_local) & (df_yolo_fil['timestamp'] <= ed_time_local)].shape[0] == 0:
                        out_lkj.append(item) # 取LKJ关联数据最后一行
                        #out_lkj.append(row_select) # 取LKJ关联数据最开始一行
            else:
                df_lkj_part = df_lkj.loc[lkj_end_list[key-1]+1:item]

                df_lkj_part = df_lkj_part.loc[pd.notnull(df_lkj_part['里程']).index.tolist()]
                df_lkj_part.insert(df_lkj_part.shape[1],'distanceToInitial',np.abs(df_lkj_part['里程']-df_lkj_part.loc[item,'里程'])*1000)
                df_lkj_part.insert(df_lkj_part.shape[1],'distance_judge',df_lkj_part['distanceToInitial']-distance_thresh)
                df_lkj_part2 = df_lkj_part[df_lkj_part['distance_judge'] >= 0]
                if df_lkj_part2.shape[0] != 0:
                    row_select = df_lkj_part2[df_lkj_part2['distance_judge'] == df_lkj_part2['distance_judge'].min()].index.tolist()[0]
                else:
                    row_select = lkj_end_list[key-1]+1
                ##通过event_list选择第一个终止行
                df_lkj_addix = df_lkj_part.iloc[:-1]
                index_stop = df_lkj_addix[df_lkj_addix['事件'].isin(event_list)].index.tolist()
                if len(index_stop) == 0:
                    row_stop = 0
                else:
                    row_stop = index_stop[-1]
                row_select = max(row_stop,row_select)
                df_lkj_fil_1 = df_lkj_part.loc[row_select:item]
                df_lkj_fil_2 = df_lkj_fil_1[df_lkj_fil_1['速度'] > speed_thresh]
                if df_lkj_fil_2.shape[0]>0:
                    st_time_local = df_lkj_fil_2['timestamp'].min()
                    ed_time_local = df_lkj_fil_2['timestamp'].max()
                    if df_yolo_fil[(df_yolo_fil['timestamp'] >= st_time_local) & (df_yolo_fil['timestamp'] <= ed_time_local)].shape[0] == 0:
                        out_lkj.append(item) # 取LKJ关联数据最后一行
                        #out_lkj.append(row_select) # 取LKJ关联数据最开始一行
    return df_lkj.loc[out_lkj,out_col].values.tolist()


def arm_detect_include_filter(model_data, df_lkj_input, time_range, motion, event_list, lkj_condi,
                      speed_thresh, distance_thresh):
    """
    与arm_detect_filter相反，函数返回在距离event_list事件点前distance_thresh米内的有手比的lkj事件时间点与lkj信息（时间、信号、事件、距离）
    """
    # motion为列表或者tuple
    # name_lkj = ['序号', '事件', '时间', '里程', '其他', '距离', '信号机', '信号', '速度', '限速', '零位', '牵引',
    #              '前后', '管压', '缸压', '转速电流', '均缸1','均缸2', 'dummy1', 'dummy2', 'dummy3', 'dummy4']
    out_col = ['时间', '信号', '事件', '距离']
    # print(model_data)
    col_yolo = ['time', 'frame', 'motion'] + ['col_%s' % i for i in range(len(model_data[0]) - 4)]
    df_yolo = pd.DataFrame(model_data, columns=col_yolo)
    df_yolo.insert(0, 'timestamp', list(map(func_stamp, df_yolo['time'])))
    if motion != []:
        df_yolo_fil = df_yolo[df_yolo['motion'].isin(motion)]
    else:
        df_yolo_fil = df_yolo
    df_lkj_cp = df_lkj_input.copy()
    df_lkj = pd.DataFrame(df_lkj_cp, columns=names)
    df_lkj.insert(0, 'timestamp', list(map(func_stamp, df_lkj['时间'])))
    st_time = func_stamp(time_range[0])
    ed_time = func_stamp(time_range[1])
    df_lkj = df_lkj[(df_lkj['timestamp'] >= st_time) & (df_lkj['timestamp'] <= ed_time)].sort_values(by='timestamp')\
        .reset_index(drop=True)
    # print(event_list)
    #start to calcu the out lkj row
    out_lkj = []
    lkj_end_list = df_lkj[df_lkj['事件'].isin(event_list) & (df_lkj['信号'].isin(lkj_condi))].index.tolist()
    for key,item in enumerate(lkj_end_list):
        if item != 0:
            if key == 0:
                df_lkj_part = df_lkj.loc[0:item]

                df_lkj_part = df_lkj_part.loc[pd.notnull(df_lkj_part['里程']).index.tolist()]
                df_lkj_part.insert(df_lkj_part.shape[1],'distanceToInitial',np.abs(df_lkj_part['里程']-df_lkj_part.loc[item,'里程'])*1000)
                df_lkj_part.insert(df_lkj_part.shape[1],'distance_judge',df_lkj_part['distanceToInitial']-distance_thresh)

                df_lkj_part2 = df_lkj_part[df_lkj_part['distance_judge']>=0]
                if df_lkj_part2.shape[0] != 0:
                    row_select1 = df_lkj_part2[df_lkj_part2['distance_judge']==df_lkj_part2['distance_judge'].min()].index.tolist()[0]
                else:
                    row_select1 = 0
                ##通过event_list选择第一个终止行
                df_lkj_addix = df_lkj_part.iloc[:-1]
                index_stop = df_lkj_addix[df_lkj_addix['事件'].isin(event_list)].index.tolist()
                if len(index_stop) == 0:
                    row_stop = 0
                else:
                    row_stop = index_stop[-1]
                row_select = max(row_stop,row_select1)

                df_lkj_fil_1 = df_lkj_part.loc[row_select:item]
                df_lkj_fil_2 = df_lkj_fil_1[df_lkj_fil_1['速度'] > speed_thresh]
                if df_lkj_fil_2.shape[0] > 0:
                    st_time_local = df_lkj_fil_2['timestamp'].min()
                    ed_time_local = df_lkj_fil_2['timestamp'].max()
                    if df_yolo_fil[(df_yolo_fil['timestamp'] >= st_time_local) & (df_yolo_fil['timestamp'] <= ed_time_local)].shape[0] > 0:
                        out_lkj.append(item) # 取LKJ关联数据最后一行
                        #out_lkj.append(row_select) # 取LKJ关联数据最开始一行
            else:
                df_lkj_part = df_lkj.loc[lkj_end_list[key-1]+1:item]

                df_lkj_part = df_lkj_part.loc[pd.notnull(df_lkj_part['里程']).index.tolist()]
                df_lkj_part.insert(df_lkj_part.shape[1],'distanceToInitial',np.abs(df_lkj_part['里程']-df_lkj_part.loc[item,'里程'])*1000)
                df_lkj_part.insert(df_lkj_part.shape[1],'distance_judge',df_lkj_part['distanceToInitial']-distance_thresh)

                df_lkj_part2 = df_lkj_part[df_lkj_part['distance_judge'] >= 0]
                if df_lkj_part2.shape[0] != 0:
                    row_select1 = df_lkj_part2[df_lkj_part2['distance_judge'] == df_lkj_part2['distance_judge'].min()].index.tolist()[0]
                else:
                    row_select1 = lkj_end_list[key-1]+1
                ##通过event_list选择第一个终止行
                df_lkj_addix = df_lkj_part.iloc[:-1]
                index_stop = df_lkj_addix[df_lkj_addix['事件'].isin(event_list)].index.tolist()
                if len(index_stop) == 0:
                    row_stop = 0
                else:
                    row_stop = index_stop[-1]
                row_select = max(row_stop,row_select1)
                df_lkj_fil_1 = df_lkj_part.loc[row_select:item]
                df_lkj_fil_2 = df_lkj_fil_1[df_lkj_fil_1['速度'] > speed_thresh]
                if df_lkj_fil_2.shape[0]>0:
                    st_time_local = df_lkj_fil_2['timestamp'].min()
                    ed_time_local = df_lkj_fil_2['timestamp'].max()
                    if df_yolo_fil[(df_yolo_fil['timestamp'] >= st_time_local) & (df_yolo_fil['timestamp'] <= ed_time_local)].shape[0] > 0:
                        out_lkj.append(item) # 取LKJ关联数据最后一行
                        #out_lkj.append(row_select) # 取LKJ关联数据最开始一行
    return df_lkj.loc[out_lkj,out_col].values.tolist()

