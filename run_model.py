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
import lib.common as common
import numpy as np
import pandas as pd
from model.right.pos_recog_model import wrong_head as wrong_head_right
from model.back.pos_recog_model import wrong_head as wrong_head_back
from model.right_back.pos_recog_model import wrong_head as wrong_head_right_back
from model.right_back.pos_recog_model import arm_detect as arm_detect_right_back
from model.right_back.pos_recog_model import get_angle
import time
import lib.lkj_lib as LKJLIB
import lib.json_reader as json_reader
import sys

os_sep = os.path.sep
openpose_logger = common.get_logger('openpose')


def init():
    ''' initialization process including config parameters and logger fetch
        input: model log name
        return: config and loggers objects, json path and box info
    '''
    print('run_model initializing')

    common.file_check('config/reference_box.ini', openpose_logger, 'Reference_box NOT set!', 41)
    try:
        box_info = json_reader.get_reference_data('config/reference_box.ini')
        openpose_logger.info('function init: box config data read successfully')
    except Exception:
        openpose_logger.error('function init: box config data read failed {0}'.format(traceback.format_exc()))
    
    model_logger.info('function init: checking box config data')
    if box_info == None: common.raise_error('Error: box_info is None', 42)
    return cfg, main_logger, model_logger, mysql_logger, oracle_logger, json_path, box_info

#def exe_model(root_arr, box_info, leave_result, num_people_result, wrong_head_result, st_time):
def exe_model(root_arr, box_info, model_result, st_time):
    ''' execute model and return results
        input:
                root_arr: path list split by '/'
                box_info: used to constrain the scope of position of drivers in a frame picture
                leave_result: the result of leave model
                wrong_head_result: the result of wrong head model
        return:
                a boolean flag used to judge the success of executing model 
    '''
    global model_logger
    exe_path = os_sep.join(root_arr)
    model_logger.info('function exe_model: custom model execute begin under path {0}'.format(exe_path))
    # read json and get posture list
    #print(os_sep.join(root_arr), box_info)
    #print(root_arr)
    model_logger.info('function exe_model: reading json files')
    rt_list = []
    #print(pd.DataFrame(json_reader.read_json(exe_path,box_info)).shape)
    try:
        rt_list = np.array(json_reader.read_json(exe_path,box_info))
    except Exception as e:
        model_logger.error('function exe_model: json file read failed {0}'.format(traceback.format_exc()))
    #print(type(rt_list))
    #print(rt_list.shape)
    #print(rt_list == np.array([]))
    if rt_list == [] or rt_list.shape[0] == 0:
        model_logger.error('function exe_model: no json file under path {0}'.format(exe_path))
        exe_flg = 0
        return exe_flg
    else:
        model_logger.info('function exe_model: json files read successfully')
        #print(rt_list)
        file_list = rt_list[:,0]    # first column is filename
        model_logger.info('function exe_model: file name list generate successfully')
        pos_list = rt_list[:,1:-1].astype('float32')
        num_plp_list = rt_list[:,-1].astype('float32')
        #print(num_plp_list)	
        model_logger.info('function exe_model: posture list generate successfully')
        fps = root_arr[-1].split('_')[-1]    # dirname include video info
        #print(fps)
	#fps = dirname[-1]
        # format time to 'yyyy-mm-dd hh:mm:ss'
        #st_time = dirname[-3][:4] + '-' + dirname[-3][4:6] + '-' + dirname[-3][6:] + " " + dirname[-2][:2] + ":" + dirname[-2][2:4] +":"+dirname[-2][4:]
        #st_time = common.date_time_reformat(dirname[-4], dirname[-3])
        exe_flg = 0
        # for each pos coordinate
        model_logger.info('function exe_model: executing custom model')
        for i in range(len(pos_list)):
            # number of people check
            if num_plp_list[i] == 1:
                #common.add_result(num_people_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, '单人值乘')
                common.add_result(model_result, file_list[i].replace('_keypoints.json' ,''), fps, st_time, '单人值乘')
            # leave check
            if pos_list[i][4] == -1:
                #common.add_result(leave_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, '离岗')
                common.add_result(model_result, file_list[i].replace('_keypoints.json',''), fps, st_time,'离岗')
            else:
                coord = [list(pos_list[i])]
                # execute wrong head model
                wrong_head_rt = 0    
                wrong_head_model = 'wrong_head_' + root_arr[1]
                try:
                    wrong_head_rt = eval(wrong_head_model)(coord)
                except Exception as e:
                    model_logger.error('function exe_model: wrong head model {0} execute failed with {1}: {2}'.format(eval(wrong_head_model).__module__, coord, traceback.format_exc()))
                    exe_flg = 2

                if wrong_head_rt != 0: # model output wrong head
                    #common.add_result(wrong_head_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, '偏头')
                    common.add_result(model_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, '偏头')

                # execute arm check model
                arm_detect_rt = 0
                arm_detect_model = 'arm_detect_' + root_arr[1]
                try:
                    arm_detect_rt = eval(arm_detect_model)(coord)
                    #if 'HXD1C0827_株洲所_10_二端司机室_20181001_110001_03980' in file_list[i]:
                    #     print(arm_detect_rt)
                except Exception as e:
                    model_logger.error('function exe_model: arm detect model {0} execute failed with {1}: {2}'.format(eval(arm_detect_model).__name__, coord, traceback.format_exc()))
                    exe_flg = 2

                if arm_detect_rt != 1 : # no person and normal case
                    if arm_detect_rt == 2 or arm_detect_rt == 0:
                        common.add_result(model_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, '手比')
                    elif arm_detect_rt == 3 or arm_detect_rt == 0:
                        common.add_result(model_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, '握拳')
                    elif arm_detect_rt == 4:
                        common.add_result(model_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, '非标准手比')
                    else:
                        model_logger.error('function exe_model: arm check model return code out of range: {0}'.format(coord))
                        exe_flg = 2
                    #print([list(pos_list[i])],wrong_head_rt,file_list[i],fps, st_time)
                    #print(wrong_head_rt,file_list[i],fps, st_time)
        if not 'wrong_head_rt' in locals().keys():
            model_logger.warning('function exe_model: wrong head model does not execute: {0}'.format(pos_list))
            exe_flg = 1
        if not 'arm_detect_rt' in locals().keys():
            model_logger.warning('function exe_model: arm detect model does not execute: {0}'.format(pos_list))
        model_logger.info('function exe_model: custom model execute finish under path {0}'.format(exe_path))
        return exe_flg


