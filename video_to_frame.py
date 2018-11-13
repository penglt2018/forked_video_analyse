#coding: utf-8
'''
Program Name: Video to Frame
File Name: video_to_frame
Creation Date: Apr 2018
Programmer: XINWU LIU, BANGFAN LIU
Abstract: This program is for convert videos to frames given a path
Entry Condition: N/A
Exit Condition: N/A
Example: N/A
Program Message: N/A
Remarks: N/A
Amendment Hisotry:
			Version:
			Date:
			Programmer:
			Reason:
'''
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.utf8'
import src.common as common
import traceback

if __name__ == '__main__':
	cfg = common.get_config('config.ini')
	main_logger = common.get_logger('video_to_frame','logconfig.ini', True)
	main_logger.info('function main: video_to_frame.py execute begin')
	# get paths
	video_path=cfg.get('path', 'video_path')
	common.path_check(video_path, main_logger, 'Video path NOT set!', 8)
	main_logger.info('function main: video path {0} get successfully'.format(video_path))
	frame_path=cfg.get('path', 'frame_path')
	common.path_check(frame_path, main_logger, 'Fram path NOT set!', 9)
	main_logger.info('function main: frame path {0} get successfully'.format(frame_path))

	''' find all videos under a path and convert them into frames '''
	import src.video_handler as video_handler
	main_logger.info('function main: src.video_handler import successfully')
	#main_logger.info('Frame extraction start...')
	for root,dirs,files in os.walk(video_path):
		for item in files:
			if common.video_fname_check(item, main_logger):
				print('processing video {0}'.format(root + os.path.sep + item))
				for lkj_file in os.listdir(root):
					if lkj_file.endswith('.csv'):
						main_logger.info('function main: reading lkj data {0}/{1}'.format(root, lkj_file))
						lkj_result = common.get_lkj(root, lkj_file)
						if lkj_result[0] == False:
							main_logger.error(lkj_result[1])
						else:
							lkj_data = lkj_result[1]
							main_logger.info('function main: lkj data read successfully')
							item_dir_name = root.split(os.path.sep)[-2] + os.path.sep + root.split(os.path.sep)[-1] + os.path.sep + os.path.splitext(item)[0]
							main_logger.info('function main: loading video {0}'.format(root + os.path.sep + item))
							item_video = video_handler.VideoHandler(root + os.path.sep + item)
							eve_tm_list = list(lkj_data[lkj_data['事件']=='出站']['时间'])
							try:
								item_video.write_frame(frame_path + item_dir_name, skip_step=4, time_list=eve_tm_list)
							except Exception as e:
								main_logger.error('function main: item_video.write_fame error: {0}'.format(traceback.format_exc()))
	main_logger.info('function main: execute finish')
									
