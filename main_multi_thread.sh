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
source ./src/openpose.sh
source ./src/common.sh

###############
# Thred Pool
###############
function process_pool() {
        _process_num=$1
        shift
        _func=$1
        shift
        fifo="/tmp/$$.fifo"
        mkfifo $fifo
        exec {FD}<>$fifo
        rm $fifo

        for i in $(seq $_process_num);do
                echo >&$FD
        done
        for arg in $@; do
                read -u $FD
                {
                        $_func `echo $arg |tr '@' ' '`
                        echo >&$FD
                }&
        done
        wait
        exec {FD}>&-
}


#################
# Call Openpose
#################
function callOpenpose() {
    local frame_path="$1"
    echo "Run Openpose..."
    for d in `find $frame_path -type d`;do
        if [ `echo "$d" |awk -F "/" '{print NF}'` -eq 3 ]; then
            dir_name=`echo "$d" |awk -F "/" '{print $2"/"$3}'`
            cmd=(`ls "$d"`)
            #ls "$d"
            #echo "${cmd[*]}"
            for((v=0;v<${#cmd[@]};v++));do
    #       for v in `seq 0 $((${#cmd[@]}-1))`;do
                    #echo ${cmd[v]}
                    json_out_dir="$json_out_path/$dir_name/${cmd[v]}"
                    mkdir -p "$json_out_dir"
                    cmd[v]="${script_dir}/${d}/${cmd[v]}@${script_dir}/${json_out_path}/${dir_name}/${cmd[v]}"
            done
            process_pool 2 'runOpenPose' ${cmd[*]}
            #       echo "${cmd[*]}"
    #       for v in `ls "$d"`;do
    #               json_out_dir="$json_out_path/$dir_name/$v"
    #               mkdir -p "$json_out_dir"
    #               cmd="$script_dir/$d/$v@$json_out_dir"
    #               #echo runOpenPose@"$script_dir/$d/$v"@$json_out_dir
    #       done
    #       wait
    #       echo "$d is finished"
           # dir_name=`echo "$d" |awk -F "/" '{print $3"/"$4}'`
            #echo "$dir_name"
           # camera_direction=`echo "$d" |awk -F "/" '{print $2}'`
           # json_out_dir="$json_out_path/$camera_direction/$dir_name"
           # mkdir -p "$json_out_dir"
           # echo "$json_out_dir"
           # if [ ! -z "$image_output_path" ]; then
           #         image_out_dir="$image_output_path/$camera_direction/$dir_name"
           #         mkdir -p "$image_out_dir"
           #         runOpenPose "$script_dir/$d" "$script_dir/$json_out_dir" "$script_dir/$image_out_dir"
           # #echo "run openpose"
           # else    
           #         runOpenPose "$script_dir/$d" "$script_dir/$json_out_dir"
           # fi
        fi
    done
}


#################################
# Common Check
#################################
./check.sh

#################################
# Openpose Path Check
#################################
frame_path=`cat ./config.ini |grep "^frame_path" |awk -F "=" '{print $2}'`
json_out_path=`cat ./config.ini |grep "^json_out_path" |awk -F "=" '{print $2}'`
image_output_path=`cat ./config.ini |grep "^image_output" |awk -F "=" '{print $2}'`
ckDirExist $frame_path
ckDirExist $json_out_path
[ ! -z "$image_output_path" ] && ckDirExist $image_output_path

#################################
# Download videos
#################################
st_time=`date +%s`
echo "Download videos..."
#python3 ./get_video.py
rtCheck $? 'python3 ./get_video.py'
download_time=`date +%s`
echo "Video download time: $((download_time-st_time))"

#################################
# Convert Video to Frame
#################################
echo "Video to Frame..."
#python3 ./video_to_frame.py
rtCheck $? 'python3 ./video_to_frame.py'
#frm_time=`date +'%Y-%m-%d %H:%M:%S'`
frm_time=`date +%s`
echo "Frame time: $((frm_time-download_time))"

#################################
# Run Yolo
#################################
echo "Run yolo...."
#python3 ./run_yolo.py && md_time=`date +%s` && echo "yolo model time: $((md_time-frm_time))" &

################################
# Generate Pos Json by Openpose
################################
callOpenpose $frame_path 

wait
#op_time=`date +'%Y-%m-%d %H:%M:%S'`
op_time=`date +%s`
echo "Openpose time: $((op_time-frm_time))"
cd $script_dir

# #################################
# # Run Model
# #################################
echo "Run model...."
#python3 ./run_model.py && md_time=`date +%s` && echo "wrong head model time: $((md_time-op_time))"

#./clean.sh

