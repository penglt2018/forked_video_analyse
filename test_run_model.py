import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
import src.common as common
import src.json_reader as json_reader
import numpy as np
import pandas as pd
from model.right.pos_recog_model import wrong_head as wrong_head_right
from model.back.pos_recog_model import wrong_head as wrong_head_back
from model.right_back.pos_recog_model import wrong_head as wrong_head_right_back
import time
import src.time_check as time_check
import sys
#sys.path.append('src/')
#import src.pyMysql as pyMysql

os_sep = os.path.sep
from tensorflow.python.framework import dtypes
#from stand1_test import Stand1
#from shoushi_test import Shoushi
import tensorflow as tf


def init(log_name):
    ''' initialization process including config parameters and logger fetch
        input: model log name
        return: config and loggers objects, json path and box info
    '''
    cfg = common.get_config('config.ini')
    main_logger = common.get_logger('run_openpose', 'logconfig.ini', True)
    model_logger = common.get_logger(log_name, 'logconfig.ini', False)
    mysql_logger = common.get_logger('mysql', 'logconfig.ini', False)
    oracle_logger = common.get_logger('oracle', 'logconfig.ini', False)
    json_path = cfg.get('path', 'json_out_path')
    common.path_check(json_path, main_logger, 'Json path NOT set!', 40)
    common.file_check('config/reference_box.ini', main_logger, 'Reference_box NOT set!', 41)
    box_info = json_reader.get_reference_data('config/reference_box.ini')
    if box_info == None: common.raise_error('Error: box_info is None', 42)
    return cfg, main_logger, model_logger, mysql_logger, oracle_logger, json_path, box_info


def add_to_db(db, qry_result, result_list, table_name, violate):
    ''' for each result from result_list, insert it to database
        input:
                db: database
                root_arr: path list split by '/'
                result_list: the result list returned by model
                driver: driver info
                violate: violate tag
        return:
                a boolean flag to determine the success of db insertion
    '''
    global mysql_logger, main_logger
    main_logger.info('starting add_to_db')

    # dirname = root_arr[-1].split('_')
    # train_type, train_num, duan = dirname[0], dirname[1], dirname[2]
    lkj_fname, video_st_tm, video_ed_tm, video_name, traintype, trainum, port, shift_num, driver, _,video_path = qry_result
    print(video_path)
    for result in result_list:
        #ptc_fname = result[2]
        violate_st_tm = result[0]
        #violate_ed_tm = result[4]
        #frame_st = result[1]
        #frame_ed = result[5]
        #violate = result[3]
        #violate = '未手比'
        
        sql = "insert into {0} ({1}) values (\'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', \'{7}\', {8}, \'{9}\', \'{10}\', \'{11}\', \'{12}\', now(), \'{13}\')".\
            format(table_name, 'LKJ_FILENAME,VIDEO_FILENAME,VIDEO_STARTTIME,VIDEO_ENDTIME,TRAIN_TYPE,TRAIN_NUM,PORT,SHIFT_NUM,DRIVER,VIOLATE,START_TIME,INSERT_TIME,VIDEO_PATH',\
                lkj_fname, video_name, video_st_tm, video_ed_tm, traintype, trainum, port, shift_num, driver, violate, violate_st_tm, video_path)
        mysql_logger.info('executing insert sql: {0}'.format(sql))
        try:
            db.Insert(sql)
            mysql_logger.info('insertion sql executing successfully')
        except Exception as e:
            mysql_logger.error('Insertion sql executing failed: {0}'.format(e))
            return False
    return True
    
