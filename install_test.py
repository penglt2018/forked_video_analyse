from abc import ABCMeta,abstractmethod,abstractproperty
import sys
sys.path.append('/home/crrc/AlexAB/darknet/python')
sys.path.append('/home/crrc/openpose/build/python/openpose')
from configparser import ConfigParser
from model.back.pos_recog_model import wrong_head as wrong_head_back
from model.right_back.pos_recog_model import arm_detect as arm_detect_right_back
from model.right_back.pos_recog_model import get_angle
from model.right_back.pos_recog_model import nap_detect as nap_detect_right_back
from model.right_back.pos_recog_model import wrong_head as wrong_head_right_back
from model.right.pos_recog_model import wrong_head as wrong_head_right
from tensorflow.python.framework import dtypes
import cv2
import cx_Oracle
import darknet as dn
import datetime
import ftplib
import json
import lib.common as common
import lib.coord_handler as coord_handler
import lib.ftp_client as ftp_client
import lib.lkj_lib as LKJLIB
import lib.video_handler as video_handler
import logging
import logging.config
import math
import multiprocessing
import numpy as np
import openpose as op
import openpose_handler 
import os
import pandas as pd
import pymysql
import random
import tensorflow as tf
import threading
import time
import traceback
import yolo
import yolo_handler