def update_video_table(video_name, oracle_db):
    global oracle_logger
    oracle_logger.info('function update_video_table: execute begin')

    sql = "update lkjvideoadmin.LAVDR set ISANALYZED = 1 where filepath like \'%{0}%\'".format(video_name)
    #sql = "update lkjvideoadmin.LAVDR set ISANALYZED = 1 where filename = \'http://10.196.205.47/{0}.mp4\'".format(video_name)
    oracle_logger.info('function update_video_table: executing update sql: {0}'.format(sql))
    try:
        oracle_db.Exec(sql)
        oracle_logger.info('function update_video_table: update sql execute successfully')
    except Exception as e:
        oracle_logger.error('function update_video_table: update sql execute failed: {0}'.format(traceback.format_exc()))
        return False
    return True

def update_lkj_table(oracle_db, mysql_db, lkj_id):
    global oracle_logger, mysql_logger
    #lkj_id = qry_result[-2]
    mysql_logger.info('function update_lkj_table: execute begin')
    count_sql = "select count(1) from violate_result.video_info where lkjid = {0} group by lkjid".format(lkj_id)
    mysql_logger.info('function update_lkj_table: executing counting sql : {0}'.format(count_sql))
    try:
        cnt_result = mysql_db.Query(count_sql)
        mysql_logger.info('function update_lkj_table: counting sql executing successfully')
    except Exception as e:
        mysql_logger.error('function update_lkj_table: counting sql execute failed: {0}'.format(traceback.format_exc()))
        return False
    #print(cnt_result)
    cnt = cnt_result[0][0]

    oracle_logger.info('function update_lkj_table: execute begin')
    update_sql = 'update lkjvideoadmin.lkjvideoproblem set videoanalyzed = videoanalyzed + {0}, ISANALYZED = 1 where lkjid = {1}'.format(cnt, lkj_id)
    oracle_logger.info('function update_lkj_table: executing update sql {0}'.format(update_sql))
    try:
        oracle_db.Exec(update_sql)
        oracle_logger.info('function update_lkj_table: update sql execute successfully')
    except Exception as e:
        oracle_logger.error('function update_lkj_table: update sql execute failed: {0}'.format(traceback.format_exc()))
        return False

    # update_sql = 'update lkjvideoadmin.lkjvideoproblem set ISANALYZED = 1 where lkjid = {0}'.format(lkj_id)
    # oracle_logger.info('function update_lkj_table: executing update sql {0}'.format(update_sql))
    # try:
    #     oracle_db.Exec(update_sql)
    #     oracle_logger.info('update sql execute successfully')
    # except Exception as e:
    #     oracle_logger.error('update sql execute failed: {0}'.format(traceback.format_exc()))
    #     return False

    return True