# def fun_json_file_read(jsonfilename):
#     with open(jsonfilename) as fid:
#         js = json.load(fid)
#     if js['people'] != []:
#         if len(js['people']) > 1:
#             min_dist = 9
#             plp_list = js['people']
#             min_index = 0
#             for i in range(len(plp_list)):
#                 non_zero_point = [[plp_list[i]['pose_keypoints'][3*j],plp_list[i]['pose_keypoints'][3*j+1]] for j in range(len(plp_list[i]['pose_keypoints'])//3) if (plp_list[i]['pose_keypoints'][3*j] != 0) & (plp_list[i]['pose_keypoints'][3*j+1] != 0)]
#                 df_res = pd.DataFrame(non_zero_point,columns=['X','Y'])
#                 my_median = df_res.median()
#                 dist = my_median[1]
#                 if dist < min_dist:
#                     min_dist = dist
#                     min_index = i
#             pos = js['people'][min_index]['pose_keypoints']
#             x = [ random.random() if pos[x]==0 else pos[x] for x in range(len(pos)) if x%3 == 0 ]
#             y = [ random.random() if pos[y]==0 else pos[y] for y in range(len(pos)) if y%3 == 1 ]
#             data_list = [[[x[0],x[1],x[8],x[9],x[10]],[x[0],x[1],x[2],x[3],x[4]],[x[0],x[14],x[15],x[16],x[17]],[x[0],x[1],x[5],x[6],x[7]],[x[0],x[1],x[11],x[12],x[13]]],[[y[0],y[1],y[8],y[9],y[10]],[y[0],y[1],y[2],y[3],y[4]],[y[0],y[14],y[15],y[16],y[17]],[y[0],y[1],y[5],y[6],y[7]],[y[0],y[1],y[11],y[12],y[13]]]]
#         else:
#             pos = js['people'][0]['pose_keypoints']
#             x = [ random.random() if pos[x]==0 else pos[x] for x in range(len(pos)) if x%3 == 0 ]
#             y = [ random.random() if pos[y]==0 else pos[y] for y in range(len(pos)) if y%3 == 1 ]
#             data_list = [[[x[0],x[1],x[8],x[9],x[10]],[x[0],x[1],x[2],x[3],x[4]],[x[0],x[14],x[15],x[16],x[17]],[x[0],x[1],x[5],x[6],x[7]],[x[0],x[1],x[11],x[12],x[13]]],[[y[0],y[1],y[8],y[9],y[10]],[y[0],y[1],y[2],y[3],y[4]],[y[0],y[14],y[15],y[16],y[17]],[y[0],y[1],y[5],y[6],y[7]],[y[0],y[1],y[11],y[12],y[13]]]]
#         #print(data_list)
#         return np.array([data_list]).astype('float32')
#     else:
#         return [[]]

def get_lkj_signal(lkj_data):
    lkj_data_not_nan = lkj_data[pd.notnull(lkj_data['信号'])][['时间', '信号','事件']].reset_index(drop=True)
    #lkj_data_not_nan['时间'] = [date_str_fmt+' '+ x for x in lkj_data_not_nan['时间']]
    return lkj_data_not_nan


def exe_model(y, x, keep_prob, root_arr, box_info, leave_result, victory_result, st_time, fps):
    global model_logger
    model_logger.info('openpose model execution begin')
    # read json and get posture list
    #print(os_sep.join(root_arr), box_info)
    #print(root_arr)
    rt_list = json_reader.read_json_cus(os_sep.join(root_arr),box_info)
    #print(rt_list)
    if rt_list != []:
        file_list = np.array([i[0] for i in rt_list])    # first column is filename
        pos_list = [j[1] for j in rt_list]#, dtype=np.float32)
        dirname = root_arr[-1].split('_')    # dirname include video info
        #fps = dirname[-1]
        # format time to 'yyyy-mm-dd hh:mm:ss'
        #st_time = dirname[-3][:4] + '-' + dirname[-3][4:6] + '-' + dirname[-3][6:] + " " + dirname[-2][:2] + ":" + dirname[-2][2:4] +":"+dirname[-2][4:]
        #st_time = common.date_time_reformat(dirname[-4], dirname[-3])
        exe_flg = True
        # for each pos coordinate
        for i in range(len(pos_list)):
            # leave check
            #print(np.array([pos_list[i]]).shape)
            if pos_list[i] == [[]] or pos_list[i] == []:
                common.add_result(leave_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, 'leave_1')
            else: # execute wrong head model
                result = sess.run(y, feed_dict={x: np.array([pos_list[i]],dtype=np.float32), keep_prob:1.0}).tolist()[0]
                prob = max(result)
                demo_out = result.index(prob)
                        #print('filename is %s,the percent %s'%(item,data_percet))
                #demo_out = False
                #print(ct, demo_out, prob)
                if demo_out == 0 and prob > 0.5:
                    common.add_result(victory_result, file_list[i].replace('_keypoints.json', ''), fps, st_time, 'victory_1')
                
    return exe_flg


