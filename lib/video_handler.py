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
        self._frameNum = self._cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self._width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._frames = []
        
    @property
    def get_video_fps(self):
        return self._fps
    @property
    def get_video_frame_num(self):
        return self._frameNum
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
        return int(round(self._frameNum / self._fps))

    def set_video_frames(self, skip_step=4, time_list=[], forward_time=30, bilateralFlg=False):
        self._frames = self.frame_extract(skip_step, time_list, forward_time, bilateralFlg)
    
    def get_video_frames(self):
        return self._frames

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

    def frame_extract(self,skip_step=4,time_list=[],forward_time=30,bilateralFlg=False):
        cnt = 0
        frame_data = []
        if skip_step < 1:
            skip_step = 1
        skip_step = int(skip_step)
        if not math.isinf(self._fps) and self._fps != 0: #fps有效
            frame_index_list = self.get_frame_index(time_list)
            while self._cap.isOpened():
                ret, frame = self._cap.read()
                if ret:
                    flag = 0 #用于判断是否落在不抽帧的时间段
                    for i in range(len(frame_index_list)):
                        if frame_index_list[i] - self._fps * forward_time <= cnt <= frame_index_list[i]:
                            if bilateralFlg:
                                frame = cv2.bilateralFilter(frame, 9, 75, 75)
                            frame_data.append([frame,cnt])
                            flag = 1
                            break
                    if flag == 0 and np.mod(cnt,skip_step) == 0: #按常规情况抽帧
                        if bilateralFlg:
                            frame = cv2.bilateralFilter(frame, 9, 75, 75)
                        frame_data.append([frame, cnt])
                    cnt += 1
                else:
                    break
            self._cap.release()
        else:
            raise SystemError('{0} fps error !'.format(self._videoPath))
        return frame_data

    def write_frames(self, path, video_name, frame_st_idx, frame_ed_idx):
        for pix_mat, frame_idx in self._frames:
            if frame_idx >= frame_st_idx and frame_idx <= frame_ed_idx:
                write_filename = path + os.path.sep + video_name + '_' + '0' * (5 - len(str(frame_idx))) + str(frame_idx) + '.png'
                cv2.imencode('.png', pix_mat, [int(cv2.IMWRITE_PNG_COMPRESSION), 0])[1].tofile(write_filename)


# filepath = r'C:\Users\08\Desktop\1109\HXD1C6095_济南若临_02_一端司机室_20181109_114500.mp4'
# video_handler = VideoHandler(filepath)
# # frame_data = video_handler.get_frames(skip_step=4,time_list=['2018-11-09 11:16:00','2018-11-09 11:17:00','2018-11-09 11:18:00'])
# frame_data = video_handler.get_frames()
