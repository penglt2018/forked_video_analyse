#coding: utf-8
'''
Program Name: read json file
File Name: json_reader.py
Creation Date: Apr 2018
Programmer: BANGFAN LIU
Abstract: This program is for read json file data given a path
Entry Condition: N/A
Exit Condition: N/A
Example: N/A
Program Message: N/A
Remarks: N/A
Amendment Hisotry:
			Version:V2
			Date:20180813
			Programmer:get_json_file_data
			Reason:(pose point from 18 to 25)
'''
import os
import json
import numpy as np
import random


def get_reference_data(reference_box_in):
    """
        获取参考框的坐标信息

        Args:
            reference_box_in:参考文件对应的路径

        Returns:
            各车次的参考框信息(车型,车号,主副,一二端,x_min, x_max, y_min, y_max)
    """
    with open(reference_box_in, 'r') as fid:
        txt_data = [x.rstrip('\n').split(',') for x in fid.readlines()]
        out_list = [[],]*len(txt_data)
        for i in range(len(txt_data)):
            coordinate_data = txt_data[i][-4:]
            x_min = float(coordinate_data[0])
            x_max = float(coordinate_data[0]) + float(coordinate_data[2])
            y_min = float(coordinate_data[1])
            y_max = float(coordinate_data[1]) + float(coordinate_data[3])
            out_list[i] = txt_data[i][:4]+[x_min, x_max, y_min, y_max]
        return out_list

def get_json_file_data(json_file_in,boxin):
    """
        获取指定json文件的pose_keypoints_2d

        Args:
            json_file_in:json文件对应的路径
            boxin:json文件对应的参考框信息
        Returns:
            参考框内人的pose_keypoints_2d(目前只提取有且仅有一个人的情况/待后续调整优化)
    """
    #print(json_file_in)
    with open(json_file_in) as fid:
        js = json.load(fid)
        if js['people'] != []:
            min_index = 0
            plp_cnt = 0
            plp_list = js['people']
            for i in range(len(plp_list)):
                x = plp_list[i]['pose_keypoints_2d'][3]
                y = plp_list[i]['pose_keypoints_2d'][4]
                c = plp_list[i]['pose_keypoints_2d'][5]
                if x > boxin[0] and x < boxin[1] and y > boxin[2] and y < boxin[3]:
                    min_index = i
                    plp_cnt += 1
            if plp_cnt == 1:
                pos = js['people'][min_index]['pose_keypoints_2d']
                pos = [-1 if p == 0 else p for p in pos]
                data_list = [pos[j] for j in range(len(pos))] + [len(plp_list)]
                return np.array(data_list, dtype=np.float32)
            else:
                return [-2]*76 #(目前只提取有且仅有一个人的情况,多余一个人先返回空list)
        else:
            return [-1]*76 #未监测到人时返回空list，供离岗识别检测使用

def get_driver_coord(pose_keypoints_arr, box_data):
    ''' Function for returning pos keypoints of driver
        Input:
                pose_keypoints_arr: numpy array contains several human coordinates,
                                    return by openpose with shape (_,25,3) 
                box_data:   custom driver coordinates range, used to exclude non-driver person
        return:
                [ pose_keypoints 1-D list , num of people ]
    '''
    num_plp_tot = len(pose_keypoints_arr)   # tot number of person in frame
    
    if num_plp_tot == 0:        # if no person detected
        return [-1] * 75 + [0]  # return [-1,-1,-1,...., 0]
    else:
        min_idex = 0
        plp_cnt = 0             # used for couting how many person in coordiate range box
        for i in range(num_plp_tot):
            x,y,c = pose_keypoints_arr[i][1]    # neck coordinate is used for check
            # neck coordinate in the coordiate range box
            # print(x, box_data)
            if x > box_data[0] and x < box_data[1] and y > box_data[2] and y < box_data[3]:
                min_idex = i
                plp_cnt += 1
        if plp_cnt != 1:                        # when > 1 person stay in range box
            return [-2] * 75 + [num_plp_tot]    # return [-2,-2,-2,....., tot num of person]
        else:
            # flatten (_,25,3) np array to 1d list
            pos = pose_keypoints_arr[min_idex].flatten().tolist()
            return pos + [num_plp_tot]          # return [pose_keypoints 1-D list , num of people]
            

