#coding:utf-8
'''
Program Name: Run Model
File Name: run_model.py
Creation Date: Apr 2018
Programmer: XINWU LIU, BANGFAN LIU
Abstract: This program extract pos keypoints from json file as input
          and run models
Entry Condition: N/A
Exit Condition: N/A
Example: N/A
Program Message: N/A
Remarks: N/A
Amendment Hisotry:
            Version:
            Date:
            Programmer:
            Reason:
'''
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
#os.environ["CUDA_VISIBLE_DEVICES"]="0"
import lib.common as common
import numpy as np
import pandas as pd
from model.right.pos_recog_model import wrong_head as wrong_head_right
from model.back.pos_recog_model import wrong_head as wrong_head_back
from model.right_back.pos_recog_model import wrong_head as wrong_head_right_back
from model.right_back.pos_recog_model import arm_detect as arm_detect_right_back
from model.right_back.pos_recog_model import get_angle
from model.right_back.pos_recog_model import nap_detect as nap_detect_right_back
import time
import lib.lkj_lib as LKJLIB
import lib.coord_handler as coord_handler
import sys
import tensorflow as tf
import datetime

os_sep = os.path.sep
openpose_logger = common.get_logger('openpose')


def init():
    ''' Initializing
        Input:
                None
        return:
                None
    '''
    global openpose, box_info
    openpose_logger.info('Initializing')
    # tensorflow initialization
    openpose_logger.info('Tensorflow initializing')
    global sess, y_conv, keep_prob, x_conv
    sess = tf.InteractiveSession()
    sess.run(tf.global_variables_initializer())
    new_saver = tf.train.import_meta_graph('./modelsave/model.ckpt-6801.meta')
    model_file=tf.train.latest_checkpoint('./modelsave/')
    new_saver.restore(sess, model_file)
    graph = tf.get_default_graph()
    x_conv = graph.get_operation_by_name('x').outputs[0]
    #y_ = graph.get_operation_by_name('y_').outputs[0]
    keep_prob = graph.get_operation_by_name('keep_prob').outputs[0]
    y_conv = tf.get_collection('pred_network')[0]

    # get openpose path and parameters
    # op_params is a dict
    op_path, op_params = common.get_openpose_config()
    common.file_check(op_path + os_sep + 'openpose.py', openpose_logger, 'openpose.py NOT found!', 8)
    common.file_check('config/reference_box.ini', openpose_logger, 'Reference_box NOT set!', 41)
    sys.path.append(op_path)
    import openpose as op
    openpose = op.OpenPose(op_params)
    print("gpu is set to {0}".format(op_params['num_gpu_start']))
    # get main driver and co-driver coordinates range
    try:
        box_info = coord_handler.get_reference_data('config/reference_box.ini')
        openpose_logger.info('Box config data read successfully')
    except Exception:
        openpose_logger.error('Box config data read failed', exc_info=True)

    openpose_logger.info('checking box config data')
    if box_info == None: common.raise_error('Error: box_info is empty', 42)



def normlization(np_arr, width, height):
    ''' Function for normlizate pose keypoints to range 0 - 1
        Input:
                np_arr: a (_,25,3) shape np array
                        format (num_plp, human part, xyconfidence)
                width:  frame width
                height: frame height
        return:
                None
    '''
    if np_arr != []:
        np_arr[:,:,0] = np_arr[:,:,0] / (width-1)
        np_arr[:,:,1] = np_arr[:,:,1] / (height-1)

def data_trans(pos_keypoints_arr):
    ''' Function for transforming pose keypoints array returned
        by openpose to a custom list used for tensorflow model
        Input:
                pos_keypoints_arr:  numpy array returned by openpose
                                    including all human poses in one frame
        return:
                rt_pos_list: custom pose keypoints list with all human in one frame
    '''
    rt_pos_list = []
    for one_per_pos_keypoints in pos_keypoints_arr:
        pos_list = one_per_pos_keypoints.flatten().tolist()
        x = [ 0 if pos_list[x]==0 else pos_list[x] for x in range(len(pos_list)) if x%3 == 0 ]
        y = [ 0 if pos_list[y]==0 else pos_list[y] for y in range(len(pos_list)) if y%3 == 1 ]

        cus_pos_keypoints = [[[x[13],x[12],x[7],x[6],x[5],x[1],x[0]],\
                          [x[0],x[1],x[8],x[9],x[10],x[11],x[22]],\
                          [x[0],x[1],x[2],x[3],x[4],x[9],x[10]],\
                          [x[8],x[1],x[0],x[15],x[16],x[17],x[18]],\
                          [x[0],x[1],x[5],x[6],x[7],x[12],x[13]],\
                          [x[0],x[1],x[8],x[12],x[13],x[14],x[19]],\
                          [x[10],x[9],x[4],x[3],x[2],x[1],x[0]]],\

                          [[y[13],y[12],y[7],y[6],y[5],y[1],y[0]],\
                          [y[0],y[1],y[8],y[9],y[10],y[11],y[22]],\
                          [y[0],y[1],y[2],y[3],y[4],y[9],y[10]],\
                          [y[8],y[1],y[0],y[15],y[16],y[17],y[18]],\
                          [y[0],y[1],y[5],y[6],y[7],y[12],y[13]],\
                          [y[0],y[1],y[8],y[12],y[13],y[14],y[19]],\
                          [y[10],y[9],y[4],y[3],y[2],y[1],y[0]]]]
        rt_pos_list.append(cus_pos_keypoints)
    #test_pos_keypoints = numpy.array(coord_arrange).astype('float32')
    return rt_pos_list