#def match_lkj(qry_result,leave_result,wrong_head_result, num_people_result):
def match_lkj(qry_result, model_result, root_arr):
    global model_logger, video_pth
    model_logger.info('function match_lkj: execute begin')

    lkj_fname = qry_result[0][0]
    dirname = video_pth+os_sep+root_arr[1]+os_sep+root_arr[2]
    model_logger.info('function match_lkj: reading lkj data {0}/{1}'.format(dirname, lkj_fname))
    lkj_result = common.get_lkj(dirname, lkj_fname)

    match_flg = 0

    leave_result = [ i for i in model_result if i[-1] == '离岗' ]
    wrong_head_result = [ i for i in model_result if i[-1] == '偏头' ]
    num_people_result = [ i for i in model_result if i[-1] == '单人值乘' ]
    point_forward_result = [ i for i in model_result if i[-1] == '手比' ]
    fist_result = [ i for i in model_result if i[-1] == '握拳' ]
    other_gesture_result = [ i for i in model_result if i[-1] == '非标准手比' ]

    leave_final = []
    wrong_head_final = []
    double_person_final = []
    port_shift_final = []
    point_forward_final = []
    point_forward_include_final = []
    fist_final = []
    fist_include_final = []
    point_forward_other_final = []
    fist_other_final = []
    #print(num_people_result)

    if lkj_result[0] == False:
        model_logger.error('function match_lkj: {0}'.format(lkj_result[1]))
        match_flg = 1
    else:
        model_logger.info('function match_lkj: lkj data read successfully')
        st_time = qry_result[0][1]
        ed_time = qry_result[0][2]
        #print(st_time, ed_time)
        #\print(num_people_result)
        # execute leave judge rules
        if leave_result != []:
            model_logger.info('function match_lkj: joining lkj data and leave result')
            try:
                leave_final = time_check.lkj_time_filter(leave_result, lkj_result[1])
                model_logger.info('function match_lkj: lkj data and leave result join successfully')
            except Exception as e:
                model_logger.error('function match_lkj: lkj data and leave result join failed {0}'.format(traceback.format_exc()))
                match_flg = 2
            if leave_final != []:
                #print(leave_final)
                leave_final = common.leave_filt(leave_final, lkj_result[1], qry_result[0][3])

        # execute wrong head judge ruls
        if wrong_head_result != []:
            model_logger.info('function match_lkj: joining lkj data and wrong head result')
            #lkj_data = get_lkj(root_arr[1], root_arr[2])
            #print(wrong_head_result)
            try:
                wrong_head_final = time_check.lkj_time_filter(wrong_head_result, lkj_result[1])
                model_logger.info('function match_lkj: lkj data and wrong head result join successfully')
            except Exception as e:
                model_logger.error('function match_lkj: lkj data and wrong head result join failed {0}'.format(traceback.format_exc()))
                match_flg = 3
            if wrong_head_final != []:
                #print(wrong_head_final)
                wrong_head_final = common.leave_filt(wrong_head_final, lkj_result[1], qry_result[0][3])

        # execute double person rules
        if num_people_result != []:
            model_logger.info('function match_lkj: joining lkj data and double person result')
            try:
                double_person_final = time_check.lkj_double_person(num_people_result, lkj_result[1])
                model_logger.info('function match_lkj: lkj data and double person result join successfully')
            except Exception as e:
                model_logger.error('function match_lkj: lkj data and double person result join failed {0}'.format(traceback.format_exc()))
                match_flg = 4

            model_logger.info('function match_lkj: joining lkj data and port shift result')
            try:
                #print(num_people_result)
                port_shift_final = time_check.lkj_port_shift(num_people_result, lkj_result[1], st_time, ed_time)
                model_logger.info('function match_lkj: lkj data and port shift result join successfully')
            except Exception as e:
                model_logger.error('function match_lkj: lkj data and port shift result join failed {0}'.format(traceback.format_exc()))
                match_flg = 5

        
        model_logger.info('function match_lkj: getting lkj signal info')
        try:
            lkj_signal = get_lkj_signal(lkj_result[1])
            model_logger.info('function match_lkj: lkj signal info get successfully')
        except Exception as e:
            model_logger.error('function match_lkj: lkj signal info get failed {0}'.format(traceback.format_exc()))
            match_flg = 6

        if match_flg != 6:
            # execute point forward rules
            point_forward_comb = point_forward_result + other_gesture_result
            if point_forward_comb != []:
                model_logger.info('function match_lkj: joining lkj data and point_forward_comb')
                try:
                    point_forward_final = time_check.arm_detect_filter(point_forward_comb,lkj_signal,[st_time, ed_time],30,10,[],['出站', '进站'],['绿灯', '绿黄灯','双黄灯','黄闪黄','黄灯'],1)
                    if point_forward_result != []:
                        point_forward_include_final = time_check.arm_detect_include_filter(point_forward_result,lkj_signal,[st_time, ed_time],30,10,[],['出站', '进站'],['绿灯', '绿黄灯','双黄灯','黄闪黄','黄灯'],1)

                        point_forward_include_final = common.leave_filt(point_forward_include_final, lkj_result[1], qry_result[0][3])
                        #print(point_forward_include_final)
                        #print(lkj_signal.values.tolist())
                    if other_gesture_result != []:
                        #other_gesture_result = time_check.model_time_exclude(other_gesture_result,point_forward_result,2)
                        #print(lkj_signal)
                        if point_forward_include_final != [] and point_forward_include_final != [[]]:
                            lkj_signal_filt = time_check.model_time_exclude(lkj_signal, pd.DataFrame(point_forward_include_final,columns=lkj_signal.columns.values.tolist()),0)
                        else:
                            lkj_signal_filt = lkj_signal
                        #print(lkj_signal_filt)
                       	#print(time_check.model_time_exclude(lkj_signal.values.tolist(), point_forward_include_final,1))
                        #print(other_gesture_result)
                        point_forward_other_final = time_check.arm_detect_include_filter(other_gesture_result, lkj_signal_filt, [st_time, ed_time], 30,10,[],['出站', '进站'],['绿灯', '绿黄灯','双黄灯','黄闪黄','黄灯'],1)
                    model_logger.info('function match_lkj: lkj data and point_forward_comb join successfully')
                except Exception as e:
                    model_logger.error('function match_lkj: lkj data and point_forward_comb join failed {0}'.format(traceback.format_exc()))
                    match_flg = 7

            # execute fist rules
            fist_comb = fist_result + other_gesture_result
            #print(fist_result)
            if fist_comb != []:
                model_logger.info('function match_lkj: joining lkj data and fist result')
                try:
                    fist_final = time_check.arm_detect_filter(fist_comb, lkj_signal, [st_time, ed_time], 30, 10, [], ['机车信号变化'], ['红灯'],1)
                    #print(fist_final)
                    if fist_result != []:
                        fist_include_final = time_check.arm_detect_include_filter(fist_result, lkj_signal, [st_time, ed_time], 30, 10, [], ['机车信号变化'], ['红灯'],1)
                        
                        fist_include_final = common.leave_filt(fist_include_final, lkj_result[1], qry_result[0][3])
                        #print(fist_include_final)
                    if other_gesture_result != []:
                        #other_gesture_result = time_check.model_time_exclude(other_gesture_result,fist_result,2)
                        if fist_include_final != [] and fist_include_final != [[]]:
                            lkj_signal_filt = time_check.model_time_exclude(lkj_signal,pd.DataFrame(fist_include_final,columns=lkj_signal.columns.values.tolist()),0)
                        else:
                            lkj_signal_filt = lkj_signal
                        fist_other_final = time_check.arm_detect_include_filter(other_gesture_result, lkj_signal_filt, [st_time, ed_time], 30, 10, [], ['机车信号变化'], ['红灯'],1)
                        #print(fist_other_final)
                    model_logger.info('function match_lkj: lkj data and fist result join successfully')
                except Exception as e:
                    model_logger.error('function match_lkj: lkj data and fist result join failed {0}'.format(traceback.format_exc()))
                    match_flg = 8

            # if double_person_final != []:
            #     #print(leave_final)
            #     double_person_final = leave_filt(double_person_final, lkj_result[1], qry_result[0][3])
    final_result = ([leave_final] + [wrong_head_final] + [double_person_final] + [port_shift_final] + [point_forward_final] + [fist_final])
    include_final_result = ([point_forward_include_final] + [fist_include_final] + [point_forward_other_final] + [fist_other_final])
    return match_flg, final_result, include_final_result