def read_json(json_file_path,reference_box):
    """
        获取指定路径下的所有json文件信息

        Args:
            json_file_path:json路径(改路径必须到最后一层路径)
                        eg: /home/json/
            reference_box:各车次的参考框信息
        Returns:
            指定路径下的json文件名及其对应的pose_keypoints_2d
    """
    #reference_box = get_reference_data(txt_file)
    json_data_all = []
    for root,dirs,files in os.walk(json_file_path):
        dirname = root.split(os.path.sep)[-2]
        dirname_list = dirname.split('_')
        #print(reference_box, dirname_list)
        reference_data = [x for x in reference_box if x[0] == dirname_list[0] and x[1] == dirname_list[1]]
        #print(reference_data)
        for item in files:
            if item.endswith('.json'):
                #print(reference_data)
                json_data = get_json_file_data(root+os.path.sep+item,reference_data[0][-4:])
                if json_data is not None:
                    #print(np.array([item]+list(json_data)).shape)
                    json_data_all.append([item]+list(json_data))
    return json_data_all


def get_cus_json_file_data(json_file_in,boxin):
    """
        获取指定json文件的pose_keypoints_2d

        Args:
            json_file_in:json文件对应的路径
            boxin:json文件对应的参考框信息
        Returns:
            参考框内人的pose_keypoints_2d(目前只提取有且仅有一个人的情况/待后续调整优化)
    """
    with open(json_file_in) as fid:
        js = json.load(fid)
        if js['people'] != []:
            min_index = 0
            plp_cnt = 0
            plp_list = js['people']
            for i in range(len(plp_list)):
                x = plp_list[i]['pose_keypoints_2d'][3]
                y = plp_list[i]['pose_keypoints_2d'][4]
                c = plp_list[i]['pose_keypoints_2d'][5]
                if x > boxin[0] and x < boxin[1] and y > boxin[2] and y < boxin[3]:
                    min_index = i
                    plp_cnt += 1
            if plp_cnt == 1:
                pos = js['people'][min_index]['pose_keypoints_2d']
                x = [ random.random() if pos[x]==0 else pos[x] for x in range(len(pos)) if x%3 == 0 ]
                y = [ random.random() if pos[y]==0 else pos[y] for y in range(len(pos)) if y%3 == 1 ]
                data_list = [[[x[0],x[1],x[8],x[9],x[10]],[x[0],x[1],x[2],x[3],x[4]],[x[0],x[14],x[15],x[16],x[17]],[x[0],x[1],x[5],x[6],x[7]],[x[0],x[1],x[11],x[12],x[13]]],[[y[0],y[1],y[8],y[9],y[10]],[y[0],y[1],y[2],y[3],y[4]],[y[0],y[14],y[15],y[16],y[17]],[y[0],y[1],y[5],y[6],y[7]],[y[0],y[1],y[11],y[12],y[13]]]]
                
                return [data_list]
            else:
                return [[]] #(目前只提取有且仅有一个人的情况,多余一个人先返回空list)
        else:
            return [[]] #未监测到人时返回空list，供离岗识别检测使用


def read_json_cus(json_file_path,reference_box):
    """
        获取指定路径下的所有json文件信息

        Args:
            json_file_path:json路径(改路径必须到最后一层路径)
                        eg: /home/json/
            reference_box:各车次的参考框信息
        Returns:
            指定路径下的json文件名及其对应的pose_keypoints_2d
    """
    #reference_box = get_reference_data(txt_file)
    json_data_all = []
    for root,dirs,files in os.walk(json_file_path):
        dirname = root.split(os.path.sep)[-2]
        dirname_list = dirname.split('_')
        #print(reference_box, dirname_list)
        reference_data = [x for x in reference_box if x[0] == dirname_list[0] and x[1] == dirname_list[1]]
        #print(reference_data)
        for item in files:
            if item.endswith('.json'):
                #print(reference_data)
                json_data = get_cus_json_file_data(root+os.path.sep+item,reference_data[0][-4:])
                if json_data is not None:
                    json_data_all.append([item]+json_data)
    return json_data_all
