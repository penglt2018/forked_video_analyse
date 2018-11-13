#!/bin/bash



#save_info=`mysql -uroot -p123456 -e "select video_filename,start_frame,end_frame from violate_result.report where start_frame is not null;" 2>/dev/null |sed '1d'`
save_info=`cat tmp/pict.sav`
for i in `echo "$save_info"`;do
	fname=`echo "$i" |awk -F "," '{print $1}'`
	start_frame=`echo "$i" |awk -F "," '{print $2}'`
	end_frame=`echo "$i" |awk -F "," '{print $3}'`
	dir=`find frame |grep "$fname" |head -1`
	eval ls $dir/$fname'_'{$start_frame..$end_frame}'.png' 2>/dev/null |xargs -i cp {} ./store
done

mysql -uroot -p123456 -e "truncate table violate_result.video_info"

rm -rf frame/back/*
rm -rf frame/left/*
rm -rf frame/left_back/*
rm -rf frame/right/*
rm -rf frame/right_back/*
#mv frame/right_back/* frame_bk/

rm -rf json_output/back/*
rm -rf json_output/left/*
rm -rf json_output/left_back/*
rm -rf json_output/right/*
rm -rf json_output/right_back/*
#mv json_output/right_back/* json_bk

rm -rf video/back/*
rm -rf video/left/*
rm -rf video/left_back/*
rm -rf video/right/*
rm -rf video/right_back/*
#mv video/right_back/* video_bk/

rm -rf tmp/*
