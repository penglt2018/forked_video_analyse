########################################################################################
#
# Program Name: 视频转图像
# File Name: video_handler.py
# Creation Date: Apr 2018
# Programmer: BANGFAN LIU
# Abstract: 视频基本信息获取，保存降采样后的图像
# Entry Condition: N/A
# Exit Condition: N/A
# Example: N/A
# Program Message: N/A
# Remarks: N/A
# Amendment Hisotry:
#           Version:
#           Date:
#           Programmer:
#           Reason:
#
########################################################################################
import os
import cv2
import time
import math
import numpy as np

class VideoHandler(object):
    """
        获取输入视频的基本信息
        对视频进行降采样处理
    """

    def __init__(self,videoPath):
        """
            获取视频基本信息：帧率、总帧数、分辨率

            Args:
                videoPath:视频的输入路径及视频名称
                       eg:/home/test.avi
        """
        self._videoPath = videoPath
        self._cap = cv2.VideoCapture(videoPath)
        self._fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._frames = self._cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self._width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    @property
    def get_video_fps(self):
        return self._fps
    @property
    def get_video_frames(self):
        return self._frames
    @property
    def get_video_width(self):
        return self._width
    @property
    def get_video_height(self):
        return self._height
    @property
    def get_video_path(self):
        return self._videoPath
    @property
    def get_video_time_length(self):
        return int(round(self._frames / self._fps))

    def get_frame_index(self,time_list=[]):
        """需要增加判断输入的时间是否在合理范围内(目前没有加)"""
        if time_list:
            video_name_list = os.path.splitext(os.path.basename(self._videoPath))[0].split('_')
            video_st_time = video_name_list[-2] + video_name_list[-1]
            video_st_timestamp = time.mktime(time.strptime(video_st_time, '%Y%m%d%H%M%S'))
            timestamp_list = [time.mktime(time.strptime(item, '%Y-%m-%d %H:%M:%S')) for item in time_list]
            frame_index_list = [int(self._fps*(item - video_st_timestamp)) for item in timestamp_list]
            # video_st_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(video_st_timestamp))
        else:
            frame_index_list = []
        return frame_index_list

    def write_frame(self,image_write_path,skip_step=4,time_list=[],forward_time=30):
        """
            视频降采样处理：每隔固定帧(默认为4)抽一帧

            Args：
                image_write_path:图片写入路径
                              eg:/home/image
                skip_step:抽帧间隔,默认为4,当值为1时,不进行降采样
                time_list:不抽帧的时间点
                forward_time:向前取的时间(s),默认为30s
        
        """
        
        if not math.isinf(self._fps) and self._fps != 0: 
            dir_name = image_write_path + "_" + str(self.get_video_time_length) + "_" + str(round(self._fps))
            if not os.path.isdir(dir_name):
                os.makedirs(dir_name)
            cnt = 0
            if skip_step < 1:
                skip_step = 1
            skip_step = int(skip_step)
            video_name = os.path.splitext(os.path.basename(self._videoPath))[0]
            frame_index_list = self.get_frame_index(time_list)
            if frame_index_list:
                pass
                while self._cap.isOpened():
                    ret,frame = self._cap.read()
                    if ret:
                        flag = 0
                        for i in range(len(frame_index_list)):
                            if frame_index_list[i] - self._fps * forward_time <= cnt <= frame_index_list[i]:
                                #frame = cv2.bilateralFilter(frame, 9, 75, 75)
                                cv2.imencode('.png', frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 0])[1].tofile(dir_name + os.path.sep + video_name + '_' + '0' * (5 - len(str(cnt))) + str(cnt) + '.png')
                                flag = 1
                                break
                        if flag == 0 and np.mod(cnt,skip_step) == 0:
                            frame = cv2.bilateralFilter(frame, 9, 75, 75)
                            cv2.imencode('.png', frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 0])[1].tofile(dir_name + os.path.sep + video_name + '_' + '0' * (5 - len(str(cnt))) + str(cnt) + '.png')
                        cnt += 1
                    else:
                        break
            else:
                while self._cap.isOpened():
                    ret,frame = self._cap.read()
                    if ret:
                        if np.mod(cnt,skip_step) == 0:#从1改为0(为了满足skip_step=1的情况),此时起始帧不再是默认的第一帧(skip_step帧为第一帧)
                            frame = cv2.bilateralFilter(frame, 9, 75, 75)
                            cv2.imencode('.png', frame, [int(cv2.IMWRITE_PNG_COMPRESSION),0])[1].tofile(dir_name + os.path.sep + video_name + '_' + '0'*(5-len(str(cnt))) + str(cnt) + '.png')
                        cnt += 1
                    else:
                        #print('获取帧异常:输入视频存在异常')
                        break

            self._cap.release()

    # def get_frame_time(self,fps,st_time,frame_index):
    #     """
    #         获取给定帧图像的时间

    #         Args:
    #             fps:视频帧率
    #             st_time:视频开始时间(格式为:'%Y-%m-%d %H:%M:%S')
    #             frame_index:待转换帧的index

    #         Returns:
    #             转换后的时间(格式为:'%Y-%m-%d %H:%M:%S')

    #     """
    #     if not math.isinf(self._fps):
    #         st_time_timestamp = time.mktime(time.strptime(st_time, '%Y-%m-%d %H:%M:%S'))
    #         frame_timestamp = st_time_timestamp + int(frame_index / fps)
    #         frame_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(frame_timestamp))
    #         return frame_time
