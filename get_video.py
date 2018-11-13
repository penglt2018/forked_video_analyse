#coding:utf-8
"""
Created on 2017-10-26

@author: LIU XINWU

Functions of database operations 
"""
import sys 
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'  #或者os.environ['NLS_LANG'] = 'AMERICAN_AMERICA.AL32UTF8'
import src.common as common
import src.ftp_client as ftp_client
import src.time_check as time_check
from requests import get  # to make GET request
import traceback
os_sep = os.path.sep


def init(log_name):
    ''' initialization process including config parameters and logger fetch
        input: model log name
        return: config and loggers objects
    '''
    print('get_video initializing')
    cfg = common.get_config('config.ini')
    main_logger = common.get_logger(log_name, 'logconfig.ini', True)
    oracle_logger = common.get_logger('oracle', 'logconfig.ini', False)
    mysql_logger = common.get_logger('mysql', 'logconfig.ini', False)
    return cfg, main_logger, oracle_logger, mysql_logger

def update_video_table(video_id, video_source):
    global oracle_logger, oracle_db
    oracle_logger.info('function update_video_table: updating video table begin')
    sql = "update lkjvideoadmin.LAVDR set ISANALYZED = 1 where id = \'{0}\' and DATASOURCE = \'{1}\'".format(video_id, video_source)
    #sql = "update lkjvideoadmin.LAVDR set ISANALYZED = 1 where filename = \'http://10.196.205.47/{0}.mp4\'".format(video_name)
    oracle_logger.info('function update_video_table: executing update sql: {0}'.format(sql))
    try:
        oracle_db.Exec(sql)
        oracle_logger.info('function update_video_table: update sql execute successfully')
    except Exception as e:
        oracle_logger.error('function update_video_table: update sql execute failed: {0}'.format(traceback.format_exc()))
        return False
    return True

def update_lkj_table(lkj_id):
    global oracle_logger, oracle_db
    oracle_logger.info('function update_lkj_table: updating lkj table begin')
    sql = "update lkjvideoadmin.lkjvideoproblem set ISANALYZED = 1 where lkjid = \'{0}\'".format(lkj_id)
    #sql = "update lkjvideoadmin.LAVDR set ISANALYZED = 1 where filename = \'http://10.196.205.47/{0}.mp4\'".format(video_name)
    oracle_logger.info('function update_lkj_table: executing update sql: {0}'.format(sql))
    try:
        oracle_db.Exec(sql)
        oracle_logger.info('function update_lkj_table: update sql execute successfully')
    except Exception as e:
        oracle_logger.error('function update_lkj_table: update sql execute failed: {0}'.format(traceback.format_exc()))
        return False
    return True

