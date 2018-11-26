# coding:utf-8
'''
Program Name: Common Functions
File Name: common.py
Creation Date: Apr 2018
Programmer: XINWU LIU
Abstract: This program contains common functions
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
import sys
from configparser import ConfigParser
import logging
import logging.config
import time
import pandas as pd
import lib.lkj_lib as LKJLIB
import lib.ftp_client as ftp_client
os_sep = os.path.sep
import traceback

log_path = './logconfig.ini'

# Function to log, print error message and quit.
def raise_error(msg, err_code):
    #logger.error(msg)
    sys.stderr.write('{0}\n'.format(msg))
    raise SystemExit(err_code)


# Functions to get main config file
def get_config(cfg_path):
    cfg = ConfigParser()
    try:
        cfg.read(cfg_path)
    except Exception as e:
        raise_error("Error: Config file load error: {0} {1}".format(e, cfg_path), 7)
    return cfg

# Function to get log config file
def get_logger(log_name):
    try:
        logger = logging.getLogger(log_name)
    except Exception as e:
        raise_error('getting logger {0} error: {1}'.format(log_name, e), 8)
    return logger

try:
    logging.config.fileConfig(log_path)
except Exception as e:
    raise_error(e, 8)

cfg = get_config('config.ini')
oracle_logger = get_logger('oracle')
mysql_logger = get_logger('mysql')
ftp_logger = get_logger('ftp')


# Function to log error message.
def log_error(logger, msg):
    logger.error(msg)

# Function to check path existence.
def path_check(pt, logger, msg, err_code):
    if not os.path.isdir(pt):
        logger.error(msg)
        sys.stderr.write('{0}\n'.format(msg))
        raise SystemExit(err_code)
    
# Function to check file existence.
def file_check(f, logger, msg, err_code):
    if not os.path.isfile(f):
        logger.error(msg)
        sys.stderr.write('{0}\n'.format(msg))
        raise SystemExit(err_code)

def get_yolo_config():
    global cfg
    dn_path = cfg.get('yolo', 'darknet')
    mdl_cfg = cfg.get('yolo', 'cfg')
    weights = cfg.get('yolo', 'weights')
    meta = cfg.get('yolo', 'meta')
    return dn_path, mdl_cfg, weights, meta

def get_openpose_config():
    global cfg
    openpose_path = cfg.get('openpose', 'openpose_path')
    params = dict()
    params["openpose_path"] = cfg.get('openpose', 'logging_level')
    params["output_resolution"] = cfg.get('openpose', 'output_resolution')
    params["net_resolution"] = cfg.get('openpose', 'net_resolution')
    params["model_pose"] = cfg.get('openpose', 'model_pose')
    params["alpha_pose"] = cfg.get('openpose', 'alpha_pose')
    params["scale_gap"] = cfg.get('openpose', 'scale_gap')
    params["scale_number"] = cfg.get('openpose', 'scale_number')
    params["render_threshold"] = cfg.get('openpose', 'render_threshold')
    params["default_model_folder"] = cfg.get('openpose', 'default_model_folder')
    if type(params) != dict or len(params) < 11:
        raise_error('Error: Openpose params set wrong', 88)
    return openpose_path, params
    

# Function to check video file name
def video_fname_check(fname):
    ''' Function for checking video filename
        Input:
                fname: video filename
        return:
                True/False
    '''
    f_prefix, f_sufix = os.path.splitext(fname)
    if f_sufix != '.mp4' and f_sufix != '.avi':
        return False
    else:
        return True
        
    # # file name length check
    # if len(f_arr) != 5:
    #     logger.error('Video ' + fname + ' file name length is wrong!')
    #     return False

    # # train_num check
    # t_num = f_arr[1]
    # if len(t_num) != 4:
    #     logger.error('Video ' + fname + ' train_num length is wrong!')
    #     return False
    # if not t_num.isdigit():
    #     logger.error('Video ' + fname + ' train_num is NOT a digit!')
    #     return False

    # # terminal check
    # ter_num = f_arr[2]
    # if not ter_num.isdigit():
    #     logger.error('Video ' + fname + ' terminal number is NOT a digit!')
    #     return False
    # elif int(ter_num) != 1 and int(ter_num) != 2:
    #     logger.error('Video ' + fname + ' terminal number should be 1 or 2!(' + int(ter_num) + ')')
    #     return False

    # # date check
    # date = f_arr[3]
    # if len(date) != 8:
    #     logger.error('Video ' + fname + ' date lenght should be 8!')
    #     return False
    # elif not date.isdigit():
    #     logger.error('Video ' + fname + ' date is NOT a digit!')
    #     return False

    # # time check
    # tm = f_arr[4]
    # if len(tm) != 6:
    #     logger.error('Video ' + fname + ' time length should be 6!')
    #     return False
    # elif not date.isdigit():
    #     logger.error('Video ' + fname + ' time is NOT a digit!')
    #     return False

    # else

def add_to_db(mysql_db, video_info, result_list, table_name, violate, video_obj, save_path=None):
    ''' for each result from result_list, insert it to database
        input:
                mysql_db: mysql database
                video_info: video related information
                result_list: violate result list returned by model
                table_name: mysql table for storing violate result
                violate: violation name
                video_obj: custom video object, used for saving frames
                save_path: path for saving violate frames
        return:
                a True/False flag to determine the success of db insertion
    '''
    global mysql_logger
    mysql_logger.info('Execute begin')
    
    lkj_filename, video_st_tm, video_ed_tm, video_name, \
    train_type, train_num, channel, trace, driver_1, lkj_id, video_url = video_info
    
    for result in result_list:
        '''
        result list format:
            [ violate_st_tm, violate_st_frame_idx, label,
            violate_ed_tm, violate_ed_frame_idx, label ]
        '''
        violate_st_tm = result[0]
        if save_path != None:
            if not os.path.isdir(save_path):
                os.makedirs(save_path)

            violate_ed_tm = result[3]
            frame_st = result[1]
            frame_ed = result[4]

            sql = "insert into {0} values (\'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', \'{7}\', {8}, \'{9}\', \'{10}\', \'{11}\', \'{12}\', \'{13}\', \'{14}\', now(), \'{15}\')".\
                    format(table_name, lkj_filename, video_name, video_st_tm, video_ed_tm, \
                    train_type, train_num, channel, trace, driver_1, \
                    violate, violate_st_tm, violate_ed_tm, frame_st, frame_ed, video_url)
        else:
            sql = "insert into {0} ({1}) values (\'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', \'{7}\', {8}, \'{9}\', \'{10}\', \'{11}\', \'{12}\', now(), \'{13}\')".\
                    format(table_name, 'LKJ_FILENAME,VIDEO_FILENAME,VIDEO_STARTTIME,VIDEO_ENDTIME,TRAIN_TYPE,TRAIN_NUM,CHANNEL,TRACE,DRIVER_1,VIOLATE,START_TIME,INSERT_TIME,VIDEO_PATH',\
                    lkj_filename, video_name, video_st_tm, video_ed_tm,\
                    train_type, train_num, channel, trace, driver_1,\
                    violate, violate_st_tm, video_url)
        
        mysql_logger.info('Executing insert sql: {0}'.format(sql))
        try:
            mysql_db.Insert(sql)
            mysql_logger.info('Insert sql execute successfully')
            
            if save_path != None:
                video_obj.write_frames(save_path, video_name, frame_st, frame_ed)

        except Exception:
            mysql_logger.error('Insert sql execute failed', exc_info=True)
            return False
    return True

def channel_filt(result_list, lkj_df, video_name):
    '''
        this function is used for excluding non-operate
        channel by events in lkj data
        input: 
                result_list: openpose returned leave result list
                lkj_df: lkj dataframe
                video_name: video name
        output:
                rt_list: leave result after filtering
    '''
    rt_list = []
    for i in result_list:
        leave_ed_tm = i[3]
        lkj_channel=lkj_df[(lkj_df['事件']== '鸣笛开始') | (lkj_df['事件']== '鸣笛结束')][['时间', '其他']].drop_duplicates()
        channel = LKJLIB.channel_filter(lkj_channel, leave_ed_tm, 5)
        channel = channel.replace('II', '二').replace('I', '一')
        if channel != False:
            if channel in video_name:
                rt_list.append(i)
    return rt_list

def get_frame_time(fps,video_st_time,frame_index):
    """
        获取给定帧图像的时间

        Args:
            fps:视频帧率
            video_st_time:视频开始时间(格式为:'%Y-%m-%d %H:%M:%S')
            frame_index:待转换帧的index

        Returns:
            转换后的时间(格式为:'%Y-%m-%d %H:%M:%S')
    """
    st_time_timestamp = time.mktime(time.strptime(video_st_time, '%Y-%m-%d %H:%M:%S'))
    frame_timestamp = st_time_timestamp + int(int(frame_index) / int(fps))
    frame_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(frame_timestamp))
    return frame_time

def append_result(arr, frame_index, fps, video_st_time, label):
    ''' Function for appending model result to an list.
        input:
                arr: model result list
                frame_index: frame index
                fps: fps of the video
                video_st_time: begin time of the video
                label: violate
        return:
                None
    '''
    arr.append([get_frame_time(fps, video_st_time,frame_index), frame_index, label])

def get_lkj(lkj_local_file):
    ''' Function for reading lkj data from a csv file to pandas dataframe.
        Input:
                lkj_local_file: local lkj file with path
        output:
                [ True/False, log infor, LKJ pandas dataframe ]
    '''
    try:
        lkj_data = pd.read_csv(lkj_local_file, encoding='utf-8', names=['序号','事件','时间','里程','其他','距离','信号机','信号','速度','限速','零位','牵引','前后','管压','缸压','转速电流','均缸1','均缸2','dummy1','dummy2','dummy3','dummy4'])
        result = [True, 'LKJ file read successfully', lkj_data]
    except Exception:
        result = [False, 'LKJ file read error: {0}'.format(traceback.format_exc())]
    return result

def get_video_info(video_name, mysql_db):
    ''' Retrieve video infomation from Mysql 
        input:
                video_name: video filename without suffix
                mysql_db: mysql database connector object
        return:
                [ False, log info ] when failed, otherwise
                [ True, log info, sql_result ]
    '''
    global mysql_logger    
    # get video_start time via mysql
    mysql_logger.info('searching infomation related to video {0}'.format(video_name))
    qry_result = False      
    sql = "select lkj_filename,\
                date_format(video_st_tm, '%Y-%m-%d %H:%i:%s'), \
                date_format(video_ed_tm, '%Y-%m-%d %H:%i:%s'), \
                video_name, \
                train_type, \
                train_num, \
                channel, \
                trace, \
                driver_1, \
                lkj_id, \
                video_url \
                from violate_result.video_info \
                where video_name = \'{0}\'".format(video_name)

    qry_result = query_sql(mysql_db, 'mysql', sql)    

    # check video info
    print(qry_result)

    if qry_result == False:
        return [ False, 'video {0} information retrieve failed'.format(video_name) ]
    elif len(qry_result) > 1:
        return [ False, 'video {0} is related to more than one record {1}'.format(video_name, qry_result) ]
    elif len(qry_result) <= 0:
        return [ False, 'video {0} can NOT be found in database'.format(video_name) ]
    else:
        return [ True, 'video {0} information retrieve successfully'.format(video_name), qry_result[0]]

def connect_db(db_name):
    ''' Function for database connection
        input:
                db_name: mysql/oracle
        return:
                [connection flag, log infor, database object]
    '''
    global cfg
    username = cfg.get(db_name, 'user')
    password = cfg.get(db_name, 'password')
    host_name = cfg.get(db_name, 'host')
    port = cfg.get(db_name, 'port')

    # connect to oracle
    if db_name.lower() == 'oracle':
        db_logger = oracle_logger
        db_logger.info('{0} database connection begin'.format(db_name))
        from .cxOracle import cxOracle
        service = cfg.get(db_name,'service-name')
        protocol = cfg.get(db_name, 'protocol')
        # build tns for connection
        tns = '(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL={0})(HOST={1})(PORT={2})))(CONNECT_DATA=(SERVICE_NAME={3})))'.format(protocol,host_name,port,service)
        db_logger.info('Database connecting info: {0}'.format(tns))
        try:
            db = cxOracle(username, password, tns)
            log_info = '{0} database connect successfully'.format(db_name)
            db_logger.info(log_info)
            return [ True, log_info, db]
        except Exception:
            db_logger.error('{0} database connecting Failed: {1}'.format(db_name, tns), exc_info=True)
            return [ False, '{0} database connecting Failed!'.format(db_name) ]
    # connect to mysql
    elif db_name.lower() == 'mysql':
        db_logger = mysql_logger
        db_logger.info('{0} database connection begin'.format(db_name))
        from .pyMysql import Mysql
        # build tns for debug usage
        tns='host: {0}, port: {1}, username: {2}, password: {3}'.format(host_name, port, username, password)
        db_logger.info('Database connecting info: {0}'.format(tns))
        try:
            db = Mysql(username, password, host_name, port)
            log_info = '{0} database connect successfully'.format(db_name)
            db_logger.info(log_info)
            return [ True, log_info, db]
        except Exception:
            db_logger.error('{0} database connecting Failed: {1}'.format(db_name, tns), exc_info=True)
            return [ False, '{0} database connecting Failed!'.format(db_name) ]
    else:
        log_info = 'Can not connect to database {0}, database does not exist'.format(db_name)
        raise_error(log_info, 40)
        
def close_db(db, db_name):
    ''' Function for closing database:
        Input:
                db: database
                db_name: refer to which database
                         (oracle/mysql)
        return:
                None
    '''
    if db_name.lower() == 'oracle':
        db_logger = oracle_logger
    elif db_name.lower() == 'mysql':
        db_logger = mysql_logger
    else:
        raise_error('Database {0} does not exist!'.format(db_name), 41)

    db_logger.info('Closing {0} database connector'.format(db_name))
    try:
        db.__del__()
        db_logger.info('{0} database connector close successfully'.format(db_name))
    except Exception as e:
        db_logger.error('{0} database connector close failed'.format(db_name), exc_info=True)

def query_sql(db, db_name, sql):
    ''' Function for query sql and log
        input: 
                db: database object
        return:
                query_rt: sql result when no error occur, otherwise "False"
    '''
    if db_name.lower() == 'oracle':
        db_logger = oracle_logger
    elif db_name.lower() == 'mysql':
        db_logger = mysql_logger
    else:
        raise_error('Database {0} does not exist!'.format(db_name), 41)

    db_logger.info('Executing query sql: {0}'.format(sql))
    query_rt = []
    try:
        query_rt = db.Query(sql)
        db_logger.info('Query sql executing successfully')
    except Exception:
        query_rt = False
        db_logger.error('Query sql executing failed!', exc_info=True)

    return query_rt

def conn_ftp():
    ''' Function for connecting ftp server
        Input:
                None
        return:
                ftp connector object when connecting success,
                otherwise return "False"
    '''
    global ftp_logger, cfg
    ftp_logger.info('ftp connecting begin')
    ftp_host = cfg.get('ftp', 'host')
    ftp_port = cfg.get('ftp', 'port')
    ftp_uname = cfg.get('ftp', 'username')
    ftp_pwd = cfg.get('ftp', 'password')

    # connect to ftp server
    ftp_logger.info('Conneting to ftp server: {0}'.format([ftp_host,int(ftp_port), ftp_uname, ftp_pwd]))
    ftp_conn = ftp_client.getConnect(ftp_host, int(ftp_port), ftp_uname, ftp_pwd)
    if ftp_conn[0] == False: # ftp failed
        ftp_logger.error(ftp_conn[1])
        return False
    else:   # ftp success
        ftp_logger.info(ftp_conn[1])
        ftp_logger.info('Ftp connecting finish')
        return ftp_conn[2]

def update_lkj_table(lkj_id, oracle_db):
    ''' Function for updating LKJ table in Oracle database
        Input:
                lkj_id: primary key of lkj table (lkjvideoadmin.lkjvideoproblem)
                oracle_db: Oracle database connector object
        return:
                True or False for evaluation of the success of update process
    '''
    global oracle_logger
    oracle_logger.info('Updating lkj table begin')
    sql = "update lkjvideoadmin.lkjvideoproblem set ISANALYZED = 1 where lkjid = \'{0}\'".format(lkj_id)
    oracle_logger.info('Executing update sql: {0}'.format(sql))
    try:
        oracle_db.Exec(sql)
        oracle_logger.info('Update sql execute successfully')
        return True
    except Exception:
        oracle_logger.error('Update sql execute failed!', exc_info=True)
        return False

def update_lkj_group_table(lkj_id, oracle_db, mysql_db):
    ''' Function for updating LKJ table in oracle database based on
        the number of videos grouped by lkj id
        Input:
                lkj_id: primary key of lkj table (lkjvideoadmin.lkjvideoproblem)
                oracle_db: Oracle database connector object
                mysql_db: Mysql database connector object
        return:
                True or False for evaluation of the success of update process
    '''
    global oracle_logger, mysql_logger
    mysql_logger.info('Counting number of videos related to LKJ {0}'.format(lkj_id))
    count_sql = "select count(1) from violate_result.video_info where lkjid = {0} group by lkjid".format(lkj_id)
    cnt_result = query_sql(count_sql)
    #print(cnt_result)
    cnt = cnt_result[0][0]

    oracle_logger.info('Updating lkj table begin')
    update_sql = 'update lkjvideoadmin.lkjvideoproblem set videoanalyzed = videoanalyzed + {0}, ISANALYZED = 1 where lkjid = {1}'.format(cnt, lkj_id)
    oracle_logger.info('Executing update sql {0}'.format(update_sql))
    try:
        oracle_db.Exec(update_sql)
        oracle_logger.info('Update sql execute successfully')
        return True
    except Exception as e:
        oracle_logger.error('Update sql execute failed!', exc_info=True)
        return False

def update_video_table(video_id, video_source, oracle_db):
    ''' Function for updating video table (lkjvideoadmin.LAVDR) in Oracle database
        Input:
                video_id: key
                video_source: video_id + video_source = primary key of video table
                oracle_db: Oracle database connector object
        return:
                True or False for evaluation of the success of update process
    '''
    global oracle_logger
    oracle_logger.info('Updating video table begin')
    sql = "update lkjvideoadmin.LAVDR set ISANALYZED = 1 where id = \'{0}\' and DATASOURCE = \'{1}\'".format(video_id, video_source)
    oracle_logger.info('Executing update sql: {0}'.format(sql))
    try:
        oracle_db.Exec(sql)
        oracle_logger.info('Update sql execute successfully')
        return True
    except Exception:
        oracle_logger.error('Update sql execute failed!', exc_info=True)
        return False

def store_video_info(mysql_db, info_list):
    ''' Function for insert video information to video_info table
        in mysql database
        Input:
                mysql_db: mysql connector object
                info_list:  a list fetched from oracle database
                            after some modification
                return:
                            True or False for evaluation of the success of insert process
    '''
    global mysql_logger
    mysql_logger.info('Insert video info to video_info table execute begin')
    # resolve info
    lkj_filename, lkj_st_tm, lkj_ed_tm,\
    video_filename, video_st_tm, video_ed_tm,\
    train_type, train_num, channel, trace, driver_1, driver_2,\
    lkj_id, video_id, video_source, video_url = info_list

    sql = "insert into violate_result.video_info values (\'{0}\',\'{1}\',\'{2}\',\'{3}\',\'{4}\',\'{5}\',\'{6}\',\'{7}\',{8},\'{9}\', \'{10}\', \'{11}\', \'{12}\')"\
    .format(lkj_filename, lkj_st_tm, lkj_ed_tm, os.path.splitext(video_filename)[0], video_st_tm, video_ed_tm, train_type, train_num, int(channel), trace, driver_1, lkj_id, video_url)
    mysql_logger.info('Executing insert sql: {0}'.format(sql))
    try:
        mysql_db.Insert(sql)
        mysql_logger.info('Insert sql execute successfully')
        return True
    except Exception:
        mysql_logger.error('Insert sql execute failed: ', exc_info=True)
        return False

def isnum(s):
    try:
        nb = int(s)
        return True
    except ValueError as e:
        return False

def is_valid_time(str):
    try:
        time.strptime(str, "%Y-%m-%d %H:%M:%S")
        return True
    except:
        return False

def date_reformat(date):
    return date[:4] + '-' + date[4:6] + '-' + date[6:]

def time_reformat(tm):
    return tm[:2] + ':' + tm[2:4] + ':' + tm[4:]

def date_time_reformat(date, tm):
    return date_reformat(date) + " " + time_reformat(tm)
    
