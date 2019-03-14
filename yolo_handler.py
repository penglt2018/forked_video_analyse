#coding:utf-8

import sys, os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
#os.environ.pop('CUDA_VISIBLE_DEVICES')
#os.environ["CUDA_VISIBLE_DEVICES"]="1"
import lib.common as common
import time
import pandas as pd
import lib.lkj_lib as LKJLIB
import datetime

os_sep = os.path.sep
gpu_idx = 1
yolo_logger = common.get_logger('yolo')

def init():
    ''' Initializing function
        Input:
                None
        return:
                None
    '''
    yolo_logger.info('Initializing')
    # get darkent parameters
    global dn, net, meta
    dn_path, mdl_cfg, weights, meta_f = common.get_yolo_config()
    
    cellphone_weights = './yolov3_32025000.weights'
    cellphone_cfg = './lyc_cellphone.cfg'
    cellphone_meta = './lyc_cellphone_coco.data'

    # check darknet path
    common.file_check(dn_path + os_sep + 'darknet.py', yolo_logger, 'darknet.py NOT found!', 8)
    common.file_check(mdl_cfg, yolo_logger, 'yolo cfg file set wrong!', 9)
    common.file_check(weights, yolo_logger, 'yolo weight file set wrong!', 9)
    common.file_check(meta_f, yolo_logger, 'yolo meta file set wrong!', 9)
    yolo_logger.info('Yolo parameters get successfully')
    # import darknet
    sys.path.append(dn_path)
    print(dn_path)
    import darknet as dn
    dn.set_gpu(gpu_idx)
    yolo_logger.info('GPU set to {0}'.format(gpu_idx))
    yolo_logger.info('Darknet import successfully')

    # initialize darknet network
    meta = dn.load_meta(meta_f.encode('utf-8'))
    yolo_logger.info('Darknet meta load successfully')
    net = dn.load_net(mdl_cfg.encode('utf-8'), weights.encode('utf-8'), 0)
    yolo_logger.info('Darknet network load successfully')
    
    #global cell_net, cell_meta
    #import darknet as cell_dn
    #cell_dn.set_gpu(0)
    # cell_meta = dn.load_meta(cellphone_meta.encode('utf-8'))
    # cell_net = dn.load_net(cellphone_cfg.encode('utf-8'), cellphone_weights.encode('utf-8'), 0)

def init_cellphone():
    ''' Initializing function
        Input:
                None
        return:
                None
    '''
    yolo_logger.info('Initializing')
    # get darkent parameters
    global dn, net, meta
    dn_path, mdl_cfg, weights, meta_f = common.get_yolo_config()
    
    cellphone_weights = './yolov3_32095000.weights'
    #cellphone_weights = './yolov3_32025000.weights'
    cellphone_cfg = './lyc_cellphone.cfg'
    cellphone_meta = './lyc_cellphone_coco.data'

    # check darknet path
    common.file_check(dn_path + os_sep + 'darknet.py', yolo_logger, 'darknet.py NOT found!', 8)
    common.file_check(mdl_cfg, yolo_logger, 'yolo cfg file set wrong!', 9)
    common.file_check(weights, yolo_logger, 'yolo weight file set wrong!', 9)
    common.file_check(meta_f, yolo_logger, 'yolo meta file set wrong!', 9)
    yolo_logger.info('Yolo parameters get successfully')
    # import darknet
    sys.path.append(dn_path)
    print(dn_path)
    import darknet as dn
    #dn.set_gpu(0)
    dn.set_gpu(gpu_idx)
    yolo_logger.info('GPU set to {0}'.format(gpu_idx))
    yolo_logger.info('Darknet import successfully')

    # initialize darknet network
    meta = dn.load_meta(cellphone_meta.encode('utf-8'))
    yolo_logger.info('Darknet meta load successfully')
    net = dn.load_net(cellphone_cfg.encode('utf-8'), cellphone_weights.encode('utf-8'), 0)
    yolo_logger.info('Darknet network load successfully')
    
    #global cell_net, cell_meta
    #import darknet as cell_dn
    #cell_dn.set_gpu(0)
    # cell_meta = dn.load_meta(cellphone_meta.encode('utf-8'))
    # cell_net = dn.load_net(cellphone_cfg.encode('utf-8'), cellphone_weights.encode('utf-8'), 0)