def get_video_list():
    ''' connect to database and fetch required lkj and video files
        input: null
        return: a 2D list or False if errors occur
    '''
    global oracle_logger, main_logger
    main_logger.info('function get_video_list: execute begin')
    main_logger.info('function get_video_list: connecting to Oracle database')
    db = common.connect_db(cfg, oracle_logger, 'oracle')
    video_list = []
    if db == False:
        main_logger.error('function get_video_list: Oracle database connecting failed')
        return False, False
    else:
        main_logger.info('function get_video_list: Oracle database connect successfully')
        #video_list = [[]]
        # sql = 'select lkj.JICHEXINGHAO, lkj.JCH, lkj.TRACE, lkj.lkjwholecourse,\
        #         video.FILEPATH, video.STARTTIME, video.ENDTIME, video.CHNO, video.DRIVERNO, video.DRIVER2NO\
        #         from lkjvideoadmin.lkjvideoproblem lkj\
        #         inner join LAVDR video on lkj.LKJID = video.LKJID\
        #         where lkj.videoneedanaly > lkj.videoanalyzed and lkj.lkjwholecourse is not null and video.ISANALYZED = 0'
        #lkj_data, lkj_st_tm, lkj_ed_tm, video_url, video_st_tm, video_ed_tm, train_type, train_num, port, shift_num
        sql="""select lkj.lkjwholecourse, to_char(lkj.starttime, 'yyyymmddhh24miss') as lkj_st_tm, to_char(lkj.endtime, 'yyyymmddhh24miss') as lkj_ed_tm,
                video.FILEPATH, to_char(video.STARTTIME, 'yyyy-mm-dd hh24:mi:ss') as video_st_tm, to_char(video.ENDTIME,'yyyy-mm-dd hh24:mi:ss') as video_ed_tm, lkj.JICHEXINGHAO, lkj.JCH, video.CHNO, lkj.TRACE, video.DRIVERNO, video.DRIVER2NO,lkj.lkjid,                 video.ID, video.DATASOURCE 
                from lkjvideoadmin.lkjvideoproblem lkj 
                inner join LAVDR video 
                on lkj.locotypeno = video.TRAINNO 
                where (lkj.JCH='826' or lkj.JCH='827' or lkj.JCH='6110' or lkj.JCH='6167' or lkj.JCH='6169') and lkj.JICHEXINGHAO = 'HXD1C' 
                and lkj.videoneedanaly > lkj.videoanalyzed and lkj.lkjwholecourse is not null
                and not (video.STARTTIME <= lkj.STARTTIME or video.ENDTIME >= lkj.ENDTIME)
                and video.ISANALYZED = 0
		and (video.CHNO=2 or video.CHNO=10) 
                and lkj.starttime is not null and lkj.endtime is not null and video.FILEPATH is not null and video.STARTTIME is not null and video.ENDTIME is not null and lkj.JICHEXINGHAO is not null and lkj.JCH is not null 
and video.CHNO is not null and lkj.TRACE is not null and video.DRIVERNO is not null and lkj.lkjid is not null and video.ID is not null and video.DATASOURCE is not null 
                and rownum<=500 and video.filepath like '%HXD1C6167_成都运达_02_一端司机室_20180923_101500%'
                """
        #and cast(to_char(video.STARTTIME, 'hh24') as int) between 7 and 18
        #and to_char(lkj.starttime, 'yyyymmddhh24miss') like '201809%' and video.filepath like '%HXD1C0002_株洲所_02_一端司机室_20180906_211501%'
        #and (lkj.TRACE = '51454')"
                #and video.FILEPATH like '10.195.32.229%'
        main_logger.info('function get_video_list: fetching video list')
        oracle_logger.info('function get_video_list: executing query sql: {0}'.format(sql))
        try:
            video_list = db.Query(sql)
            oracle_logger.info('function get_video_list: query sql executing successfully')
        except Exception as e:
            video_list = False
            oracle_logger.error('function get_video_list: query sql executing failed: {0}'.format(traceback.format_exc()))

    if video_list == False:
        main_logger.error('function get_video_list: video_list fetch failed')
    if video_list == []:
        main_logger.warning('function get_video_list: video_list is empty, no required video')
    main_logger.info('function get_video_list: execute finish')
    return video_list, db

    #[lkj_file, video_file, video_st_tm, video_ed_tm, train_type, train_num, port, shift_num] 

def get_video_list_test():
    return [['/0506/012784.csv','20180101000000', '20180101010000', 'http://192.168.1.6/HXD11514B_成都运达_02_B节司机室_20171121_14300.mp4', '2018-01-01 00:00:00', '2018-01-01 00:15:00', 'HXD1', '0001A', 2, '2018-0001']]

# def get_ftp(cfg):
#     ''' get ftp connection info
#         input: configure file
#         return: host, port
#     '''
    
#     return host, port, uname, pwd

def conn_ftp(cfg):
    global main_logger
    main_logger.info('function conn_ftp: ftp connecting begin')
    ftp_host = cfg.get('ftp', 'host')
    ftp_port = cfg.get('ftp', 'port')
    ftp_uname = cfg.get('ftp', 'username')
    ftp_pwd = cfg.get('ftp', 'password')

    # connect to ftp server
    #ftp_host, ftp_port, ftp_uname, ftp_pwd = get_ftp(cfg)
    main_logger.info('function conn_ftp: Conneting to ftp server: {0}'.format([ftp_host,int(ftp_port), ftp_uname, ftp_pwd]))
    ftp_conn = ftp_client.getConnect(ftp_host, int(ftp_port), ftp_uname, ftp_pwd)
    if ftp_conn[0] == False: # ftp failed
        main_logger.error(ftp_conn[1])
        return False
    else:   # ftp success
        main_logger.info(ftp_conn[1])
        main_logger.info('function conn_ftp: ftp connecting finish')
        return ftp_conn[2]


def http_download(url, file_name):
    ''' download a file via http request
        input: url and output filename on local
        return: None
    '''
    from requests import get  # to make GET request
    # open in binary mode
    try:
        with open(file_name, "wb") as f:
            # get request
            response = get(url)
            f.write(response.content)
        result = [True, "http download " + url + " success"]
    except Exception as e:
        result = [False, "http download fail, reason:{0}".format(traceback.format_exc())]

    return result