def exe_openpose(frame_mat, openpose_result, video_info, fps, video_width, video_height):
    ''' Function for executing openpose detect function and
        append the predict result into a list frame by frame
        Input:
                frame_mat: [ [pixel_mat], frame_index ]
                openpose: array to store openpose result
                video_info: information related to the video
                fps: video fps
                video_width: frame width
                video_height: frame height
        return:
                rt_flag: True / False
    '''
    global openpose_logger, box_info, openpose, sees, y_conv
    openpose_logger.info('Prepare for running openpose')
    rt_flag = True
    video_st_time = video_info[1]
    video_name = video_info[3]
    train_type = str(video_info[4])
    train_num = str(video_info[5])
    channel = str(video_info[6])
    camera_loc = video_info[0].split('/')[2]    # camera location: right / right_back / back
    #print(box_info)
    #print(train_type, train_num, channel)
    main_drive_box_data = [x[-4:] for x in box_info if x[0] == train_type and \
                           x[1] == train_num and \
                           x[2] == '1' and \
                           x[3] == channel ]
    if main_drive_box_data == [] or main_drive_box_data == [[]] :
        openpose_logger.error('Main drive coord range get failed {0}'.format(main_drive_box_data))
        rt_flag = False
    else:
        openpose_logger.info('Main drive coord range get successfully {0}'.format(main_drive_box_data))
        openpose_logger.info('Executing openpose to video {0}'.format(video_name))

        for pix_mat, frame_idx in frame_mat:
            try:
                # return pose keypoints list with all human in pix_mat
                pos_keypoint_arr = openpose.forward(pix_mat, display=False)
                #print(pos_keypoint_arr)
                # normlizate all human's pose keypoints
                normlization(pos_keypoint_arr, video_width, video_height)
                # filter main driver from all human
                # main_driver_rt = [ pos_keypoints 1-d list, num person ]
                main_driver_rt = coord_handler.get_driver_coord(pos_keypoint_arr, main_drive_box_data[0])
                if len(main_driver_rt) != 76:
                    openpose_logger.error('Driver pose keypoints list shape wrong {0}')
                    rt_flag = False
                pos_flag = True
            except Exception:
                openpose_logger.error('Driver pose keypoints return failed {0}'.format(pos_keypoint_arr), exc_info=True)
                pos_flag = False
                rt_flag = False

            if pos_flag == True and rt_flag == True:
                main_driver_pos = main_driver_rt[0:-1]
                num_plp = main_driver_rt[-1]
                #print(main_driver_pos)
                if num_plp == 1:                # single driver
                    common.append_result(openpose_result, frame_idx, fps, video_st_time, '单人值乘')
                if main_driver_pos[4] == -1:    # no person detected
                    common.append_result(openpose_result, frame_idx, fps, video_st_time, '主司机离岗')
                else:
                    # execute wrong head model
                    wrong_head_rt = 0
                    wrong_head_model = 'wrong_head_' + camera_loc
                    try:
                        wrong_head_rt = eval(wrong_head_model)(main_driver_pos)
                        # if frame_idx == 6496:
                        #     print(wrong_head_rt, video_name, main_driver_pos)
                    except Exception:
                        openpose_logger.error('Wrong head detect model {0} execute failed with {1}'.format(eval(wrong_head_model).__module__, main_driver_pos), exc_info=True)
                        rt_flag = False
                    if wrong_head_rt != 0: # model output wrong head
                        common.append_result(openpose_result, frame_idx, fps, video_st_time, '主司机偏头')

                    # excute nap model
                    nap_rt = 0
                    nap_model = 'nap_detect_' + camera_loc
                    try:
                        nap_rt = eval(nap_model)(main_driver_pos)
                    except Exception:
                        openpose_logger.error('Nap detect model {0} execute failed with {1}'.format(eval(nap_model).__module__, main_driver_pos), exc_info=True)
                        rt_flag = False
                    if nap_rt != 0:
                        common.append_result(openpose_result, frame_idx, fps, video_st_time, '主司机盹睡')

                    # execute arm check model
                    arm_detect_rt = 0
                    arm_detect_model = 'arm_detect_' + camera_loc
                    try:
                        arm_detect_rt = eval(arm_detect_model)(main_driver_pos)
                        #if frame_idx >= 5816 and frame_idx <= 5824:
                            #print("================ {0} {1}".format(frame_idx, arm_detect_rt))
                    except Exception:
                        openpose_logger.error('Arm detect model {0} execute failed with {1}'.format(eval(arm_detect_model).__name__, main_driver_pos), exc_info=True)
                        rt_flag = False
                    if arm_detect_rt != 1 : # no person and normal case
                        if arm_detect_rt == 2:
                            common.append_result(openpose_result, frame_idx, fps, video_st_time, '主司机手比')
                        elif arm_detect_rt == 3:
                            common.append_result(openpose_result, frame_idx, fps, video_st_time, '主司机握拳')
                        elif arm_detect_rt == 4 or arm_detect_rt == 0:
                            common.append_result(openpose_result, frame_idx, fps, video_st_time, '主司机非标准手比')
                        else:
                            openpose_logger.error('Arm detect model return code out of range: {0}'.format(main_driver_pos))
                            rt_flag = False

            # execute sleep detect model with tensorflow
            if pos_keypoint_arr != []:
                try:
                    # tranform pos_keypoints_arr to custom pose keypoints
                    cus_pos_keypoints_list = data_trans(pos_keypoint_arr)
                    # cus_pos_keypoints_list = data_trans(main_driver_pos)
                    #print(cus_pos_keypoints_list)
                    # since all people should NOT sleep, all people's pos
                    # keypoints are used for detecting
                    for cus_pos in cus_pos_keypoints_list:
                        tf_model_result = sess.run(y_conv, feed_dict={x_conv: np.array([cus_pos], dtype=np.float32), keep_prob:1.0}).tolist()[0]
                        prob = max(tf_model_result)
                        max_index = tf_model_result.index(prob)
                        # label 1 = sleep, 0 = normal & sit, 2 = stand
                        if max_index == 1 and prob > 0.8:
                            common.append_result(openpose_result, frame_idx, fps, video_st_time, '平躺睡觉')
                except Exception:
                    openpose_logger.error('Sleep detect model failed with {0}'.format(pos_keypoint_arr), exc_info=True)
                    rt_flag = False


        if not 'wrong_head_rt' in locals().keys():
            openpose_logger.warning('Wrong head model does not execute to video {0}'.format(video_name))
            rt_flag = False
        if not 'arm_detect_rt' in locals().keys():
            openpose_logger.warning('Arm detect model does not execute to video {0}'.format(video_name))
            rt_flag = False
        if rt_flag == True:
            openpose_logger.info('Openpose model execute finish to video {0}'.format(video_name))
        else:
            openpose_logger.error('Openpose model execute failed to video {0}'.format(video_name))
        return rt_flag

