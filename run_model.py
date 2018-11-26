#coding: utf-8
'''
Program Name: Video to Frame
File Name: video_to_frame
Creation Date: Apr 2018
Programmer: XINWU LIU, BANGFAN LIU
Abstract: This program is for convert videos to frames given a path
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
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.utf8'
import lib.common as common
import lib.video_handler as video_handler
import yolo_handler 
import openpose_handler 
import multiprocessing
os_sep = os.path.sep
video_path='./video'       # set download path

def init(log_name):
    ''' Function for initializing main logger,
        databse connector objects, darknet network, and temp file
        Input: 
                log name
        Return: 
                return True if all global variables are generated successfully,
                otherwise return False
    '''
    global main_logger, oracle_db, mysql_db
    main_logger = False
    oracle_db = False
    mysql_db = False
    main_logger = common.get_logger(log_name)
    
    # initialize darknet
    yolo_handler.init()
    # initialize openpose
    openpose_handler.init()

    # connect to Oracle database
    main_logger.info('Connecting to Oracle database')
    oracle_conn_rt = common.connect_db('oracle')    # conn_rt = [ True/False, log_info, database object ]
    if oracle_conn_rt[0] == False:
        main_logger.error(oracle_conn_rt[1])
    else:
        main_logger.info(oracle_conn_rt[1])
        oracle_db = oracle_conn_rt[2]

    # connect to Mysql database
    main_logger.info('Connecting to Mysql database')
    mysql_conn_rt = common.connect_db('mysql')
    if mysql_conn_rt[0] == False:
        main_logger.error(mysql_conn_rt[1])
    else:
        main_logger.info(mysql_conn_rt[1])
        mysql_db = mysql_conn_rt[2] 

    # create a temp file to record image filenames
    # which needs to be saved
    # save_tmp=open('tmp/pict.sav', 'a+')
    # common.file_check(save_tmp, main_logger, 'Temp file tmp/pict.sav create failed!', 10)
    # main_logger.info('temp file {0} generate successfully'.format(save_tmp))

    if main_logger != False and oracle_db != False and mysql_db != False:
        main_logger.info('Initializting process successfully')
        return True
    else:
        main_logger.error('Initializting process Failed!')
        if oracle_db != False:
            common.close_db(oracle_db, 'oracle')
        if mysql_db != False:
            common.close_db(mysql_db, 'mysql')
        return False
    
def run_yolo(video_obj, video_info, lkj_file):
    ''' Function for executing yolo
        Input:
                video_obj:  custom video object
                video_info: video related information
                lkj_file:   LKJ file with path
        return:
                None
    '''
    global main_logger, mysql_db
    yolo_result = []
    video_name = video_info[3]
    frame_mat = video_obj.get_video_frames()
    fps = video_obj.get_video_fps

    if frame_mat == [] or frame_mat == [[]]:
        main_logger.warning('Empty frame from video {0}'.format(video_name))
    else:
        # execute yolo to predict labels into yolo_result list
        yolo_rt_flag = yolo_handler.exe_yolo(frame_mat, yolo_result, video_info, fps)
        if yolo_rt_flag == False:
            main_logger.error('YOLO execute failed to video {0}'.format(video_name))
        else:
            main_logger.info('YOLO execute successfully to video {0}'.format(video_name))

            # correlate lkj data and yolo result for violate judgment
            main_logger.info('Executing LKJ and yolo result correlation')
            match_rt, final_result = yolo_handler.match_lkj(lkj_file, video_info, yolo_result)
            if match_rt != 0:
                main_logger.error('LKJ and yolo result correlation contains some errors, please check yolo.log')
            else:
                main_logger.info('LKJ and yolo result correlation successfully')
                store_rt_flag = yolo_handler.store_result(final_result, video_info, mysql_db, video_obj)
                if store_rt_flag == False:
                    main_logger.error('Violation result of video {0} stored contains some errors, please refer to yolo log for further details'.format(video_name))
                else:
                    main_logger.info('Violation result of video {0} stored successfully'.format(video_name))       

def run_openpose(video_obj, video_info, lkj_file):
    '''
    '''
    global main_logger, mysql_db
    openpose_result = []
    video_name = video_info[3]
    frame_mat = video_obj.get_video_frames()
    video_width = video_obj.get_video_width
    video_height = video_obj.get_video_height
    fps = video_obj.get_video_fps()

    
    if frame_mat == [] or frame_mat == [[]]:
        main_logger.warning('Empty frame from video {0}'.format(video_name))
    else:
        # execute openpose to predict labels into openpose_result list
        openpose_rt_flag = openpose_handler.exe_openpose(frame_mat, openpose_result, video_info, fps, video_width, video_height)
        if openpose_rt_flag == False:
            main_logger.error('Openpose execute failed to video {0}'.format(video_name))
        else:
            main_logger.info('Openpose execute successfully to video {0}'.format(video_name))

            # correlate lkj data and openpose result for violate judgment
            main_logger.info('Executing LKJ and openpose result correlation')
            match_rt, final_result, final_include_result = openpose_handler.match_lkj(lkj_file, video_info, openpose_result)
            if match_rt != 0:
                main_logger.error('LKJ and openpose result correlation contains some errors, please check openpose.log')
            else:
                main_logger.info('LKJ and openpose result correlation successfully')
                if match_rt != 0:
                    main_logger.error('LKJ and openpose result correlation contains some errors, please check openpose.log')
                else:
                    main_logger.info('LKJ and openpose result correlation successfully')
                    store_rt_flag = openpose_handler.store_result(final_result, video_info, mysql_db, video_obj, final_include_result)
                    if store_rt_flag == False:
                        main_logger.error('Violation result of video {0} stored contains some errors, please refer to openpose log for further details'.format(video_name))
                    else:
                        main_logger.info('Violation result of video {0} stored successfully'.format(video_name))       

def update_video(video_id, video_source):
    global main_logger,oracle_db
    main_logger.info('Updating video table with video_id {0} and source {1}'.format(video_id,video_source))
    if common.update_video_table(video_id, video_source, oracle_db) == True:
        main_logger.info('Video table update successfully')
    else:
        main_logger.error('Video table update failed') 

def update_lkj(lkj_id):
    global main_logger, oracle_db, mysql_db
    main_logger.info('Updating LKJ table with lkj id {0}'.format(lkj_id))
    if common.update_lkj_group_table(lkj_id, oracle_db, mysql_db) == True:
        main_logger.info('LKJ table update successfully')
    else:
        main_logger.error('LKJ table update failed')



def start():
    global main_logger, video_path, mysql_db
    main_logger.info('Walking through path under video path {0}'.format(video_path))
    for root,dirs,files in os.walk(video_path):
        for item in files:
            # check video file name
            path_file = root + os_sep + item
            if path_file.endswith('csv'):
                dir_tot_ct = len(os.listdir(root))
                dir_ct = 0
            if common.video_fname_check(path_file) == True:
                # retrieve video information from mysql db
                main_logger.info('Retrieving video {0} related information'.format(item))
                video_info_rt = common.get_video_info(os.path.splitext(item)[0], mysql_db)

                if video_info_rt[0] == False:
                    main_logger.error(video_info_rt[1])
                else:
                    video_info = video_info_rt[2]
                    main_logger.info(video_info_rt[1])
                    
                    # fetch related lkj file
                    lkj_file = video_info[0]
                    lkj_id = video_info[-3]
                    video_id = video_info[-2]
                    video_source = video_info[-1]

                    if not os.path.isfile(lkj_file):
                        main_logger.error('LKJ file {0} does not exist'.format(lkj_file))
                    else:
                        video_ini_flag = False
                        main_logger.info('Generating object for video {0}'.format(path_file))
                        try:
                            video_obj = video_handler.VideoHandler(path_file)
                            main_logger.info('Extracting frames from video {0}'.format(path_file))
                            video_obj.set_video_frames(skip_step=4, bilateralFlg = True)
                            video_ini_flag = True
                            main_logger.info('Frames extraction from video {0} successfully'.format(path_file))
                        except Exception:
                            main_logger.error('Frames extraction from video {0} error'.format(path_file), exc_info=True)
                            video_ini_flag = False

                        # parallel computing
                        if video_ini_flag == True:
                            
                            # run_yolo(video_obj, video_info, lkj_file)
                            # run_openpose(video_obj, video_info, lkj_file)
                            p1 = multiprocessing.Process(target=run_yolo,args=(video_obj, video_info, lkj_file))
                            p2=  multiprocessing.Process(target=run_openpose,args=(video_obj, video_info, lkj_file))

                            p1.start()
                            p2.start()

                            p1.join()
                            p2.join()
                    # update video table 
                    update_video(video_id, video_source)
                    dir_ct += 1
                    
                    if dir_ct == dir_tot_ct:
                        update_lkj(lkj_id):

if __name__ == '__main__':
    init('run_model')
    start()
                                    