def store_video_info(db, info_list):
    global mysql_logger
    mysql_logger.info('function store_video_info: store video info execute begin')
    lkj_data, lkj_st_tm, lkj_ed_tm, video_file, video_st_tm, video_ed_tm, train_type, train_num, port, shift_num, driver_1, driver_2,lkj_id, video_id, video_source,video_url = info_list
    sql = "insert into violate_result.video_info values (\'{0}\',\'{1}\',\'{2}\',\'{3}\',\'{4}\',\'{5}\',\'{6}\',\'{7}\',{8},\'{9}\', \'{10}\', \'{11}\', \'{12}\')"\
    .format(lkj_data, lkj_st_tm, lkj_ed_tm, os.path.splitext(video_file)[0], video_st_tm, video_ed_tm, train_type, train_num, int(port), shift_num, driver_1, lkj_id, video_url)
    mysql_logger.info('function store_video_info: executing insert sql: {0}'.format(sql))
    try:
        db.Insert(sql)
        mysql_logger.info('function store_video_info: insert sql execute successfully')
    except Exception as e:
        mysql_logger.error('function store_video_info: insert sql execute failed: {0}'.format(traceback.format_exc()))
        return False
    return True

def check_qry_rt(qry_list):
    global main_logger
    main_logger.info('function check_qry_rt: checking video info begin')
    lkj_data, lkj_st_tm, lkj_ed_tm, video_url, video_st_tm, video_ed_tm, train_type, train_num, port, shift_num, driver_1, driver_2, lkj_id, video_id, video_source = qry_list
    lkj_update_flg = False
    video_update_flg = False

    main_logger.info('function check_qry_rt: checking lkj_data suffix')
    if not lkj_data.endswith('csv'):
        lkj_update_flg = True
        main_logger.error('function check_qry_rt: lkj_data format error: {0}'.format(lkj_data))

    main_logger.info('function check_qry_rt: checking lkj_st_tm')
    if not lkj_st_tm or len(lkj_st_tm) != 14 or common.isnum(lkj_st_tm) == False:
        lkj_update_flg = True
        main_logger.error('function check_qry_rt: lkj_st_tm format error: {0}'.format(lkj_st_tm))

    main_logger.info('function check_qry_rt: checking lkj_ed_tm')
    if not lkj_ed_tm or len(lkj_ed_tm) != 14 or common.isnum(lkj_ed_tm) == False:
        lkj_update_flg = True
        main_logger.error('function check_qry_rt: lkj_ed_tm format error: {0}'.format(lkj_ed_tm))

    main_logger.info('function check_qry_rt: checking video_url')
    if not video_url.endswith('.mp4') or video_url.endswith('.avi') or len(video_url.split('/')) != 4:
        video_update_flg = True
        main_logger.error('function check_qry_rt: video_url format error: {0}'.format(video_url))

    main_logger.info('function check_qry_rt: checking video_st_tm')
    if common.is_valid_time(video_st_tm) == False:
        video_update_flg = True
        main_logger.error('function check_qry_rt: video_st_tm format error: {0}'.format(video_st_tm))

    main_logger.info('function check_qry_rt: checking train_type')
    if not train_type:
        video_update_flg = True
        main_logger.error('function check_qry_rt: train_type format error: {0}'.format(train_type))

    main_logger.info('function check_qry_rt: checking train_num')
    if not str(train_num):
        video_update_flg = True
        main_logger.error('function check_qry_rt: train_num format error: {0}'.format(train_num))

    main_logger.info('function check_qry_rt: checking port')
    if not str(port):
        video_update_flg = True
        main_logger.error('function check_qry_rt: port format error: {0}'.format(port))

    main_logger.info('function check_qry_rt: checking shift_num')
    if not str(shift_num):
        video_update_flg = True
        main_logger.error('function check_qry_rt: shift_num format error: {0}'.format(shift_num))

    main_logger.info('function check_qry_rt: checking driver_1')
    if not str(driver_1):
        video_update_flg = True
        main_logger.error('function check_qry_rt: driver_1 format error: {0}'.format(driver_1))
    
    if lkj_update_flg == False and video_update_flg == False:
        main_logger.info('function check_qry_rt: checking video info finish')
        return [True, qry_list]
    else:
        main_logger.warning('function check_qry_rt: check_qry_rt video info not passed')
        if lkj_update_flg == True:
            main_logger.info('function check_qry_rt: update lkj table with lkj_id {0} execute begin'.format(lkj_id))
            if update_lkj_table(lkj_id) == True:
                main_logger.info('function check_qry_rt: update lkj table successfully')
            else:
                main_logger.error('function check_qry_rt: update lkj table failed')

        if video_update_flg == True:
            main_logger.info('function check_qry_rt: update video table {0} with video_id {1} execute begin'.format(video_file, video_id))
            if update_video_table(video_id, video_source) == True:
                main_logger.info('function check_qry_rt: update video table {0} successfully'.format(video_file))
            else:
                main_logger.error('function check_qry_rt: update video table {0} failed'.format(video_file))    
        return [False, qry_list]
    
    