def exe_yolo_cellphone(frame_mat, yolo_result, video_info, fps):
    ''' Function for executing yolo detect function and
        append the predict result into a list frame by frame
        Input: 
                frame_mat: [ [pixel_mat], frame_index ]
                yolo_result: array to store yolo result 
                video_info: information related to the video
                fps: video fps
        return:
                rt_flag: True / False
    '''
    global yolo_logger, dn, net, meta
    yolo_logger.info('Preparing for running yolo')
    rt_flag = True
    video_st_time = video_info[1]
    yolo_logger.info('Video start time get successfully')
    video_name = video_info[3]
    yolo_logger.info('Video name get successfully')
    try:
        yolo_logger.info('Running yolo detect function to video {0}'.format(video_name))
        # yolo_rt = [ label, prob, (coordinate) ]
        for pix_mat, frame_idx in frame_mat:
            yolo_rt = dn.detect(net, meta, pix_mat,thresh=.5)
            if yolo_rt != []:
                for j in range(len(yolo_rt)):
                    if yolo_rt[j][0].decode('utf-8') == 'cell phone':
                        common.append_result(yolo_result, frame_idx, fps, video_st_time, 'cellphone')

        # for pix_mat, frame_idx in frame_mat:
        #     cell_rt = dn.detect(cell_net, cell_meta, pix_mat)
        #     if cell_rt != []:
        #         for j in range(len(cell_rt)):
        #             if cell_rt[j][0].decode('utf-8') == 'cell phone':
        #                 common.append_result(yolo_result, frame_idx, fps, video_st_time, 'cellphone')
            # else:
            #     yolo_logger.warning('no result return by yolo for picture {0}'.format(ptc))
    except Exception:
        yolo_logger.error('Yolo execution failed with video: {0}, frame index: {1}, pixel_mat: {2}'.format(video_name, frame_idx, pix_mat), exc_info=True)
        rt_flag = False

    if rt_flag == True:
        yolo_logger.info('Yolo detect function execute successfully')
    return rt_flag

def exe_yolo(frame_mat, yolo_result, video_info, fps):
    ''' Function for executing yolo detect function and
        append the predict result into a list frame by frame
        Input: 
                frame_mat: [ [pixel_mat], frame_index ]
                yolo_result: array to store yolo result 
                video_info: information related to the video
                fps: video fps
        return:
                rt_flag: True / False
    '''
    global yolo_logger, dn, net, meta
    yolo_logger.info('Preparing for running yolo')
    rt_flag = True
    video_st_time = video_info[1]
    yolo_logger.info('Video start time get successfully')
    video_name = video_info[3]
    yolo_logger.info('Video name get successfully')
    try:
        yolo_logger.info('Running yolo detect function to video {0}'.format(video_name))
        # yolo_rt = [ label, prob, (coordinate) ]
        for pix_mat, frame_idx in frame_mat:
            yolo_rt = dn.detect(net, meta, pix_mat)
            if yolo_rt != []:
                for j in range(len(yolo_rt)):
                    common.append_result(yolo_result, frame_idx, fps, video_st_time, yolo_rt[j][0].decode('utf-8'))

        # for pix_mat, frame_idx in frame_mat:
        #     cell_rt = dn.detect(cell_net, cell_meta, pix_mat)
        #     if cell_rt != []:
        #         for j in range(len(cell_rt)):
        #             if cell_rt[j][0].decode('utf-8') == 'cell phone':
        #                 common.append_result(yolo_result, frame_idx, fps, video_st_time, 'cellphone')
            # else:
            #     yolo_logger.warning('no result return by yolo for picture {0}'.format(ptc))
    except Exception:
        yolo_logger.error('Yolo execution failed with video: {0}, frame index: {1}, pixel_mat: {2}'.format(video_name, frame_idx, pix_mat), exc_info=True)
        rt_flag = False

    if rt_flag == True:
        yolo_logger.info('Yolo detect function execute successfully')
    return rt_flag

