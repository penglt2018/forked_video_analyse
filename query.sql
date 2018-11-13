select lkj.JICHEXINGHAO, lkj.JCH, lkj.TRACE, lkj.lkjwholecourse,
	video.FILEPATH, video.STARTTIME, video.ENDTIME, video.CHNO, video.DRIVERNO, video.DRIVER2NO
from lkjvideoadmin.lkjvideoproblem lkj
inner join LAVDR video
on lkj.LKJID = video.LKJID
where lkj.videoneedanaly > lkj.videoanalyzed and lkj.lkjwholecourse is not null 
	and video.ISANALYZED = 0 


select lkj.JICHEXINGHAO, lkj.JCH, lkj.TRACE, lkj.lkjwholecourse,
	video.FILEPATH, video.STARTTIME, video.ENDTIME, video.CHNO, video.DRIVERNO, video.DRIVER2NO
from lkjvideoadmin.lkjvideoproblem lkj
inner join LAVDR video
on (lkj.locotypeno = video.TRAINNO and lkj.TRACE = video.TRAIN 
	and  video.STARTTIME >= lkj.STARTTIME and video.ENDTIME <= lkj.ENDTIME)
where lkj.videoneedanaly > lkj.videoanalyzed and lkj.lkjwholecourse is not null 
	and video.ISANALYZED = 0 





select locotypeno, starttime, endtime,drivernum,drivername,lkjwholecourse 
from lkjvideoadmin.lkjvideoproblem 
where videoneedanaly > videoanalyzed and lkjwholecourse is no null 
and ....(车型车号过滤反面)




select starttime, endtime, trainno, driverno, from
select t.trainno trainno, t.starttime starttime, t.endtime endtime, t.driverno driverno, 
REGEXP_REPLACE(t.filepath,'(.*)//(.*)/(.*)', 'http://\2:8080/media/\3') filepath, 
t.chno channo, t.isanalyzed isanalyzed 
from LAVDR t where where trainno = '"
    + train + "' 
    AND NOT (
    	to_date('" + key.endtime.ToString("yyyy-MM-dd HH:mm:ss") + "', 'YYYY-MM-DD HH24:MI:SS') < STARTTIME 
    	OR to_date('" + key.starttime.ToString("yyyy-MM-dd HH:mm:ss") + "', 'YYYY-MM-DD HH24:MI:SS') >= ENDTIME
    	)";
"
结果表
violate_result.report
记录表
violate_result.video_info
create table violate_result.video_info( 
	lkj_data varchar(255), 
	lkj_st_tm datetime, 
	lkj_ed_tm datetime, 
	video_name varchar(255), 
	video_st_tm datetime, 
	video_ed_tm datetime, 
	train_type varchar(255), 
	train_num varchar(255), 
	port int, 
	shift_num varchar(255),
	driver varchar(255)
);