def download_file(video_list):
    ''' given a list containing video and lkj info
        download required lkj and video files to corresponding
        folders
        input: a 2D list or False if errors occur
        output: None
    '''
    global cfg, main_logger, mysql_logger
    main_logger.info('function download_file: execute begin')

    # get paths
    video_path=cfg.get('path', 'video_path')
    program_path = cfg.get('path', 'program_path')
    common.path_check(video_path, main_logger, 'Video path NOT set!', 8)
    main_logger.info('function download_file: video_path {0} get successfully'.format(video_path))
    common.path_check(program_path, main_logger, 'Program path NOT set!', 8)
    main_logger.info('function download_file: program_path {0} get successfully'.format(program_path))

    # connect to mysql database
    main_logger.info('function download_file: connecting to Mysql database')
    db = common.connect_db(cfg, mysql_logger, 'mysql')
    if db == False:
        main_logger.error('function download_file: Mysql database connect failed')
        return 
    else: 
        main_logger.info('function download_file: Mysql database connect successfully')
        ftp = conn_ftp(cfg)
        if ftp != False:
            for v in video_list:
                v = list(v)
                print(v)
                main_logger.info('function download_file: processing video info {0}'.format(v))
                ck_rt = check_qry_rt(v)
                if ck_rt[0] == True:
                    lkj_data, lkj_st_tm, lkj_ed_tm, video_url, video_st_tm, video_ed_tm, train_type, train_num, port, shift_num, driver_1, driver_2, lkj_id, video_id, video_source = ck_rt[1]
                    # if len(train_num) < 4 :
                    #     for _ in range(len(train_num), 4): train_num='0'+train_num
                    main_logger.info('function download_file: appending original video_url: {0}'.format(video_url))
                    v.append(video_url)
                    #print(video_url)
                    http, _, ip, video_fname = video_url.split('/')
                    main_logger.info('function download_file: regenerating video_url {0} for download'.format(video_url))
                    video_url = 'http://' + ip + ':8080/' + 'media/' + video_fname
                    #video_file = video_url.split['/'][-1]
                    lkj_fname = lkj_data.split('/')[-1]
                    main_logger.info('function download_file: update video file name to {0}'.format(video_fname))
                    v[3] = video_fname
                    main_logger.info('function download_file: update lkj file name to {0}'.format(lkj_fname))
                    v[0] = lkj_fname

                    # streo video info
                    main_logger.info('function download_file: store video info execute begin')
                    insrt_flag = store_video_info(db, v)
                    if insrt_flag == False:
                        main_logger.error('function download_file: store video info execute failed')
                    else:
                        dir_name = train_type + '_' + train_num + '_' + str(port) + '_' + shift_num + '_' + lkj_st_tm + '_' + lkj_ed_tm
                        main_logger.info('function download_file: preparing video store paths')
                        if train_type == 'HXD1' or train_type == 'HXD1C' or train_type == 'HXN5B':
                            dir_name = program_path + os_sep + video_path + os_sep + 'right_back/' + dir_name
                        else:
                            # need to add train_type error handling mechanism
                            break
                        print(dir_name)
                        if not os.path.isdir(dir_name):
                            main_logger.info('function download_file: creating dir {0}'.format(dir_name))
                            os.makedirs(dir_name)
                        lkj_local_file = dir_name + os_sep + lkj_fname

                        # if lkj file does not exist, download it via ftp
                        ftp_flag = True
                        if not os.path.isfile(lkj_local_file):
                            main_logger.info('function download_file: downloading lkj file {0} to {1}'.format(lkj_data, dir_name))
                            ftp_return = ftp_client.downloadFile(ftp, lkj_data, dir_name)
                            if ftp_return[0] == 1:
                                main_logger.info('function download_file: {0}'.format(ftp_return[1]))
                            else:
                                ftp_flag = False
                                main_logger.error('function download_file: {0}'.format(ftp_return[1]))

                        # download video file via http
                        if ftp_flag:
                            # get correct duan 
                            main_logger.info('function download_file: reading lkj data {0}/{1}'.format(dir_name, lkj_fname))
                            lkj_result = common.get_lkj(dir_name, lkj_fname)
                            if lkj_result[0] == False:
                                main_logger.error('function download_file: {0}'.format(lkj_result[1]))
                            else:
                                main_logger.info('function download_file: lkj data read successfully')
                                lkj_data = lkj_result[1]
                                main_logger.info('function download_file: filtering lkj data')
                                port_info=lkj_data[(lkj_data['事件']== '鸣笛开始') | (lkj_data['事件']== '鸣笛结束')][['时间', '其他']].drop_duplicates()
                                print("lkj shape before filter: {0}".format(lkj_data.shape))
                                print("lkj shape after filter: {0}".format(port_info.shape))
                                if port_info.shape[0] == 0 or port_info.shape[1] != 2:
                                    main_logger.warning('function download_file: lkj shape not correct after filter. shape: {0}'.format(port_info.shape))
                                    if update_lkj_table(lkj_id) == True:
                                        main_logger.info('function check_qry_rt: update lkj table successfully')
                                    else:
                                        main_logger.error('function check_qry_rt: update lkj table failed')
                                else: 
                                    main_logger.info('function download_file: fetching video channel in lkj data with time_check.port_filter')
                                    
                                    try:
                                        duan = time_check.port_filter(port_info, video_st_tm, 5)
                                    except Exception as e:
                                        main_logger.error('function download_file: time_check.port_filter execute failed {0}'.format(traceback.format_exc()))

                                    if duan == False:
                                        main_logger.error('function download_file: video channel get error: lkj: {0}, time:{1}'.format(lkj_fname, video_st_tm))
                                        main_logger.warning('function download_file: updating video table {0} with id {1}'.format(video_file, video_id))
                                        if update_video_table(video_id, video_source) == True:
                                            main_logger.info('function download_file: update video table {0} successfully'.format(video_file))
                                        else:
                                            main_logger.info('function download_file: update video table {0} failed'.format(video_file))
                                    else:
                                        main_logger.info('function download_file: filtering video file by channel')
                                        print(duan, video_fname, video_st_tm)
                                        duan = duan.replace('II', '二').replace('I', '一')
                                        #duan = duan.replace('II端','司机室2').replace('I端','司机室1')
                                        print(duan)
                                        #http, _, ip, video_fname = video_url.split('/')
                                        #video_url = http + '//' + ip + ':8080/' + 'media/' + video_fname
                                        #video_fname = video_url.split('/')[-1]
                                        video_file = dir_name + os_sep + video_fname
                                        if duan in video_file:
                                            main_logger.info('function download_file: downloading video file {0} to {1}'.format(video_url, video_file))
                                            http_result = http_download(video_url.replace('192.168.1.22', '10.183.217.228'), video_file)
                                            if http_result[0] == False:
                                                main_logger.error('function download_file: {0}'.format(http_result[1]))
                                            else:
                                                main_logger.info('function download_file: {0}'.format(http_result[1]))
                                                if int(os.path.getsize(video_file)/(1024*1024)) == 0:
                                                    if update_video_table(video_id, video_source) == True:
                                                        main_logger.info('function download_file: update video table {0} successfully'.format(video_file))
                                                    else:
                                                        main_logger.error('function download_file: update video table {0} failed'.format(video_file))
                                        else:
                                            main_logger.warning('function download_file: chanel {0} does NOT match video file {1}'.format(duan, video_file))
                                            if update_video_table(video_id, video_source) == True:
                                                main_logger.info('function download_file: update video table {0} successfully'.format(video_file))
                                            else:
                                                main_logger.error('function download_file: update video table {0} failed'.format(video_file))
                                            
        # close db
        mysql_logger.info('function download_file: closing database')
        try:
            db.__del__()
            mysql_logger.info('function download_file: database close successfully')
        except Exception as e:
            mysql_logger.error('function download_file: database close failed {0}'.format(traceback.format_exc()))

    main_logger.info('function download_file: execute finish')

if __name__ == '__main__':
    cfg, main_logger, oracle_logger, mysql_logger = init('get_video')
    main_logger.info('function main: execute begin')
    video_list, oracle_db = get_video_list()
    if video_list != [] and oracle_db != False:
        #print(video_list)
        download_file(video_list)

        # close db
        oracle_logger.info('function main: closing database')
        try:
            oracle_db.__del__()
            oracle_logger.info('function main: database close successfully')
        except Exception as e:
            oracle_logger.error('function main: database close failed {0}'.format(traceback.format_exc()))

    main_logger.info('function main: execute finish')
    # #video_list = get_video_list_test()

    # if video_list == [[]]:
    #     main_logger.info('No required video')
    # else:
        

    # lkj_file, video_file, video_st_tm, video_ed_tm, train_type, train_num, port, shift_num = test()

