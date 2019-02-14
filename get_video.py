#coding:utf-8
"""
Created on 2017-10-26

@author: LIU XINWU

Functions of database operations 
"""
import sys 
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'  #或者os.environ['NLS_LANG'] = 'AMERICAN_AMERICA.AL32UTF8'
import lib.common as common
import lib.lkj_lib as LKJLIB
import lib.ftp_client as ftp_client
from requests import get    # to make GET request
import traceback
os_sep = os.path.sep
video_path='./video'        # set download path

def init(log_name):
    ''' Function for initializing main logger and
        databse connector objects
        Input: 
                log name
        Return: 
                return True if all global variables are generated successfully,
                otherwise return False
    '''
    print('get_video initializing')
    global main_logger, oracle_db, mysql_db
    main_logger = False
    oracle_db = False
    mysql_db = False
    main_logger = common.get_logger(log_name)

    main_logger.info('Connecting to Oracle database')
    oracle_conn_rt = common.connect_db('oracle')    # conn_rt = [ True/False, log_info, database object ]
    if oracle_conn_rt[0] == False:
        main_logger.error(oracle_conn_rt[1])
    else:
        main_logger.info(oracle_conn_rt[1])
        oracle_db = oracle_conn_rt[2]

    main_logger.info('Connecting to Mysql database')
    mysql_conn_rt = common.connect_db('mysql')
    if mysql_conn_rt[0] == False:
        main_logger.error(mysql_conn_rt[1])
    else:
        main_logger.info(mysql_conn_rt[1])
        mysql_db = mysql_conn_rt[2] 

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

def video_size_check(video_file,video_id,video_source):
    ''' Function for checking video file size
        Input:
                video_file: local mp4 or avi file
        return:
                None
    '''
    global main_logger
    # if video file size is too small,
    # update video table
    size = os.path.getsize(video_file)
    if int(size/(1024*1024)) == 0:
        main_logger.warning('Video {0} size is too small {1}'.format(video_file, size))
        update_video(video_id, video_source)
        os.remove(video_file)

def http_download(url, local_file):
    ''' Function for downloading a file via http request
        input: 
                url:        url of the file on server side
                local_file: target file on local side
        return: 
                result:     [ True/False, log info ]
    '''
    from requests import get  # to make GET request
    # open in binary mode
    try:
        with open(local_file, "wb") as f:
            # get request
            response = get(url)
            f.write(response.content)
        result = [True, "http download " + url + " success"]
    except Exception as e:
        result = [False, "http download fail, reason:{0}".format(traceback.format_exc())]

    return result

def download_video(video_url, local_video_file,video_id,video_source):
    ''' Function for downloading video file to local
        input: 
                video_url:  url of a video file on server side
                local_video_file: target video file on local side
        return: 
                None
    '''
    global main_logger
    main_logger.info('Downloading video file {0} to {1}'.format(video_url, local_video_file))
    download_rt = http_download(video_url.replace('192.168.1.22', '10.183.217.228'), local_video_file)
    if download_rt[0] == False:
        main_logger.error(download_rt[1])
    else:
        main_logger.info(download_rt[1])
        # check local video file size after download
        video_size_check(local_video_file,video_id,video_source)
        
def check_qry_rt(qry_list):
    global main_logger
    main_logger.info('Checking video information')
    # resolve video information list
    lkj_file, lkj_st_tm, lkj_ed_tm, video_url, video_st_tm, video_ed_tm,\
    train_type, train_num, channel, trace, driver_1, driver_2,\
    lkj_id, video_id, video_source = qry_list

    # generate 2 flags for lkj and video checking mechanism independently
    # False for normal case and True for abnormal case
    lkj_update_flg = False
    video_update_flg = False

    main_logger.info('Checking LKJ file suffix')
    if not lkj_file.endswith('csv'):
        lkj_update_flg = True
        main_logger.warning('LKJ file format error: {0}'.format(lkj_file))

    main_logger.info('checking LKJ start time')
    if not lkj_st_tm or len(lkj_st_tm) != 14 or common.isnum(lkj_st_tm) == False:
        lkj_update_flg = True
        main_logger.warning('LKJ start time format error: {0}'.format(lkj_st_tm))

    main_logger.info('Checking LKJ end time')
    if not lkj_ed_tm or len(lkj_ed_tm) != 14 or common.isnum(lkj_ed_tm) == False:
        lkj_update_flg = True
        main_logger.warning('lkj_ed_tm format error: {0}'.format(lkj_ed_tm))

    main_logger.info('Checking video_url')
    if not video_url.endswith('.mp4') or video_url.endswith('.avi') or len(video_url.split('/')) != 4:
        video_update_flg = True
        main_logger.warning('video_url format error: {0}'.format(video_url))

    main_logger.info('Checking video start time')
    if common.is_valid_time(video_st_tm) == False:
        video_update_flg = True
        main_logger.warning('Video start time format error: {0}'.format(video_st_tm))

    main_logger.info('Checking train type')
    if not train_type:
        video_update_flg = True
        main_logger.warning('Train_type format error: {0}'.format(train_type))

    main_logger.info('Checking train number')
    if not str(train_num):
        video_update_flg = True
        main_logger.warning('Train number format error: {0}'.format(train_num))

    main_logger.info('Checking channel number')
    if not str(channel):
        video_update_flg = True
        main_logger.warning('Channel number format error: {0}'.format(channel))

    main_logger.info('Checking trace number')
    if not str(trace):
        video_update_flg = True
        main_logger.warning('Trace number format error: {0}'.format(trace))

    main_logger.info('Checking driver_1 id')
    if not str(driver_1):
        video_update_flg = True
        main_logger.warning('Driver_1 id format error: {0}'.format(driver_1))

    main_logger.info('Checking driver_2 id')
    if not str(driver_2):
        video_update_flg = True
        main_logger.warning('Driver_2 id format error: {0}'.format(driver_2))
    
    if lkj_update_flg == False and video_update_flg == False:
        main_logger.info('Checking video info finish')
        return [True, qry_list]
    else:
        main_logger.warning('Checking video info NOT passed')
        if lkj_update_flg == True:
            update_lkj(lkj_id)
        if video_update_flg == True:
            update_video(video_id, video_source)  
        return [False, qry_list]