def model_rt_check(match_rt, path):
    global main_logger
    rt = True
    main_logger.info('function model_rt_check: checking lkj and custom model matching result')
    if match_rt == 1:
        main_logger.error('function model_rt_check: lkj data read error under path {0}'.format(path))
        rt = False
    elif match_rt == 2:
        main_logger.error('function model_rt_check: lkj data and leave result matching error under path {0}'.format(path))
        rt = False
    elif match_rt == 3:
        main_logger.error('function model_rt_check: lkj data and wrongHead result matching error under path {0}'.format(path))
        rt = False
    elif match_rt == 4:
        main_logger.error('function model_rt_check: lkj data and double person result matching error under path {0}'.format(path))
        rt = False
    elif match_rt == 5:
        main_logger.error('function model_rt_check: lkj data and port shift result matching error under path {0}'.format(path))
        rt = False
    elif match_rt == 6:
        main_logger.warning('function model_rt_check: lkj signal info get failed under path {0}'.format(path))
    elif match_rt == 7:
        main_logger.error('function model_rt_check: lkj data and point_forward_result matching error under path {0}'.format(path))
        rt = False
    elif match_rt == 8:
        main_logger.error('function model_rt_check: lkj data and fist_result matching error under path {0}'.format(path))
        rt = False
    elif match_rt < 0 or match_rt > 8:
        main_logger.error('function model_rt_check: lkj match program error: return out of range under path {0}'.format(path))
        rt = False
    return rt

