#!/bin/bash
########################################################################################
#
# Program Name: Checking Program
# File Name: check.sh
# Creation Date: Apr 2018
# Programmer: XINWU LIU, BANGFAN LIU
# Abstract: This script is used for checking config files existence
# Entry Condition: N/A
# Exit Condition: N/A
# Example: N/A
# Program Message: N/A
# Remarks: N/A
# Amendment Hisotry:
#			Version:
#			Date:
#			Programmer:
#			Reason:
#
########################################################################################

sh_name=$(basename $0)
script_dir=`pwd`
source ./src/common.sh
echo 'Normal check begin'
#################################
# Dir Check
#################################
ckDirExist ./config
ckDirExist ./frame/back
ckDirExist ./frame/left_back
ckDirExist ./frame/left
ckDirExist ./frame/right_back
ckDirExist ./frame/right
ckDirExist ./image_render/back
ckDirExist ./image_render/left_back
ckDirExist ./image_render/left
ckDirExist ./image_render/right_back
ckDirExist ./image_render/right
ckDirExist ./json_output/back
ckDirExist ./json_output/left_back
ckDirExist ./json_output/left
ckDirExist ./json_output/right_back
ckDirExist ./json_output/right
ckDirExist ./model/back
ckDirExist ./model/left_back
ckDirExist ./model/left
ckDirExist ./model/right_back
ckDirExist ./model/right
ckDirExist ./video/back
ckDirExist ./video/left_back
ckDirExist ./video/left
ckDirExist ./video/right_back
ckDirExist ./video/right
ckDirExist ./log

#################################
# Config File Check
#################################
ckFileExist ./config.ini
ckFileExist ./logconfig.ini
ckFileExist ./config/openpose_config.ini
ckFileExist ./config/reference_box.ini

#################################
# reference_box Format Check
#################################
rt=`awk -F "," '{print NF}' ./config/reference_box.ini |sort |uniq`
[ `echo "$rt" |wc -l` -ne 1 ] && echo "$rt" && printErr "Error: The number of columns of reference_box is NOT uniq!" 30
[ "$rt" -ne 8 ] && echo "$rt" && printErr "Error: The number of columns of reference_box is NOT equal to 8" 31
train_num_len=`awk -F "," '{print length($2)}' ./config/reference_box.ini |sort |uniq`
#[ `echo "$train_num_len" |wc -l` -ne 1 ] && echo "$train_num_len" && printErr "Error: train_num length in reference_box is NOT uniq!" 32
#[ "$train_num_len" -ne 4 ] && [ "$train_num_len" -ne 5 ] && echo "$train_num_len" && printErr "Error: train_num length in reference_box is WRONG" 33
driver=`awk -F "," '{print length($3)}' ./config/reference_box.ini |sort |uniq`
for i in $driver;do
	[ $i -ne 1 ] && [ $i -ne 2 ] && echo "$i" && printErr "Error: driver number in reference_box is Wrong!" 34
done
term=`awk -F "," '{print length($4)}' ./config/reference_box.ini |sort |uniq`
for i in $term;do
	[ $i -ne 1 ] && [ $i -ne 2 ] && echo "$i" && printErr "Error: driver room number in reference_box is Wrong!" 35
done
box_rt=`awk -F "," '{for(i=5;i<=8;i++) if($i>=1) print $0}' ./config/reference_box.ini`
[ ! -z "$box_rt" ] && echo "$box_rt" && printErr "Error: box setting in reference_box is Wrong!"


#################################
# Shell Script Check
#################################
ckFileExist ./main.sh
ckFileExist ./src/common.sh
ckFileExist ./src/openpose.sh

#################################
# Python Script Check
#################################
ckFileExist ./run_model.py
ckFileExist ./video_to_frame.py
ckFileExist ./src/common.py
ckFileExist ./src/dbHandler.py
ckFileExist ./src/json_reader.py
ckFileExist ./src/time_check.py
ckFileExist ./src/video_handler.py


#source ./src/openpose.sh
echo 'Normal check finish'