def match_lkj(lkj_file, video_info, op_result):
    ''' Function for correlating openpose predicted result with
        LKJ information which is used to judge driver violation
        Input:
                lkj_file:       LKJ file with path
                video_info:     video related inforation stored in mysql
                op_result:      return list by openpose
        return:
                match_flg:  flag for checking
                final_result: combining list from each result list
    '''
    global openpose_logger
    #print(op_result)
    match_flg = 0   # 0 is normal

    openpose_logger.info('Reading lkj data {0}'.format(lkj_file))
    lkj_rd_rt = common.get_lkj(lkj_file)
    if lkj_rd_rt[0] == False:
        openpose_logger.error(lkj_rd_rt[1])
        match_flg = 1   # lkj reading error
        openpose_logger.error('LKJ data read error {0}'.format(lkj_file))
    else:
        lkj_df = lkj_rd_rt[2]
        openpose_logger.info(lkj_rd_rt[1])
        # get video time
        video_st_time = video_info[1]
        video_ed_time = video_info[2]
        video_name = video_info[3]
        #print(video_st_time, video_ed_time)

        openpose_logger.info('Seperating Openpose predict result')
        leave_result = [ i for i in op_result if i[-1] == '主司机离岗' ]
        openpose_logger.info('Leave list build successfully')
        wrong_head_result = [ i for i in op_result if i[-1] == '主司机偏头' ]
        openpose_logger.info('Wrong head list build successfully')
        num_people_result = [ i for i in op_result if i[-1] == '单人值乘' ]
        openpose_logger.info('Single drive list build successfully')
        point_forward_result = [ i for i in op_result if i[-1] == '主司机手比' ]
        openpose_logger.info('Point list build successfully')
        fist_result = [ i for i in op_result if i[-1] == '主司机握拳' ]
        openpose_logger.info('Fist list build successfully')
        other_gesture_result = [ i for i in op_result if i[-1] == '主司机非标准手比' ]
        openpose_logger.info('Other guesture list build successfully')
        sleep_result = [i for i in op_result if i[-1] == '平躺睡觉' ]
        openpose_logger.info('Sleep list build successfully')
        nap_result = [i for i in op_result if i[-1] == '主司机盹睡']
        openpose_logger.info('Nap list build successfully')

        leave_final = []
        wrong_head_final = []
        single_person_final = []
        channel_shift_final = []
        point_forward_final = []
        point_forward_include_final = []
        fist_final = []
        fist_include_final = []
        point_forward_other_final = []
        fist_other_final = []
        sleep_final = []
        nap_final = []

        # # leave filt
        # if leave_result != []:
        #     #print(leave_result)
        #     try:
        #         leave_final = LKJLIB.time_filter(leave_result, lkj_df, speed_thresh=0, time_range=10)
        #         openpose_logger.info('LKJ data and leave result join successfully')
        #     except Exception:
        #         openpose_logger.error('LKJ data and leave result join failed', exc_info=True)
        #         match_flg = 2
        #     if leave_final != []:
        #         #print(leave_final)
        #         leave_final = common.channel_filt(leave_final, lkj_df, video_name)

        # execute wrong head judge ruls
        if wrong_head_result != []:
            #print(wrong_head_result)
            try:
                wrong_head_final = LKJLIB.time_filter(wrong_head_result, lkj_df, speed_thresh=0, time_range=5)
                openpose_logger.info('LKJ data and wrong head result join successfully')
            except Exception:
                openpose_logger.error('LKJ data and worng head result join failed', exc_info=True)
                match_flg = 3
            #if wrong_head_final != []:
            #    #print(wrong_head_final)
            #    wrong_head_final = common.channel_filt(wrong_head_final, lkj_df, video_name)

        # execute single person rules
        # if num_people_result != []:
        #     try:
        #         single_person_final = LKJLIB.single_person(num_people_result, lkj_df)
        #         openpose_logger.info('LKJ data and single drive result join successfully')
        #     except Exception:
        #         openpose_logger.error('LKJ data and single drive result join failed', exc_info=True)
        #         match_flg = 4

        #     # execute change channel same time checking rules
        #     try:
        #         channel_shift_final = LKJLIB.channel_shift(num_people_result, lkj_df, video_st_time, video_ed_time)
        #         openpose_logger.info('LKJ data and channel_shift result join successfully')
        #     except Exception:
        #         openpose_logger.error('LKJ data and channel_shift result join failed', exc_info=True)
        #         match_flg = 5

        # execute sleep rules
        if sleep_result != []:
            try:
                sleep_final = LKJLIB.time_filter(sleep_result, lkj_df, speed_thresh=0, time_range=120)
                openpose_logger.info('LKJ data and sleep result join successfully')
                #print(sleep_final)
            except Exception:
                openpose_logger.error('LKJ data and sleep result join failed', exc_info=True)
                match_flg = 6

        # execute nap rules
        if nap_result != []:
            try:
                nap_final = LKJLIB.time_filter(nap_result, lkj_df, speed_thresh=0, time_range=180)
                openpose_logger.info('LKJ data and nap result join successfully')
                #print(nap_final)
            except Exception:
                openpose_logger.error('LKJ data and nap result join failed', exc_info=True)
                match=9

            #if nap_final != []:
            #    nap_final = common.channel_filt(nap_final, lkj_df, video_name)

        # execute point forward rules
        point_forward_comb = point_forward_result + other_gesture_result + fist_result
        if point_forward_comb != []:
            try:
                point_forward_final = LKJLIB.arm_detect_filter(model_data=point_forward_comb,\
                                                            df_lkj_input=lkj_df,\
                                                            time_range=[video_st_time, video_ed_time],\
                                                            motion=[],\
                                                            event_list=['出站', '进站', '过分相'],\
                                                            lkj_condi=['绿灯', '绿黄灯','双黄灯','黄闪黄','黄灯'],\
                                                            speed_thresh=1,\
                                                            distance_thresh=800)
                #print(point_forward_comb)
                #print(point_forward_final)
                #print(point_forward_result)
                if point_forward_result != []:
                    point_forward_include_final = LKJLIB.arm_detect_include_filter(model_data=point_forward_result,\
                                                                                df_lkj_input=lkj_df,\
                                                                                time_range=[video_st_time, video_ed_time],\
                                                                                motion=[],\
                                                                                event_list=['出站', '进站', '过分相'],\
                                                                                lkj_condi=['绿灯', '绿黄灯','双黄灯','黄闪黄','黄灯'],\
                                                                                speed_thresh=1,\
                                                                                distance_thresh=800)

                    #point_forward_include_final = common.channel_filt(point_forward_include_final, lkj_df, video_name)
                #print(other_gesture_result)
                if other_gesture_result != []:
                    if point_forward_include_final != [] and point_forward_include_final != [[]]:
                        lkj_signal_filt = LKJLIB.model_time_exclude(lkj_df, pd.DataFrame(point_forward_include_final,columns=['时间', '信号', '事件', '距离']),0)
                    else:
                        lkj_signal_filt = lkj_df

                    point_forward_other_final = LKJLIB.arm_detect_include_filter(model_data=other_gesture_result, \
                                                                                df_lkj_input=lkj_signal_filt, \
                                                                                time_range=[video_st_time, video_ed_time],\
                                                                                motion=[],\
                                                                                event_list=['出站', '进站','过分相'],\
                                                                                lkj_condi=['绿灯', '绿黄灯','双黄灯','黄闪黄','黄灯'],\
                                                                                speed_thresh=1,\
                                                                                distance_thresh=800)
                openpose_logger.info('LKJ data and point result join successfully')
            except Exception:
                openpose_logger.error('LKJ data and point result join failed', exc_info=True)
                match_flg = 7

        # execute fist rules
        fist_comb = fist_result + other_gesture_result
        if fist_comb != []:
            try:
                fist_final = LKJLIB.arm_detect_filter(model_data=fist_comb, \
                                                    df_lkj_input=lkj_df, \
                                                    time_range=[video_st_time, video_ed_time], \
                                                    motion=[], \
                                                    event_list=['机车信号变化'], \
                                                    lkj_condi=['红灯'],
                                                    speed_thresh=1,\
                                                    distance_thresh=800)
                if fist_result != []:
                    fist_include_final = LKJLIB.arm_detect_include_filter(model_data=fist_result, \
                                                                        df_lkj_input=lkj_df, \
                                                                        time_range=[video_st_time, video_ed_time], \
                                                                        motion=[], \
                                                                        event_list=['机车信号变化'], \
                                                                        lkj_condi=['红灯'],
                                                                        speed_thresh=1,\
                                                                        distance_thresh=800)

                    #fist_include_final = common.channel_filt(fist_include_final, lkj_df, video_name)
                if other_gesture_result != []:
                    if fist_include_final != [] and fist_include_final != [[]]:
                        lkj_signal_filt = LKJLIB.model_time_exclude(lkj_df, pd.DataFrame(fist_include_final,columns=['时间', '信号', '事件', '距离']),0)
                    else:
                        lkj_signal_filt = lkj_df
                    fist_other_final = LKJLIB.arm_detect_include_filter(model_data=other_gesture_result, \
                                                                        df_lkj_input=lkj_signal_filt, \
                                                                        time_range=[video_st_time, video_ed_time], \
                                                                        motion=[], \
                                                                        event_list=['机车信号变化'], \
                                                                        lkj_condi=['红灯'],
                                                                        speed_thresh=1,\
                                                                        distance_thresh=800)
                openpose_logger.info('LKJ data and fist result join successfully')
            except Exception:
                openpose_logger.error('LKJ data and fist result join failed', exc_info=True)
                match_flg = 8

    final_result = ([leave_final] + [wrong_head_final] + [single_person_final] + [channel_shift_final] + [sleep_final] + [nap_final] + [point_forward_final] + [fist_final])
    include_final_result = ([point_forward_include_final] + [fist_include_final] + [point_forward_other_final] + [fist_other_final])
    return match_flg, final_result, include_final_result

