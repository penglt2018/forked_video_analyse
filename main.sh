#!/bin/bash
########################################################################################
#
# Program Name: Main Program
# File Name: main.sh
# Creation Date: Apr 2018
# Programmer: XINWU LIU
# Abstract: This script is used for generating pos_keypoints json files given directories
#			with a series of pictures
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
#st_time=`date +'%Y-%m-%d %H:%M:%S'`
script_dir=`pwd`
#source ./src/openpose.sh
#source ./src/common.sh

echo 'Program Begin'

# ####################
# # clean
# ####################
# #echo 'clean.sh execute begin'
# #./clean.sh

# #####################
# # OpenPose Function
# #####################
# function callOpenpose() {
# 	local frame_path="$1"
# 	for d in `find $frame_path -type d`;do
# 		if [ `echo "$d" |awk -F "/" '{print NF}'` -eq 4 ]; then
# 			dir_name=`echo "$d" |awk -F "/" '{print $3"/"$4}'`
# 			camera_direction=`echo "$d" |awk -F "/" '{print $2}'`
# 			json_out_dir="$json_out_path/$camera_direction/$dir_name"
# 			mkdir -p "$json_out_dir"
# 			echo "$json_out_dir"
# 			if [ ! -z "$image_output_path" ]; then
# 				image_out_dir="$image_output_path/$camera_direction/$dir_name"
# 				mkdir -p "$image_out_dir"
# 				runOpenPose "$script_dir/$d" "$script_dir/$json_out_dir" "$script_dir/$image_out_dir"
# 				#echo "run openpose"
# 			else
# 				runOpenPose "$script_dir/$d" "$script_dir/$json_out_dir"
# 			fi
# 		fi
# 	done
# }

# #################################
# # Common Check
# #################################
# ./check.sh

# #################################
# # Openpose Path Check
# #################################
# echo 'Openpose check begin'
# frame_path=`cat ./config.ini |grep "^frame_path" |awk -F "=" '{print $2}'`
# json_out_path=`cat ./config.ini |grep "^json_out_path" |awk -F "=" '{print $2}'`
# image_output_path=`cat ./config.ini |grep "^image_output" |awk -F "=" '{print $2}'`
# ckDirExist $frame_path
# ckDirExist $json_out_path
# [ ! -z "$image_output_path" ] && ckDirExist $image_output_path
# echo 'Openpose check finish'

#################################
# Download videos
#################################
echo "Download videos begin"
st_time=`date +%s`
python3 ./get_video.py
[ $? -ne 0 ] && echo 'Error: get_video.py execute failed!'
#rtCheck $? 'python3 ./get_video.py'
download_time=`date +%s`
echo "Download videos finish with time: $((download_time-st_time))"

# #################################
# # Convert Video to Frame
# #################################
# echo "Video to frame begin"
# python3 ./video_to_frame.py
# [ $? -ne 0 ] && echo 'Error: video_to_frame.py execute failed!'
# #rtCheck $? 'python3 ./video_to_frame.py'
# #frm_time=`date +'%Y-%m-%d %H:%M:%S'`
# frm_time=`date +%s`
# echo "Video to frame finish with time: $((frm_time-download_time))"

#################################
# Run Yolo
#################################
echo 'Yolo execute begin'
python3 ./run_yolo.py && md_time=`date +%s` && echo "yolo finish with time: $((md_time-frm_time))" &
#python3 ./run_yolo_cellphone.py && md_time=`date +%s` && echo "yolo finish with time: $((md_time-frm_time))" &

################################
# Generate Pos Json by Openpose
################################
echo "Openpose execute begin"
#callOpenpose $frame_path #&
python3 ./run_openpose.py && md_time=`date +%s` && echo "yolo finish with time: $((md_time-frm_time))" &

wait
#op_time=`date +'%Y-%m-%d %H:%M:%S'`
op_time=`date +%s`
echo "Openpose finish with time: $((op_time-frm_time))"
cd $script_dir

# # #################################
# # # Run Model
# # #################################
# echo "Custom model execute begin"
# python3 ./run_model.py
# if [ $? -eq 0 ]; then
# 	md_time=`date +%s` && echo "Custom model finish with time: $((md_time-op_time))"
# else
# 	echo 'Error: Custom model execute failed!'
# fi

echo 'clean.sh execute begin'
./clean.sh
[ $? -ne 0 ] && echo 'Error: clean.sh execute failed!' || echo 'clean.sh finish successfully'

echo 'Program finish'