def match_lkj(lkj_file, video_info, yolo_result):
    ''' Function for correlating yolo predicted result with
        LKJ information which is used to judge driver violation
        Input:
                lkj_file:       LKJ file with path
                video_info:     video related inforation stored in mysql
                yolo_result:    return list by yolo 
        return:
                match_flg:  flag for checking
                final_result: combining list from each result list
    '''
    global yolo_logger
    match_flg = 0   # 0 is normal

    yolo_logger.info('Reading lkj data {0}'.format(lkj_file))
    lkj_rd_rt = common.get_lkj(lkj_file)
    if lkj_rd_rt[0] == False:
        yolo_logger.error(lkj_rd_rt[1])
        match_flg = 1   # lkj reading error
        yolo_logger.error('LKJ data read error {0}'.format(lkj_file))
    else:
        lkj_df = lkj_rd_rt[2]
        yolo_logger.info(lkj_rd_rt[1])
        # get video time
        video_st_time = video_info[1]
        video_ed_time = video_info[2]
        video_name = video_info[3]
        #print(video_st_time, video_ed_time)
        yolo_logger.info('Seperating YOLO predict result')
        no_break = [x for x in yolo_result if x[-1] == 'no_break']
        yolo_logger.info('No_break list build successfully')
        #sleep = [x for x in yolo_result if x[-1] == 'sleep_1' or x[-1] == 'sleep_2']
        #yolo_logger.info('Sleep list build successfully')
        cellphone = [x for x in yolo_result if x[-1] == 'cellphone' ]
        #cellphone = yolo_result
        yolo_logger.info('Cellphone list build successfully')
        stand_2 = [x for x in yolo_result if x[-1] == 'stand_2' ]
        yolo_logger.info('Stand_2 list build successfully')

        leave_1 = [x for x in yolo_result if x[-1] == 'leave_1' ]
        yolo_logger.info('Leave_1 list build successfully')

        leave_2 = [x for x in yolo_result if x[-1] == 'leave_2' ]
        yolo_logger.info('Leave_2 list build successfully')

        '''
        result list after filtering by LKJ
        final list format:
        [ violate_st_tm, violate_st_frame_idx, label,
            violate_ed_tm, violate_ed_frame_idx, label ]
        '''
        no_break_final = []
        sleep_final = []
        cellphone_final = []
        stand_2_final = []
        leave_1_final = []
        single_person_final = []

        # no_break filt
        if no_break != [] and no_break != [[]]:
            try:
                no_break_final = LKJLIB.time_filter(no_break,lkj_df,speed_thresh=1, time_range=5*60)
                yolo_logger.info('LKJ data and no_break result join successfully')
            except Exception:
                yolo_logger.error('LKJ data and no_break result join failed', exc_info=True)
                match_flg = 2
            if no_break_final != []:
                no_break_final = common.channel_filt(no_break_final, lkj_df, video_name)

        # # sleep check
        # if sleep != [] and sleep != [[]]:
        #     try:
        #         sleep_final = LKJLIB.time_filter(sleep,lkj_df,speed_thresh=0, time_range=300)
        #         yolo_logger.info('LKJ data and sleep result join successfully')
        #     except Exception:
        #         yolo_logger.error('LKJ data and sleep result join failed'.exc_info=True)
        #         match_flg = 3 

        # cellphone check
        if cellphone != [] and cellphone != [[]]:
            try:
                cellphone_final = LKJLIB.time_filter(cellphone,lkj_df,speed_thresh=0, time_range=20)
                yolo_logger.info('LKJ data and cellphone result join successfully')
            except Exception as e:
                yolo_logger.error('LKJ data and cellphone result join failed', exc_info=True)
                match_flg = 4 

        # stand_2 check
        if stand_2 != [] and stand_2 != [[]]:
            try:
                stand_2_final = LKJLIB.lkj_event_exclude(stand_2, lkj_df,'进站','出站',[video_st_time, video_ed_time], time_range=2,time_thresh=10)
                yolo_logger.info('LKJ data and stand_2 result join successfully')
            except Exception as e:
                yolo_logger.error('LKJ data and stand_2 result join failed', exc_info=True)
                match_flg = 5

        if leave_1 != [] and leave_1 != [[]]:
            try:
                leave_1_final = LKJLIB.time_filter(leave_1, lkj_df, speed_thresh=0, time_range=10)
                yolo_logger.info('LKJ data and leave result join successfully')
            except Exception:
                yolo_logger.error('LKJ data and leave result join failed', exc_info=True)
                match_flg = 6
            if leave_1_final != []:
                #print(leave_final)
                leave_1_final = common.channel_filt(leave_1_final, lkj_df, video_name)

        if leave_2 != [] and leave_2 != [[]]:
            try:
                single_person_final = LKJLIB.single_person(leave_2, lkj_df)
                yolo_logger.info('LKJ data and single drive result join successfully')
            except Exception:
                yolo_logger.error('LKJ data and single drive result join failed', exc_info=True)
                match_flg = 7

            # # execute change channel same time checking rules
            # try:
            #     channel_shift_final = LKJLIB.channel_shift(leave_2, lkj_df, video_st_time, video_ed_time)
            #     openpose_logger.info('LKJ data and channel_shift result join successfully')
            # except Exception:
            #     openpose_logger.error('LKJ data and channel_shift result join failed', exc_info=True)
            #     match_flg = 5


    final_result = ([no_break_final] + [sleep_final] + [cellphone_final] + [stand_2_final] + [leave_1_final] + [single_person_final])
    return match_flg, final_result
        