# def model_rt_check(match_rt, path):
#     global openpose_logger
#     rt = True
#     openpose_logger.info('function model_rt_check: checking lkj and custom model matching result')
#     if match_rt == 1:
#         openpose_logger.error('function model_rt_check: lkj data read error under path {0}'.format(path))
#         rt = False
#     elif match_rt == 2:
#         openpose_logger.error('function model_rt_check: lkj data and leave result matching error under path {0}'.format(path))
#         rt = False
#     elif match_rt == 3:
#         openpose_logger.error('function model_rt_check: lkj data and wrongHead result matching error under path {0}'.format(path))
#         rt = False
#     elif match_rt == 4:
#         openpose_logger.error('function model_rt_check: lkj data and double person result matching error under path {0}'.format(path))
#         rt = False
#     elif match_rt == 5:
#         openpose_logger.error('function model_rt_check: lkj data and port shift result matching error under path {0}'.format(path))
#         rt = False
#     elif match_rt == 6:
#         openpose_logger.warning('function model_rt_check: lkj signal info get failed under path {0}'.format(path))
#     elif match_rt == 7:
#         openpose_logger.error('function model_rt_check: lkj data and point_forward_result matching error under path {0}'.format(path))
#         rt = False
#     elif match_rt == 8:
#         openpose_logger.error('function model_rt_check: lkj data and fist_result matching error under path {0}'.format(path))
#         rt = False
#     elif match_rt < 0 or match_rt > 8:
#         openpose_logger.error('function model_rt_check: lkj match program error: return out of range under path {0}'.format(path))
#         rt = False
#     return rt