def update_lkj(lkj_id):
    global main_logger, oracle_db
    main_logger.info('Updating LKJ table with lkj_id {0}'.format(lkj_id))
    if common.update_lkj_table(lkj_id, oracle_db) == True:
        main_logger.info('LKJ table update successfully')
    else:
        main_logger.error('LKJ table update failed!')

def update_video(video_id, video_source):
    global main_logger,oracle_db
    main_logger.info('Updating video table with video_id {0} and source {1}'.format(video_id,video_source))
    if common.update_video_table(video_id, video_source, oracle_db) == True:
        main_logger.info('Video table update successfully')
    else:
        main_logger.error('Video table update failed')    
 
def get_video_list():
    ''' Function which is used to connect to oracle database
        and fetch required lkj and video file information
        such as location, id, time, etc.

        input: 
                None
        return: 
                video_list: A 2D list containing a set of video info 
                            with corresponding lkj info when success,
                            otherwise return "False"
    '''
    global main_logger, oracle_db
    main_logger.info('Execute begin')
    # read sql from config/fetch.sql file
    with open('config/fetch.sql', 'r') as sql_f:
        sql = sql_f.read().replace('\n', ' ')

    main_logger.info('Fetching video list')
    video_list = common.query_sql(oracle_db, 'oracle', sql)

    if video_list == False:
        main_logger.error('Video list fetching process failed')
    elif video_list == []:
        main_logger.warning('Video list is empty, no required video')
    else:
        main_logger.info('Video list fetch successfully')
    main_logger.info('Execute finish')
    return video_list
    
def get_video_channel(lkj_local_file, lkj_id, video_st_tm):
    ''' Function for reading lkj file and get the channel info
        Input:
                lkj_local_file: lkj file name with path
                lkj_id:         primary key of the lkj in lkjvideoproblem
                                table in Oracle database
                video_st_tm:    video start time
        return:
                lkj_channel: channel info in lkj data
    '''
    # begin channel check mechanism
    main_logger.info('Reading lkj file {0}'.format(lkj_local_file))
    lkj_rd_rt = common.get_lkj(lkj_local_file)
    if lkj_rd_rt[0] == False:
        main_logger.error(lkj_rd_rt[1])
    else:
        main_logger.info(lkj_rd_rt[1])
        lkj_data = lkj_rd_rt[2]
        main_logger.info('Filtering lkj data')
        # the value of '其他' related the event of '鸣笛开始' and '鸣笛结束'
        # is used for channel determination
        lkj_data=lkj_data[(lkj_data['事件']== '鸣笛开始') | (lkj_data['事件']== '鸣笛结束')][['时间', '其他']].drop_duplicates()
        print("lkj shape before filter: {0}".format(lkj_data.shape))
        print("lkj shape after filter: {0}".format(lkj_data.shape))
        if lkj_data.shape[0] == 0 or lkj_data.shape[1] != 2:
            main_logger.warning('LKJ shape not correct after filter, shape: {0}'.format(lkj_data.shape))
            main_logger.info('Updating LKJ table in Oracle database')
            if common.update_lkj_table(lkj_id, oracle_db) == True:
                main_logger.info('LKJ table updated successfully')
            else:
                main_logger.error('LKJ table updated failed')
            return False
        else:
            # find video start time = the time of the event of '鸣笛开始' and '鸣笛结束'
            # then video channel = the value of '其他' related the event of '鸣笛开始' and '鸣笛结束'
            try:
                lkj_channel = LKJLIB.channel_filter(lkj_data, video_st_tm, 5)
                main_logger.info('Channel get successfully')
                return lkj_channel
            except Exception as e:
                main_logger.error('Channel get failed', exc_info=True)
                return False

