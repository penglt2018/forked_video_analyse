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
import src.time_check as time_check
os_sep = os.path.sep
import traceback

def leave_filt(leave_result, lkj_data, video_name):
    '''
        this function is used for excluding non-operate
        channel by events in lkj data
        input: 
                leave_result: openpose returned leave result list
                lkj_data: lkj dataframe
                video_name: video name
        output:
                rt_list: leave result after filtering
    '''
    rt_list = []
    for i in leave_result:
        leave_ed_tm = i[4]
        port_info=lkj_data[(lkj_data['事件']== '鸣笛开始') | (lkj_data['事件']== '鸣笛结束')][['时间', '其他']].drop_duplicates()
        channel = time_check.port_filter(port_info, leave_ed_tm, 5)
        if channel != False:
            if channel in video_name:
                rt_list.append(i)
    return rt_list

# Function to log, print error message and quit.
def raise_error(msg, err_code):
	#logger.error(msg)
	sys.stderr.write('{0}\n'.format(msg))
	raise SystemExit(err_code)

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

# Functions to get main config file
def get_config(cfg_path):
	cfg = ConfigParser()
	try:
		cfg.read(cfg_path)
	except Exception as e:
		raise_error("Error: Config file load error: {0} {1}".format(e, cfg_path), 7)
	return cfg

# Function to get log config file
def get_logger(log_name, log_path, main):
	if main == True:
		try:
			logging.config.fileConfig(log_path)
		except Exception as e:
			raise_error('log config file {0} can not be found: {1}'.format(log_path, e), 8)
	try:
		logger = logging.getLogger(log_name)
	except Exception as e:
		raise_error('getting logger {0} error: {1}'.format(log_name, e), 8)
	return logger

# Function to check video file name
def video_fname_check(fname, logger):
	f_prefix, f_sufix = os.path.splitext(fname)
	#f_arr = f_prefix.split('_')
	
	# suffix check
	if f_sufix != '.mp4' and f_sufix != '.avi':
		#logger.error('Video ' + fname + ' is NOT a support video format!(' + f_sufix + ')')
		return False
		
	# # file name length check
	# if len(f_arr) != 5:
	# 	logger.error('Video ' + fname + ' file name length is wrong!')
	# 	return False

	# # train_num check
	# t_num = f_arr[1]
	# if len(t_num) != 4:
	# 	logger.error('Video ' + fname + ' train_num length is wrong!')
	# 	return False
	# if not t_num.isdigit():
	# 	logger.error('Video ' + fname + ' train_num is NOT a digit!')
	# 	return False

	# # terminal check
	# ter_num = f_arr[2]
	# if not ter_num.isdigit():
	# 	logger.error('Video ' + fname + ' terminal number is NOT a digit!')
	# 	return False
	# elif int(ter_num) != 1 and int(ter_num) != 2:
	# 	logger.error('Video ' + fname + ' terminal number should be 1 or 2!(' + int(ter_num) + ')')
	# 	return False

	# # date check
	# date = f_arr[3]
	# if len(date) != 8:
	# 	logger.error('Video ' + fname + ' date lenght should be 8!')
	# 	return False
	# elif not date.isdigit():
	# 	logger.error('Video ' + fname + ' date is NOT a digit!')
	# 	return False

	# # time check
	# tm = f_arr[4]
	# if len(tm) != 6:
	# 	logger.error('Video ' + fname + ' time length should be 6!')
	# 	return False
	# elif not date.isdigit():
	# 	logger.error('Video ' + fname + ' time is NOT a digit!')
	# 	return False

	# else
	return True

def get_frame_time(fps,st_time,frame_index):
    """
        获取给定帧图像的时间

        Args:
            fps:视频帧率
            st_time:视频开始时间(格式为:'%Y-%m-%d %H:%M:%S')
            frame_index:待转换帧的index

        Returns:
            转换后的时间(格式为:'%Y-%m-%d %H:%M:%S')
    """
    st_time_timestamp = time.mktime(time.strptime(st_time, '%Y-%m-%d %H:%M:%S'))
    frame_timestamp = st_time_timestamp + int(int(frame_index) / int(fps))
    frame_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(frame_timestamp))
    return frame_time