def store_result(final_result, video_info, mysql_db, video_obj, final_include_result=None):
    ''' Function for storing violation result into mysql database
        and save violate frames to a given path
        Input:
                final_result: violate result list
                video_info: video related information
                mysql_db: database connector object
                video_obj: custom video object
                final_include_result: non-violate result list
        return:
                True / False flag
    '''
    global openpose_logger
    leave_final, wrong_head_final, single_person_final, channel_shift_final, sleep_final, nap_final, point_forward_final, fist_final = final_result
    if final_include_result:
        point_forward_include_final, fist_include_final, point_forward_other_final, fist_other_final = final_include_result
    video_name = video_info[3]
    store_flag = True
    # get the system_time
    now_time=datetime.datetime.now().strftime('%Y-%m-%d')
    #if failed to get the syetem_time
    if not now_time:
        openpose_logger.error('failed to get the system time')
        store_flag = False
        return store_flag
    else:
        store_path_prefix=os_sep+'home'+os_sep+'guest'+os_sep+'store'+os_sep+now_time+os_sep

        # add leave result to db
    if leave_final == []:
        openpose_logger.info('Leave NOT detected to video {0}'.format(video_name))
    else:
        # if common.add_to_db(mysql_db, video_info, leave_final, 'violate_result.report', '主司机离岗', video_obj, 'store/leave') == False:
        if common.add_to_db(mysql_db, video_info, leave_final, 'violate_result.report', '主司机离岗', video_obj, store_path_prefix+'leave') == False:
            openpose_logger.error('Leave result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            openpose_logger.info('Leave result insert to db successfully')
    # add wrong head result to db
    if wrong_head_final == []:
        openpose_logger.info('Wrong head NOT detected to video {0}'.format(video_name))
    else:
        wronghead_move = [i for i in wrong_head_final if i[2] > 0 ]
        #wronghead_stop = [i for i in wrong_head_final if i[2] == 0]
        if common.add_to_db(mysql_db, video_info, wronghead_move, 'violate_result.report', '主司机偏头(运行)', video_obj, store_path_prefix+'wronghead') == False : #or \
            #common.add_to_db(mysql_db, video_info, wronghead_stop, 'violate_result.report', '主司机偏头(停车)', video_obj, store_path_prefix+'wronghead') == False:
            openpose_logger.error('WrongHead result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            openpose_logger.info('WrongHead result insert to db successfully')

    # add double person result to db
    if single_person_final == []:
        openpose_logger.info('Single person NOT detected to video {0}'.format(video_name))
    else:
        if common.add_to_db(mysql_db, video_info, single_person_final, 'violate_result.report', '单人值乘', video_obj, store_path_prefix+'single_driver') == False:
            openpose_logger.error('Single person result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            openpose_logger.info('Single person result insert to db successfully')
    # add port shift result to db
    if channel_shift_final == []:
        openpose_logger.info('Channel shift NOT detected to video {0}'.format(video_name))
    else:
        if common.add_to_db(mysql_db, video_info, channel_shift_final, 'violate_result.report', '同时换端', video_obj) == False:
            openpose_logger.error('Channel shift result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            openpose_logger.info('Channel shift result insert to db successfully')
    # add sleep result to db
    if sleep_final == []:
        openpose_logger.info('Sleep NOT detected to video {0}'.format(video_name))
    else:
        sleep_move = [ i for i in sleep_final if i[2] > 0 ]
        sleep_stop = [ i for i in sleep_final if i[2] == 0 ]
        #if common.add_to_db(mysql_db, video_info, sleep_move, 'violate_result.report', '平躺睡觉(运行)', video_obj, 'store/sleep') == False or \
            #common.add_to_db(mysql_db, video_info, sleep_stop, 'violate_result.report', '平躺睡觉(停车)', video_obj, 'store/sleep') == False:
        if common.add_to_db(mysql_db, video_info, sleep_move, 'violate_result.report', '平躺睡觉(运行)', video_obj, store_path_prefix+'sleep') == False or \
            common.add_to_db(mysql_db, video_info, sleep_stop, 'violate_result.report', '平躺睡觉(停车)', video_obj, store_path_prefix+'sleep') == False:
            openpose_logger.error('Sleep result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            openpose_logger.info('Sleep result insert to db successfully')
    # add nap result to db
    if nap_final == []:
        openpose_logger.info('Nap NOT detected to video {0}'.format(video_name))
    else:
        nap_move = [ i for i in nap_final if i[2] > 0 ]
        nap_stop = [ i for i in nap_final if i[2] == 0 ]
        if common.add_to_db(mysql_db, video_info, nap_move, 'violate_result.report', '主司机盹睡(运行)', video_obj, store_path_prefix+'nap') == False or \
            common.add_to_db(mysql_db, video_info, nap_stop, 'violate_result.report', '主司机盹睡(停车)', video_obj, store_path_prefix+'nap') == False:
            #common.add_to_db(mysql_db, video_info, nap_stop, 'violate_result.report', '主司机盹睡(停车)', video_obj, 'store/nap') == False:
            openpose_logger.error('Nap result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            openpose_logger.info('Nap result insert to db successfully')
    # add point forward result to db
    if point_forward_final == []:
        openpose_logger.info('Point_forward NOT violate detected to video {0}'.format(video_name))
    else:
        if common.add_to_db(mysql_db, video_info, point_forward_final, 'violate_result.report', '主司机未手比', video_obj) == False:
            openpose_logger.error('Point_forward result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            openpose_logger.info('Point forward result insert to db successfully')
    # add fist result to db
    if fist_final == []:
        openpose_logger.info('Fist NOT detected to video {0}'.format(video_name))
    else:
        if common.add_to_db(mysql_db, video_info, fist_final, 'violate_result.report', '主司机未摇臂', video_obj) == False:
            openpose_logger.error('Fist result insert to db failed to video {0}'.format(video_name))
            store_flag = False
        else:
            openpose_logger.info('Fist result insert to db successfully')

    # addtional arm detect check
    if point_forward_include_final != []:
        common.add_to_db(mysql_db, video_info, point_forward_include_final, 'violate_result.report', '主司机手比', video_obj)
    if fist_include_final != []:
        common.add_to_db(mysql_db, video_info, fist_include_final, 'violate_result.report', '主司机摇臂', video_obj)

    other_final = point_forward_other_final + fist_other_final
    if other_final != []:
        common.add_to_db(mysql_db, video_info, other_final, 'violate_result.report', '主司机手比', video_obj)

    return store_flag


# if __name__ == '__main__':

#     # initialize
#     cfg, openpose_logger, openpose_logger, mysql_logger, oracle_logger, json_path, box_info = init('wrongHead')
#     openpose_logger.info('function main: execute begin')
#     video_pth = cfg.get('path', 'video_path')
#     common.path_check(video_pth, openpose_logger, 'Video path NOT set!', 8)
#     openpose_logger.info('function main: video_path {0} get successfully'.format(video_pth))

#     # Connect to DB
#     openpose_logger.info('function main: connecting to Mysql database')
#     mysql_db = common.connect_db(cfg, mysql_logger, 'mysql')

#     if mysql_db == False:
#         openpose_logger.error('function main: mysql database connect failed')
#     else:
#         openpose_logger.info('function main: Mysql database conneting successfully')

#         openpose_logger.info('function main: conneting to Oracle database')
#         oracle_db = common.connect_db(cfg, oracle_logger, 'oracle')
#         if oracle_db == False:
#             openpose_logger.error('function main: Oracle database connect failed')
#         else:
#             openpose_logger.info('function main: Oracle database connect successfully')
#             openpose_logger.info('function main: prepare to execute model')

#             save_tmp=open('tmp/pict.sav', 'a+')
#             openpose_logger.info('function main: temp file {0} generate successfully'.format(save_tmp))

#             # trace json folder
#             openpose_logger.info('function main: walk through dirs under json path {0}'.format(json_path))
#             for root,dirs,files in os.walk(json_path):
#                 #wrong_head_result = []
#                 #leave_result = []
#                 #num_people_result = []
#                 model_result = []
#                 root_arr = root.split(os_sep)

#                 if len(root_arr) == 3: # used for updating lkj table
#                     dir_tot_ct = len(dirs)
#                     dir_ct = 0
#                 if len(root_arr) == 4: # if a folder contains json files
#                     openpose_logger.info('function main: searching video infomation under path {0}'.format(root))
#                     go_flg, qry_result = common.get_video_info(root_arr, mysql_db, openpose_logger, mysql_logger)
#                     if go_flg == False:
#                         openpose_logger.error('function main: video info get failed under path {0}'.format(root))
#                     else:
#                         openpose_logger.info('function main: video info get successfully under path {0}'.format(root))
#                         #st_time = common.date_time_reformat(dirname[-4], dirname[-3])
#                         #lkj_file = qry_result[0][1]
#                         st_time = qry_result[0][1]
#                         video_name = qry_result[0][3]
#                         # execute model
#                         openpose_logger.info('function main: custom model execute begin under path {0}'.format(root))
#                         #mdl_exe_rt = exe_model(root_arr, box_info, leave_result, num_people_result, wrong_head_result, st_time)
#                         mdl_exe_rt = exe_model(root_arr, box_info, model_result, st_time)
#                         #print(mdl_exe_rt)
#                         openpose_logger.info('function main: checking custom model result under path {0}'.format(root))
#                         if mdl_exe_rt == 2:
#                             openpose_logger.error('function main: custom model execute failed under path {0}'.format(root))
#                         elif mdl_exe_rt == 1:
#                             openpose_logger.warning('function main: custom model was not be executed under path {0}'.format(root))
#                         elif mdl_exe_rt < 0 or mdl_exe_rt > 2:
#                             openpose_logger.error('function main: custom model program error: return out of range under path {0}'.format(root))
#                         else:
#                             openpose_logger.info('function main: custom model execute successfully under path {0}'.format(root))

#                             # execute judge rules
#                             openpose_logger.info('function main: matching lkj data and custom model result under path {0}'.format(root))
#                             #match_rt, leave_final, wrong_head_final, single_person_final, channel_shift_final = match_lkj(qry_result,leave_result,wrong_head_result, num_people_result)
#                             match_rt, model_final, model_include_final = match_lkj(qry_result, model_result, root_arr)
#                             store_flg = model_rt_check(match_rt, root)
#                             if not store_flg:
#                                 openpose_logger.error('function main: model return code check failed under path {0}'.format(root))
#                             else:
#                                 store_result(model_final, qry_result[0], mysql_db, save_tmp, root, model_include_final)

#                         openpose_logger.info('function main: updating video table {0}'.format(video_name))
#                         if update_video_table(video_name, oracle_db) == False:
#                             openpose_logger.error('function main: video table {0} update failed under path {1}'.format(video_name, root))
#                         else:
#                             openpose_logger.info('function main: video table {0} update successfully under path {1}'.format(video_name, root))

#                     # video num + 1
#                     dir_ct += 1

#                     # if all videos corresponding to a lkj file have been analyzed,
#                     # then update the lkj table
#                     if dir_ct == dir_tot_ct:
#                         lkj_id = qry_result[0][-2]
#                         openpose_logger.info('function main: updating lkj table {0} under path {1}'.format(lkj_id,root))
#                         if update_lkj_table(oracle_db, mysql_db, lkj_id) == False:
#                             openpose_logger.error('function main: lkj table {0} update failed under path {1}'.format(lkj_id,root))
#                         else:
#                             openpose_logger.info('function main: lkj table {0} update successfully under path {1}'.format(lkj_id,root))

#             openpose_logger.info('function main: closing temp file {0}'.format(save_tmp))
#             save_tmp.close()
#     # close db
#     mysql_logger.info('function main: closing database')
#     try:
#         mysql_db.__del__()
#         mysql_logger.info('function main: database close successfully')
#     except Exception as e:
#         mysql_logger.error('function main: database close failed {0}'.format(traceback.format_exc()))

#     oracle_logger.info('function main: closing database')
#     try:
#         oracle_db.__del__()
#         oracle_logger.info('function main: database close successfully')
#     except Exception as e:
#         oracle_logger.error('function main: database close failed {0}'.format(traceback.format_exc()))




