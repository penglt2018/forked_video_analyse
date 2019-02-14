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
import time
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
    global main_logger, mysql_db
    main_logger = False
    mysql_db = False
    main_logger = common.get_logger(log_name)
    
    # initialize darknet
     
    yolo_handler.init()

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

    if main_logger != False  and mysql_db != False:
        main_logger.info('Initializting process successfully')
        return True
    else:
        main_logger.error('Initializting process Failed!')
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


def start():
    global main_logger, video_path, mysql_db
    main_logger.info('Walking through path under video path {0}'.format(video_path))
    for root,dirs,files in os.walk(video_path):
        if len(root.split(os_sep)) == 3:
            dir_tot_ct = len(os.listdir(root))
            dir_ct = 0
        for item in files:
            # check video file name
            path_file = root + os_sep + item
            if common.video_fname_check(path_file) == True:
                s_time = time.time()
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
                    video_name = video_info[3]
                    #print(video_info)
                    lkj_id = video_info[-2]
                    #video_source = video_info[-1]

                    if not os.path.isfile(lkj_file):
                        main_logger.error('LKJ file {0} does not exist'.format(lkj_file))
                    else:
                        video_ini_flag = False
                        main_logger.info('Generating object for video {0}'.format(path_file))
                        try:
                            video_obj = video_handler.VideoHandler(path_file)
                            main_logger.info('Extracting frames from video {0}'.format(path_file))
                            video_obj.set_video_frames(skip_step=4, bilateralFlg = False)
                            video_ini_flag = True
                            main_logger.info('Frames extraction from video {0} successfully'.format(path_file))
                        except Exception:
                            main_logger.error('Frames extraction from video {0} error'.format(path_file), exc_info=True)
                            video_ini_flag = False

                        # parallel computing
                        if video_ini_flag == True:
                            run_yolo(video_obj, video_info, lkj_file)  

                    print("Yolo execute time: " + str(time.time() - s_time))                          

if __name__ == '__main__':
    init('run_model')
    start()
    common.close_db(mysql_db, 'mysql')                                    