if __name__ == '__main__':

    # initialize
    cfg, main_logger, model_logger, mysql_logger, oracle_logger, json_path, box_info = init('victory')
    video_pth = cfg.get('path', 'video_path') 
    # Connect to DB
    main_logger.info('connecting to Mysql database')
    mysql_db = common.connect_db(cfg, mysql_logger, 'mysql')

    if mysql_db == False:
        main_logger.error('Mysql database connect failed')
    else:
        main_logger.info('Mysql database conneting successfully')
        main_logger.info('conneting to Oracle database')
        oracle_db = common.connect_db(cfg, oracle_logger, 'oracle')
        if oracle_db == False:
            main_logger.error('Oracle database connect failed')
        else:
            main_logger.info('Oracle database connect successfully')
            
            main_logger.info('wrong head model execution begin')
            
            save_tmp=open('tmp/pict.sav', 'a+')

            with tf.Session() as sess:
                new_saver = tf.train.import_meta_graph('./modelsave/model.ckpt-15801.meta')
                model_file=tf.train.latest_checkpoint('./modelsave/')
                #print(model_file)
                new_saver.restore(sess, model_file)
                graph = tf.get_default_graph()
                x = graph.get_operation_by_name('x').outputs[0]
                keep_prob = graph.get_operation_by_name('keep_prob').outputs[0]
                #y = graph.get_operation_by_name("y").outputs[0]#[0]
                y = tf.get_collection('pred_network')[0]

                ct = 0
                for root,dirs,files in os.walk(json_path):
                    victory_result = []
                    leave_result = []
                    root_arr = root.split(os_sep)
                    if len(root_arr) == 3:
                        dir_tot_ct = len(dirs)
                        dir_ct = 0
                    if len(root_arr) == 4: # if a folder contains json files
                        dirname = root_arr[-1].split('_')   # dirname include video info
                        video_name = '_'.join(dirname[:-2])
                        fps = dirname[-1]
                        # format time to 'yyyy-mm-dd hh:mm:ss'
                        #st_time = dirname[-3][:4] + '-' + dirname[-3][4:6] + '-' + dirname[-3][6:] + " " + dirname[-2][:2] + ":" + dirname[-2][2:4] +":"+dirname[-2][4:]
                        
                        # get video_start time via mysql
                        main_logger.info('searching video infomation ')
                        sql = "select lkj_data, date_format(video_st_tm, '%Y-%m-%d %H:%i:%s'), date_format(video_ed_tm, '%Y-%m-%d %H:%i:%s'), video_name, train_type, train_num, port, shift_num, driver, lkjid, video_path from violate_result.video_info where video_name = \'{0}\'".format(video_name)
                        mysql_logger.info('executing query sql: {0}'.format(sql))
                        qry_result = False
                        try:
                            qry_result = mysql_db.Query(sql)
                            mysql_logger.info('query sql excuting successfully')
                        except Exception as e:
                            mysql_logger.error('query sql executing failed: {0}'.format(e))
                            qry_result = False

                        if qry_result == False:
                            main_logger.error('some errors occur during searching video information via mysql')
                        elif len(qry_result) > 1:
                            main_logger.error('the video {0} is related to more than one record {1}'.format(video_name, qry_result))
                        elif len(qry_result) <= 0:
                            main_logger.error('the video {0} can not be found in database'.format(video_name))
                        else:
                            #st_time = common.date_time_reformat(dirname[-4], dirname[-3])
                            #lkj_file = qry_result[0][1]
                            st_time = qry_result[0][1]
                            main_logger.info('video information searching successfully')
                            if exe_model(y, x, keep_prob, root_arr, box_info, leave_result, victory_result, st_time, fps) == False:
                                main_logger.warning('Model execution contains some errors')
                            else:
                                main_logger.info('All wrong head model execute successfully')

                            #print(victory_result)
                            main_logger.info('get lkj data')
                            lkj_fname = qry_result[0][0]
                            lkj_result = common.get_lkj(video_pth+os_sep+root_arr[1]+os_sep+root_arr[2], lkj_fname)
                            if lkj_result[0] == False:
                                main_logger.error(lkj_result[1])
                            else:
                                main_logger.info('lkj_data {0} read successfully'.format(lkj_fname))
                                ed_time = qry_result[0][2]
                                #print(st_time, ed_time)
                                
                                lkj_signal = get_lkj_signal(lkj_result[1])
                                yolo_result_signal = time_check.yolo_signal_filter(victory_result,lkj_signal,[st_time, ed_time],20,['victory_1', 'leave_1', 'leave_2'],['出站'],['绿灯', '绿黄','双黄'])
                                if yolo_result_signal != []:
                                    #print(yolo_result_signal)
                                    if add_to_db(mysql_db, qry_result[0], yolo_result_signal, 'violate_result.report', '未手比') == False:
                                        main_logger.error('yolo result insert to db contains some errors')
                                    else:
                                        main_logger.info('yolo result insert to db successfully')
                                else:
                                    main_logger.info('no violation detected')

                                # match result
                                #print(len(yolo_result),lkj_signal.shape)
                                yolo_result_include = time_check.yolo_signal_include_filter(victory_result,lkj_signal,[st_time, ed_time],20,['victory_1'],['出站'],['绿灯', '绿黄','双黄'])
                                if yolo_result_include != []:
                                    add_to_db(mysql_db, qry_result[0], yolo_result_include, 'violate_result.yolo_test', '手比正确')
                            
                            # # execute judge rules
                            # if leave_result != []:
                            #     main_logger.info('joining lkj data and leave result')
                            #     # execute leave check
                            #     leave_final = time_check.lkj_time_filter(leave_result, lkj_result[1])
                            #     main_logger.info('join lkj data and leave result successfully')
                            #     #print(leave_final)
                            #     if leave_final != []:
                            #         #print(leave_final)
                            #         leave_final = leave_filt(leave_final, lkj_result[1], qry_result[0][3])
                            #         if add_to_db(mysql_db, qry_result[0], leave_final, '离岗') == False:
                            #             main_logger.error('leave result insert to db contains some errors')
                            #         else:
                            #             main_logger.info('leave result insert to db successfully')
                            #             #continue
                            #             # leave_final = time_check.leave_check(leave_result, speed_list)
                            #             # add_to_db(db, dirname, leave_final, '主司机', '离岗')
                            # if victory_result != []:
                            #     main_logger.info('joining lkj data and wrongHead result')
                            #     #lkj_data = get_lkj(root_arr[1], root_arr[2])
                            #     #print(wrong_head_result)
                            #     # execute time check for wrong head
                            #     victory_final = time_check.lkj_time_filter(victory_result, lkj_result[1])
                            #     if wrong_head_final != []:
                            #         #print(wrong_head_final)
                            #         victory_final = leave_filt(victory_final, lkj_result[1], qry_result[0][3])
                            #         if add_to_db(mysql_db, qry_result[0], victory_final, '手比') == False:
                            #             main_logger.error('wrongHead result insert to db contains some errors')
                            #         else:
                            #             main_logger.info('wrongHead result insert to db successfully')