def store_result(model_result, qry_result, mysql_db, save_tmp, path, model_include_result=None):
    global main_logger, mysql_logger
    leave_final, wrong_head_final, double_person_final, port_shift_final, point_forward_final, fist_final = model_result
    if model_include_result:
        point_forward_include_final, fist_include_final, point_forward_other_final, fist_other_final = model_include_result
    # add leave result to db
    if leave_final == []:
        main_logger.info('function store_result: no leave detected under path {0}'.format(path))
    else:
        if common.add_to_db(mysql_db, qry_result, leave_final, 'violate_result.report', '离岗', mysql_logger, save_tmp) == False:
            main_logger.error('function store_result: leave result insert to db failed under path {0}'.format(path))
        else:
            main_logger.info('function store_result: leave result insert to db successfully under path {0}'.format(path))
    # add wrong head result to db
    if wrong_head_final == []:
        main_logger.info('function store_result: no wrongHead detected under path {0}'.format(path))
    else:
        if common.add_to_db(mysql_db, qry_result, wrong_head_final, 'violate_result.report', '偏头', mysql_logger, save_tmp) == False:
            main_logger.error('function store_result: wrongHead result insert to db failed under path {0}'.format(path))
        else:
            main_logger.info('function store_result: wrongHead result insert to db successfully under path {0}'.format(path))
    
    # add double person result to db
    if double_person_final == []:
        main_logger.info('function store_result: no double person detected under path {0}'.format(path))
    else:
        if common.add_to_db(mysql_db, qry_result, double_person_final, 'violate_result.report', '单人值乘', mysql_logger, save_tmp) == False:
            main_logger.error('function store_result: double person result insert to db failed under path {0}'.format(path))
        else:
            main_logger.info('function store_result: double person result insert to db successfully under path {0}'.format(path))
    # add port shift result to db
    if port_shift_final == []:
        main_logger.info('function store_result: no port shift violation detected under path {0}'.format(path))
    else:
        if common.add_to_db(mysql_db, qry_result, port_shift_final, 'violate_result.report', '同时换端', mysql_logger) == False:
            main_logger.error('function store_result: port shift result insert to db failed under path {0}'.format(path))
        else:
            main_logger.info('function store_result: port shift result insert to db successfully under path {0}'.format(path))
    # add point forward result to db
    if point_forward_final == []:
        main_logger.info('function store_result: no point_forward violate detected under path {0}'.format(path))
    else:
        if common.add_to_db(mysql_db, qry_result, point_forward_final, 'violate_result.report', '未手比', mysql_logger) == False:
            main_logger.error('function store_result: point_forward result insert to db failed under path {0}'.format(path))
        else:
            main_logger.info('function store_result: point forward result insert to db successfully under path {0}'.format(path))

    # add fist result to db
    if fist_final == []:
        main_logger.info('function store_result: no fist violate detected under path {0}'.format(path))
    else:
        if common.add_to_db(mysql_db, qry_result, fist_final, 'violate_result.report', '未摇臂', mysql_logger) == False:
            main_logger.error('function store_result: fist result insert to db failed under path {0}'.format(path))
        else:
            main_logger.info('function store_result: fist result insert to db successfully under path {0}'.format(path))

    # addtional arm detect check
    if point_forward_include_final != []:
        common.add_to_db(mysql_db, qry_result, point_forward_include_final, 'violate_result.report', '手比', mysql_logger)
    if fist_include_final != []:
        common.add_to_db(mysql_db, qry_result, fist_include_final, 'violate_result.report', '摇臂', mysql_logger)
    
    other_final = point_forward_other_final + fist_other_final
    if other_final != []:
        common.add_to_db(mysql_db, qry_result, other_final, 'violate_result.report', '不标准手比', mysql_logger)

