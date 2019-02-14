#!/bin/sh
########################################################################################
#
# Program Name: OpenPose Invoking
# File Name: openpose.sh
# Creation Date: Apr 2018
# Programmer: XINWU LIU
# Abstract: This script is used to execute OpenPose
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
#sh_dir=$(dirname $0)
script_dir=`pwd`
sh_dir=./src
config_dir="$sh_dir/../config"
source $sh_dir/common.sh

################################
# Check config files existence
################################
ckFileExist $config_dir/openpose_config.ini

################################
# GPU Check
################################
tot_gpu=`nvidia-smi -L 2>/dev/null |wc -l`
[ $tot_gpu -eq 0 ] && printErr "Error: NO GPU detected!" 1
num_gpu=`cat $config_dir/openpose_config.ini |grep ^GPU_NUM |awk -F "=" '{print $2}'`
if [ ! -z "$num_gpu" ]; then
	isInt "$num_gpu"
	if [ "$num_gpu" -gt $tot_gpu ] || [ "$num_gpu" -le 0 ]; then
		printErr "Error: num_gpu set incorrect!" 2
	fi
	op_num_gpu="--num_gpu $num_gpu"
else
	op_num_gpu=''
fi

gpu_index=`cat $config_dir/openpose_config.ini |grep ^GPU_INDEX |awk -F "=" '{print $2}'`
if [ ! -z $gpu_index ]; then
	isInt "$gpu_index"
	if [ "$gpu_index" -gt "$num_gpu" ] || [ "$gpu_index" -lt 0 ]; then
		printErr "Error: gpu_index set wrong!" 3
	fi
	op_num_gpu_start="--num_gpu_start $gpu_index"
else
	op_num_gpu_start=''
fi

################################
# Hand Flag Check
################################
typeset -l hand_flg
hand_flg=`cat $config_dir/openpose_config.ini |grep ^HAND |awk -F "=" '{print $2}'`
[ "$hand_flg" == "true" ] && hand_flg='--hand' || hand_flg=''

################################
# Face Flag Check
################################
typeset -l face_flg
face_flg=`cat $config_dir/openpose_config.ini |grep ^FACE |awk -F "=" '{print $2}'`
[ "$face_flg" == 'true' ] && face_flg='--face' || face_flg=''

################################
# Scale Check
################################
typeset -i scale
scale=`cat $config_dir/openpose_config.ini |grep ^SCALE |awk -F "=" '{print $2}'`
op_scale="--keypoint_scale $scale"

################################
# Displace Flag Check
################################
typeset -i display_mode
display_mode=`cat $config_dir/openpose_config.ini |grep ^DISPLAY |awk -F "=" '{print $2}'`
display="--display $display_mode"
#[ "$display_flg" == 'true' ] && display_flg=' ' || display_flg=' --no_display '

####################
# Openpose check
####################
op_path=`cat $config_dir/openpose_config.ini |grep ^OPENPOSE_PATH |awk -F "=" '{print $2}'`
[ -z "$op_path" ] && printErr "Error: Openpose PATH is NOT defined!"
ckFileExist "${op_path}build/examples/openpose/openpose.bin"
# [ -z "$frame_path" ] && printErr "Error: frame PATH is NOT defined!"
# video_path=`cat config/openpose_config.ini |grep ^VIDEO_PATH |awk -F "=" '{print $2}'`
# [ -z "$video_path" ] && printErr "Error: video PATH is NOT defined!"


####################
# Call Openpose 
####################
function runOpenPose() {
	local image_dir=$1
	local json_dir=$2
	local img_dir=$3
	ckDirExist $image_dir
	ckDirExist $json_dir
	cd "$op_path" 
	if [ ! -z "$img_dir" ]; then
		./build/examples/openpose/openpose.bin  --image_dir $image_dir --write_json $json_dir --write_images $img_dir ${op_scale} ${op_num_gpu} ${op_num_gpu_start} ${hand_flg} ${face_flg} ${display} --render_pose 1 #--net_resolution "1312x736" --scale_number 4 --scale_gap 0.25
	#echo "./build/examples/openpose/openpose.bin --image_dir $image_dir --write_json $json_dir ${op_scale} ${op_gpu_num} ${hand_flg} ${face_flg} ${display}"
	else
		./build/examples/openpose/openpose.bin  --image_dir $image_dir --write_json $json_dir ${op_scale} ${op_num_gpu} ${op_num_gpu_start} ${hand_flg} ${face_flg} ${display} --render_pose 0 #--net_resolution "1312x736" --scale_number 4 --scale_gap 0.25	
	fi
	cd $script_dir
}