def store_result(final_result, video_info, mysql_db, video_obj):
    ''' Function for storing violation result into mysql database 
        and save violate frames to a given path
        Input:
                final_result: violate result list
                video_info: video related information
                mysql_db: database connector object
                video_obj: custom video object
        return:
                True / False flag
    '''
    global yolo_logger
    # resolve 
    no_break_final, sleep_final, cellphone_final, stand_2_final, leave_1_final,single_person_final = final_result
    video_name = video_info[3]
    store_flag = True

    # add no_break result to db
    now_time=datetime.datetime.now().strftime('%Y-%m-%d')
    #if failed to get the syetem_time
    if not now_time:
        yolo_logger.error('failed to get the system time')
        store_flag = False
        return store_flag
    else:
        store_path_prefix=os_sep+'home'+os_sep+'guest'+os_sep+'store'+os_sep+now_time+os_sep
    
    if no_break_final == []:
        yolo_logger.info('No_break NOT detected to video {0}'.format(video_name))
    else:
        if common.add_to_db(mysql_db, video_info, no_break_final, 'violate_result.report', '主司机左手未握大闸', video_obj, store_path_prefix+'no_break') == False:
            yolo_logger.error('no_break result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            yolo_logger.info('no_break result insert to db successfully')
    
    # # add sleep result to db
    # if sleep_final == []:
    #     yolo_logger.info('Sleep NOT detected to video {0}'.format(video_name))
    # else:
    #     if common.add_to_db(mysql_db, video_info, sleep_final, 'violate_result.report', '平躺睡觉', video_obj, 'store/sleep') == False:
    #         yolo_logger.error('Sleep result insert to db failed to video {0}'.format(video_name))
    #         store_flag = False
    #     else:
    #         yolo_logger.info('Sleep result insert to db successfully')
    
    # add cellphone result to db
    if cellphone_final == []:
        yolo_logger.info('Cellphone NOT detected to video {0}'.format(video_name))
    else:
        cellphone_move = [ i for i in cellphone_final if i[2] > 0 ]
        cellphone_stop = [ i for i in cellphone_final if i[2] == 0]
        if common.add_to_db(mysql_db, video_info, cellphone_move, 'violate_result.report', '玩手机(运行)', video_obj, store_path_prefix+'cellphone') == False or\
            common.add_to_db(mysql_db, video_info, cellphone_stop, 'violate_result.report', '玩手机(停车)', video_obj, store_path_prefix+'cellphone') == False:
            yolo_logger.error('Cellphone result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            yolo_logger.info('Cellphone result insert to db successfully')
    
    # add stand_2 result to db
    if stand_2_final == []:
        yolo_logger.info('Stand_2 violation NOT detected to video {0}'.format(video_name))
    else:
        if common.add_to_db(mysql_db, video_info, stand_2_final, 'violate_result.report', '副司机进站未立岗', video_obj) == False:
            yolo_logger.error('Stand_2 result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            yolo_logger.info('Stand_2 result insert to db successfully')

    return store_flag

    if leave_1_final == []:
        yolo_logger.info('Leave_1 violation NOT detected to video {0}'.format(video_name))
    else:
        if common.add_to_db(mysql_db, video_info, leave_1_final, 'violate_result.report', '主司机离岗', video_obj, store_path_prefix+'leave_1') == False:
            yolo_logger.error('Leave_1 result insert to db failed to video {0}'.format(video_name))
        else:
            yolo_logger.info('Leave_1 result insert to db successfully')

    if single_person_final == []:
        yolo_logger.info('Single person NOT detected to video {0}'.format(video_name))
    else:
        if common.add_to_db(mysql_db, video_info, single_person_final, 'violate_result.report', '单人值乘', video_obj, store_path_prefix+'single_driver') == False:
            yolo_logger.error('Single person result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            yolo_logger.info('Single person result insert to db successfully')


