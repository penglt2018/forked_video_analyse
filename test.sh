#!/bin/bash

echo $(dirname $0)

json_out_path='json_output'
script_dir=`pwd`
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
			$_func $arg |tr '@' ' '
			echo >&$FD
		}&
	done
	
	wait

	exec {FD}>&-
}


function test() {
	echo $1
	sleep 3
	return 0
}

	


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
		#	for v in `seq 0 $((${#cmd[@]}-1))`;do
				#echo ${cmd[v]}
				cmd[v]="${script_dir}/${d}/${cmd[v]}@${script_dir}/${json_out_path}/${dir_name}/${cmd[v]}"
			done
			process_pool 3 'test' ${cmd[*]}
			#	echo "${cmd[*]}"
		#	for v in `ls "$d"`;do
		#		json_out_dir="$json_out_path/$dir_name/$v"
		#		mkdir -p "$json_out_dir"
		#		cmd="$script_dir/$d/$v@$json_out_dir"
		#		#echo runOpenPose@"$script_dir/$d/$v"@$json_out_dir
		#	done
		#	wait
		#	echo "$d is finished"
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
callOpenpose frame/
#test 1 2 3 4 5 6 7
#process_pool 3 'test' 1@2 3@4 5@6 7@8