def download_file(video_list):
    ''' Function for downloading lkj and video files to specific paths
        given a list containing video and lkj infor
        input: 
                video_list: a 2D list or False if errors occur
        return: 
                True or False for evaluate downloading process
    '''
    global main_logger, mysql_db
    main_logger.info('Download program execute begin')
    main_logger.info('Checking video path')
    
    if not os.path.isdir(video_path):
        main_logger.warning('Video path does not exist, creating path {0}'.format(video_path))
        os.makedirs(video_path)
    main_logger.info('Video path {0} is ready'.format(video_path))

    # connecting to ftp server for downloading lkj file
    main_logger.info('Connecting to ftp server')
    ftp_con = common.conn_ftp()
    if ftp_con == False:
        main_logger.error('ftp server connecting failed!')
        return False
    else:
        main_logger.info('Ftp server connecting successfully')
        main_logger.info('Looping video list')
        # for each video file
        for v in video_list:
            v = list(v)
            print(v)
            main_logger.info('processing {0}'.format(v))
            # check video information fetched from oracle database
            ck_rt = check_qry_rt(v) # ck_rt = [ True/False, video_info ]
            if ck_rt[0] == True:
                # resolve video infor
                lkj_file, lkj_st_tm, lkj_ed_tm,\
                video_url, video_st_tm, video_ed_tm,\
                train_type, train_num, channel, trace, driver_1, driver_2,\
                lkj_id, video_id, video_source = ck_rt[1]

                # backup video_url at the end of video info list
                # for modification usage
                v.append(video_url) 
                #print(video_url)
                
                # resovle video url
                http, _, ip, video_fname = video_url.split('/')
                main_logger.info('Modifying video_url from {0}'.format(video_url))
                # build correct video_url which is used for further download process
                video_url = 'http://' + ip + ':8080/' + 'media/' + video_fname
                main_logger.info('Video url is changed to {0}'.format(video_url))

                # change v[3] from video url to video filename
                v[3] = video_fname
                main_logger.info('Video filename is set to {0}'.format(v[3]))
                
                # prepare path for storing video and lkj files
                dir_name = train_type + '_' + train_num + '_' + str(channel) + '_' + trace + '_' + lkj_st_tm + '_' + lkj_ed_tm
                # add a camera direction path as prefix
                if train_type == 'HXD1' or train_type == 'HXD1C' or train_type == 'HXN5B' or train_type == 'HXD2':
                    dir_name = video_path + os_sep + 'right_back' + os_sep + dir_name
                else:
                    # need to add train_type error handling mechanism
                    break
                print(dir_name)
                if not os.path.isdir(dir_name):
                    os.makedirs(dir_name)
                    main_logger.info('Path {0} created successfully'.format(dir_name))

                # change v[0] from lkj file path to lkj filename
                lkj_fname = lkj_file.split('/')[-1] # get lkj filename
                lkj_local_file = dir_name + os_sep + lkj_fname    
                v[0] = lkj_local_file
                main_logger.info('LKJ filename is set to {0}'.format(v[0]))

                # streo video info
                main_logger.info('Storing video info to table video_info in mysql')
                insrt_flag = common.store_video_info(mysql_db, v)
                if insrt_flag == False:
                    main_logger.error('Video information stored failed')
                else:
                    # set lkj file in local for downloading via ftp
                    ftp_flag = True
                    if not os.path.isfile(lkj_local_file):
                        main_logger.info('Downloading lkj file {0} to {1}'.format(lkj_file, lkj_local_file))
                        ftp_return = ftp_client.downloadFile(ftp_con, lkj_file, dir_name)
                        # ftp_return = [ 1/-1, log information ]
                        if ftp_return[0] == 1:
                            main_logger.info(ftp_return[1])
                        else:
                            ftp_flag = False
                            main_logger.error(ftp_return[1])

                    if ftp_flag == True:
                        video_channel = get_video_channel(lkj_local_file, lkj_id, video_st_tm)
                        if video_channel == False:
                            main_logger.error('Video channel get error: lkj: {0}, time:{1}'.format(lkj_local_file, video_st_tm))
                            update_video(video_id, video_source)
                        else:
                            main_logger.info('Filtering video file by video channel')
                            print(video_channel, video_fname, video_st_tm)
                            # video_channel get from lkj looks like 'II端'
                            # while channel in video filename looks like '二端'
                            # so need to replace II to 二 and I to 一
                            video_channel = video_channel.replace('II', '二').replace('I', '一').replace('一端', '_02_').replace('二端', '_10_')
                            print(video_channel)
                            
                            # set video file in local for downloading via http
                            video_file = dir_name + os_sep + video_fname
                            if video_channel in video_file: # only download channel matched video file
                                download_video(video_url, video_file, video_id,video_source)
                            else:
                                main_logger.warning('LKJ channel {0} does NOT match video file {1}'.format(video_channel, video_file))
                                update_video(video_id, video_source)

    main_logger.info('Download program execute finish')

if __name__ == '__main__':
    init_flag = init('get_video')
    if init_flag == True:
        main_logger.info('Execute start')
        video_list = get_video_list()
        if video_list != []:
            #print(video_list)
            download_file(video_list)
        # close database connector
        common.close_db(oracle_db, 'oracle')
        common.close_db(mysql_db, 'mysql')
        main_logger.info('Database connetors close finish')
    main_logger.info('Execute finish')
    