def add_result(arr, fname, fps, st_time, label):
	''' compute pos time by video start time, fps and frame index,
	    then add to result array.

	    input:
		    	arr: result array
		    	fname: frame filename
		    	fps: fps of the video
		    	st_time: begine time of the video
		    	label: violate
	    output:
	    		result array
	'''
	frame_index = fname.split("_")[-1]
	# print(frame_index)
	arr.append([get_frame_time(fps, st_time,frame_index), frame_index, fname+'.png', label])

def get_lkj(dirname, fname):
    #global video_pth
    ''' read lkj data from a csv file to pandas dataframe.

    	input:
    			dirname: directory of a lkj csv file
    			fname: lkj csv filename
    	output:
    			pandas dataframe
    '''
    lkj_file = dirname + os_sep + fname.split(os_sep)[-1]
    try:
        lkj_data = pd.read_csv(lkj_file, encoding='utf-8', names=['序号','事件','时间','里程','其他','距离','信号机','信号','速度','限速','零位','牵引','前后','管压','缸压','转速电流','均缸1','均缸2','dummy1','dummy2','dummy3','dummy4'])
        result = [True, lkj_data]
    except Exception as e:
        result = [False, 'lkj_data read error: {0}'.format(traceback.format_exc())]
    #date_str = dirname.split('_')[-1]
    #date_str_fmt = date_str[:4]+'-'+date_str[4:6]+'-'+date_str[6:]
    #date_str_fmt = common.date_reformat(date_str)
    return result #, date_str_fmt


def get_video_info(root_arr, db, model_logger, mysql_logger):
    ''' get corresponding video infomation given by a frame path
        input:
                db: database
                root_arr: path list split by '/'
        return:
                go_flg: a boolean flag to determine the success of fetching video infomation
                qry_result: video information 
    '''
    #global model_logger, mysql_logger
    dirname = root_arr[-1].split('_')   # dirname include video info
    model_logger.info('function get_video_info: dir name {0} get successfully'.format(dirname))
    video_name = '_'.join(dirname[:-2])
    model_logger.info('function get_video_info: video name {0} get successfully'.format(video_name))
    fps = dirname[-1]
    model_logger.info('function get_video_info: fps {0} get successfully'.format(fps))
    # format time to 'yyyy-mm-dd hh:mm:ss'
    #st_time = dirname[-3][:4] + '-' + dirname[-3][4:6] + '-' + dirname[-3][6:] + " " + dirname[-2][:2] + ":" + dirname[-2][2:4] +":"+dirname[-2][4:]
    
    # get video_start time via mysql
    model_logger.info('function get_video_info: searching video infomation')
    sql = "select lkj_data, date_format(video_st_tm, '%Y-%m-%d %H:%i:%s'), date_format(video_ed_tm, '%Y-%m-%d %H:%i:%s'), video_name, train_type, train_num, port, shift_num, driver, lkjid, video_path from violate_result.video_info where video_name = \'{0}\'".format(video_name)
    mysql_logger.info('function get_video_info: executing query sql: {0}'.format(sql))
    try:
        qry_result = db.Query(sql)
        mysql_logger.info('function get_video_info: query sql execute successfully')
    except Exception as e:
        mysql_logger.error('function get_video_info: query sql execute failed: {0}'.format(traceback.format_exc()))
        qry_result = False
    print(qry_result)

    go_flg = True
    if qry_result == False:
        model_logger.error('function get_video_info: some errors occur during searching video information via mysql')
        go_flg = False
    elif len(qry_result) > 1:
        model_logger.error('function get_video_info: the video {0} is related to more than one record {1}'.format(video_name, qry_result))
        go_flg = False
    elif len(qry_result) <= 0:
        model_logger.error('function get_video_info: the video {0} can not be found in database'.format(video_name))
        go_flg = False
    else:
        return go_flg, qry_result


# def add_to_db(db, qry_result, result_list, table_name, violate, mysql_logger):
#     ''' for each result from result_list, insert it to database
#         input:
#                 db: database
#                 root_arr: path list split by '/'
#                 result_list: the result list returned by model
#                 driver: driver info
#                 violate: violate tag
#         return:
#                 a boolean flag to determine the success of db insertion
#     '''
#     mysql_logger.info('function add_to_db: execute begin')
#     # dirname = root_arr[-1].split('_')
#     # train_type, train_num, duan = dirname[0], dirname[1], dirname[2]
#     lkj_fname, video_st_tm, video_ed_tm, video_name, traintype, trainum, port, shift_num, driver, _, video_path = qry_result
#     #print(video_path)
#     for result in result_list:
#         #ptc_fname = result[2]
#         violate_st_tm = result[0]
#         #violate_ed_tm = result[4]
#         #frame_st = result[1]
#         #frame_ed = result[5]
#         #violate = result[3]
#         #violate = '未手比'