if __name__ == '__main__':

    # initialize
    cfg, main_logger, model_logger, mysql_logger, oracle_logger, json_path, box_info = init('wrongHead')
    main_logger.info('function main: execute begin')
    video_pth = cfg.get('path', 'video_path')
    common.path_check(video_pth, main_logger, 'Video path NOT set!', 8)
    main_logger.info('function main: video_path {0} get successfully'.format(video_pth))
    
    # Connect to DB
    main_logger.info('function main: connecting to Mysql database')
    mysql_db = common.connect_db(cfg, mysql_logger, 'mysql')

    if mysql_db == False:
        main_logger.error('function main: mysql database connect failed')
    else:
        main_logger.info('function main: Mysql database conneting successfully')

        main_logger.info('function main: conneting to Oracle database')
        oracle_db = common.connect_db(cfg, oracle_logger, 'oracle')
        if oracle_db == False:
            main_logger.error('function main: Oracle database connect failed')
        else:
            main_logger.info('function main: Oracle database connect successfully')
            main_logger.info('function main: prepare to execute model')
            
            save_tmp=open('tmp/pict.sav', 'a+')
            main_logger.info('function main: temp file {0} generate successfully'.format(save_tmp))
            
            # trace json folder
            model_logger.info('function main: walk through dirs under json path {0}'.format(json_path))
            for root,dirs,files in os.walk(json_path):
                #wrong_head_result = []
                #leave_result = []
                #num_people_result = []
                model_result = []
                root_arr = root.split(os_sep)

                if len(root_arr) == 3: # used for updating lkj table
                    dir_tot_ct = len(dirs)
                    dir_ct = 0
                if len(root_arr) == 4: # if a folder contains json files
                    main_logger.info('function main: searching video infomation under path {0}'.format(root))
                    go_flg, qry_result = common.get_video_info(root_arr, mysql_db, model_logger, mysql_logger)
                    if go_flg == False:
                        main_logger.error('function main: video info get failed under path {0}'.format(root))
                    else:
                        main_logger.info('function main: video info get successfully under path {0}'.format(root))
                        #st_time = common.date_time_reformat(dirname[-4], dirname[-3])
                        #lkj_file = qry_result[0][1]
                        st_time = qry_result[0][1]
                        video_name = qry_result[0][3]
                        # execute model
                        main_logger.info('function main: custom model execute begin under path {0}'.format(root))
                        #mdl_exe_rt = exe_model(root_arr, box_info, leave_result, num_people_result, wrong_head_result, st_time)
                        mdl_exe_rt = exe_model(root_arr, box_info, model_result, st_time)
                        #print(mdl_exe_rt)
                        main_logger.info('function main: checking custom model result under path {0}'.format(root))
                        if mdl_exe_rt == 2:
                            main_logger.error('function main: custom model execute failed under path {0}'.format(root))
                        elif mdl_exe_rt == 1:
                            main_logger.warning('function main: custom model was not be executed under path {0}'.format(root))
                        elif mdl_exe_rt < 0 or mdl_exe_rt > 2:
                            main_logger.error('function main: custom model program error: return out of range under path {0}'.format(root))
                        else:
                            main_logger.info('function main: custom model execute successfully under path {0}'.format(root))
                            
                            # execute judge rules
                            main_logger.info('function main: matching lkj data and custom model result under path {0}'.format(root))
                            #match_rt, leave_final, wrong_head_final, double_person_final, port_shift_final = match_lkj(qry_result,leave_result,wrong_head_result, num_people_result)
                            match_rt, model_final, model_include_final = match_lkj(qry_result, model_result, root_arr)
                            store_flg = model_rt_check(match_rt, root)
                            if not store_flg:
                                main_logger.error('function main: model return code check failed under path {0}'.format(root))
                            else:
                                store_result(model_final, qry_result[0], mysql_db, save_tmp, root, model_include_final)

                        main_logger.info('function main: updating video table {0}'.format(video_name))
                        if update_video_table(video_name, oracle_db) == False:
                            main_logger.error('function main: video table {0} update failed under path {1}'.format(video_name, root))
                        else:
                            main_logger.info('function main: video table {0} update successfully under path {1}'.format(video_name, root))
                        
                    # video num + 1
                    dir_ct += 1

                    # if all videos corresponding to a lkj file have been analyzed,
                    # then update the lkj table
                    if dir_ct == dir_tot_ct:
                        lkj_id = qry_result[0][-2]
                        main_logger.info('function main: updating lkj table {0} under path {1}'.format(lkj_id,root))
                        if update_lkj_table(oracle_db, mysql_db, lkj_id) == False:
                            main_logger.error('function main: lkj table {0} update failed under path {1}'.format(lkj_id,root))
                        else:
                            main_logger.info('function main: lkj table {0} update successfully under path {1}'.format(lkj_id,root))

            main_logger.info('function main: closing temp file {0}'.format(save_tmp))
            save_tmp.close()
    # close db
    mysql_logger.info('function main: closing database')
    try:
        mysql_db.__del__()
        mysql_logger.info('function main: database close successfully')
    except Exception as e:
        mysql_logger.error('function main: database close failed {0}'.format(traceback.format_exc()))

    oracle_logger.info('function main: closing database')
    try:
        oracle_db.__del__()
        oracle_logger.info('function main: database close successfully')
    except Exception as e:
        oracle_logger.error('function main: database close failed {0}'.format(traceback.format_exc()))
        


                    