#         sql = "insert into {0} ({1}) values (\'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', \'{7}\', {8}, \'{9}\', \'{10}\', \'{11}\', \'{12}\', now(), \'{13}\')".\
#             format(table_name, 'LKJ_FILENAME,VIDEO_FILENAME,VIDEO_STARTTIME,VIDEO_ENDTIME,TRAIN_TYPE,TRAIN_NUM,PORT,SHIFT_NUM,DRIVER,VIOLATE,START_TIME,INSERT_TIME,VIDEO_PATH',\
#                 lkj_fname, video_name, video_st_tm, video_ed_tm, traintype, trainum, port, shift_num, driver, violate, violate_st_tm, video_path)
#         mysql_logger.info('function add_to_db: executing insert sql: {0}'.format(sql))
#         try:
#             db.Insert(sql)
#             mysql_logger.info('function add_to_db: insert sql execute successfully')
#         except Exception as e:
#             mysql_logger.error('function add_to_db: insert sql execute failed: {0}'.format(traceback.format_exc()))
#             return False
#     return True

def add_to_db(db, qry_result, result_list, table_name, violate, mysql_logger, save_tmp=None):
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
    mysql_logger.info('function add_to_db: execute begin')
    # dirname = root_arr[-1].split('_')
    # train_type, train_num, duan = dirname[0], dirname[1], dirname[2]
    lkj_fname, video_st_tm, video_ed_tm, video_name, traintype, trainum, port, shift_num, driver,_,video_path = qry_result
    for result in result_list:
        violate_st_tm = result[0]
        if save_tmp != None:
            ptc_fname = result[2]
            violate_ed_tm = result[4]
            frame_st = result[1]
            frame_ed = result[5]
        #violate = result[3]
        #print(result)
        #print(qry_result)
        #sql="insert into {0} ({1}) values (\'{2}\',\'{3}\',\'{4}\',\'{5}\',\'{6}\',\'{7}\',\'{8}\',\'{9}\',\'{10}\',\'{11}\')".format('edward_database.action_result', 'filename,traintype,trainum,start_time,end_time,start_frame,end_frame,driver,action,port', result[2], train_type, train_num, result[0], result[3], result[1], result[4], driver, violate, duan)
            sql = "insert into {0} values (\'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', \'{7}\', {8}, \'{9}\', \'{10}\', \'{11}\', \'{12}\', \'{13}\', \'{14}\', now(), \'{15}\')".\
                format(table_name, lkj_fname, video_name, video_st_tm, video_ed_tm, traintype, trainum, port, shift_num, driver, violate, violate_st_tm, violate_ed_tm, frame_st, frame_ed, video_path)
        else:
        	sql = "insert into {0} ({1}) values (\'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', \'{7}\', {8}, \'{9}\', \'{10}\', \'{11}\', \'{12}\', now(), \'{13}\')".\
            format(table_name, 'LKJ_FILENAME,VIDEO_FILENAME,VIDEO_STARTTIME,VIDEO_ENDTIME,TRAIN_TYPE,TRAIN_NUM,PORT,SHIFT_NUM,DRIVER,VIOLATE,START_TIME,INSERT_TIME,VIDEO_PATH',\
                lkj_fname, video_name, video_st_tm, video_ed_tm, traintype, trainum, port, shift_num, driver, violate, violate_st_tm, video_path)
        
        mysql_logger.info('function add_to_db: executing insert sql: {0}'.format(sql))
        try:
            db.Insert(sql)
            mysql_logger.info('function add_to_db: insert sql execute successfully')
            if save_tmp != None:
            	save_tmp.write(video_name + ',' + frame_st + ',' + frame_ed+'\n')
        except Exception as e:
            mysql_logger.error('function add_to_db: insert sql execute failed: {0}'.format(traceback.format_exc()))
            return False
    return True

# def add_to_db(db, qry_result, result_list, violate_conti):
#     ''' for each result from result_list, insert it to database
#         input:
#                 db: database
#                 root_arr: path list split by '/'
#                 result_list: the result list returned by model
#                 driver: driver info
#                 violate: violate tag
#         return:
#                 a boolean flag to determine the success of db insertion
#     '''
#     global mysql_logger, main_logger
#     main_logger.info('starting add_to_db')

#     # dirname = root_arr[-1].split('_')
#     # train_type, train_num, duan = dirname[0], dirname[1], dirname[2]
#     lkj_fname, video_st_tm, video_ed_tm, video_name, traintype, trainum, port, shift_num, driver = qry_result
#     for result in result_list:
#         ptc_fname = result[2]
#         violate_st_tm = result[0]
#         violate_ed_tm = result[4]
#         frame_st = result[1]
#         frame_ed = result[5]
#         violate = result[3]
#         if violate_conti:
#         	sql = "insert into violate_result.report ({0}) values (\'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', {7}, \'{8}\', \'{9}\', \'{10}\', \'{11}\', \'{12}\')".\
#             	format('LKJ_FILENAME,VIDEO_FILENAME,VIDEO_STARTTIME,VIDEO_ENDTIME,TRAIN_TYPE,TRAIN_NUM,PORT,SHIFT_NUM,DRIVER,VIOLATE,START_TIME',\
#                 	lkj_fname, video_name, video_st_tm, video_ed_tm, traintype, trainum, port, shift_num, driver, violate, violate_st_tm, frame_st)
#         else:
#         	sql = "insert into violate_result.report values (\'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', {7}, \'{8}\', \'{9}\', \'{10}\', \'{11}\', \'{12}\', \'{13}\', \'{14}\')".\
#         		format(lkj_fname, video_name, video_st_tm, video_ed_tm, traintype, trainum, port, shift_num, driver, violate, violate_st_tm, violate_ed_tm, frame_st, frame_ed)
#         mysql_logger.info('executing insert sql: {0}'.format(sql))
#         try:
#             db.Insert(sql)
#             mysql_logger.info('insertion sql executing successfully')
#         except Exception as e:
#             mysql_logger.error('Insertion sql executing failed: {0}'.format(traceback.format_exc()))
#             return Fasle
#     return True

# Get DB info
def connect_db(cfg, db_logger, db_name):
	#global cfg, db_logger
	username = cfg.get(db_name, 'user')
	password = cfg.get(db_name, 'password')
	host_name = cfg.get(db_name, 'host')
	port = cfg.get(db_name, 'port')

	db_logger.info('function connect_db: Database connection begin')
	db = False
	if db_name.lower() == 'oracle':
		from .cxOracle import cxOracle
		service = cfg.get(db_name,'service-name')
		protocol = cfg.get(db_name, 'protocol')
		tns = '(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL={0})(HOST={1})(PORT={2})))(CONNECT_DATA=(SERVICE_NAME={3})))'.format(protocol,host_name,port,service)
		db_logger.info('function connect_db: Database connecting info: {0}'.format(tns))
		try:
			db = cxOracle(username, password, tns)
			db_logger.info('function connect_db: {0} database connect successfully'.format(db_name))
		except Exception as e:
			db_logger.error('function connect_db: Database connecting Failed: {0} {1}'.format(tns, e))
	elif db_name.lower() == 'mysql':
		from .pyMysql import Mysql
		tns='host: {0}, port: {1}, username: {2}, password: {3}'.format(host_name, port, username, password)
		db_logger.info('function connect_db: Database connecting info: {0}'.format(tns))
		try:
			db = Mysql(username, password, host_name, port)
			db_logger.info('function connect_db: {0} database connect successfully'.format(db_name))
		except Exception as e:
			db_logger.error('function connect_db: Database connecting Failed: {0} {1}'.format(tns,e))
	else:
		db_logger.error('function connect_db: Can not connect to database {0}, database does not exist'.format(db_name))

	db_logger.info('function connect_db: Database connection finish')
	if db != False:
		db_logger.info("function connect_db: {0} database conneting successfully".format(db_name))
	else:
		db_logger.error("function connect_db: {0} database conneting failed".format(db_name))
	return db

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
	
