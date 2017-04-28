from __future__ import absolute_import, unicode_literals
import os
from media.models import *
from media_server.settings import MEDIA_user
from django.http import HttpResponse
from django.core.mail import send_mail
from celery import shared_task
# from celery.task.schedules import crontab
# from celery.decorators import periodic_task
#
# @periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
# def test():
#     print "Test Task"


@shared_task
def handleFileUploadAsync(update, m, file_type, video_types):
	filename = m.file.name
	if not m.is_360:
		if video_types[file_type] == 'wmv':
			os.system(
				"ffmpeg -i '" + MEDIA_user + filename + "' -strict experimental -vcodec libx264 -profile:v baseline '" + MEDIA_user + filename.replace(video_types[file_type],'mp4')+"'"
			)
			m.file.name = m.file.name.replace(video_types[file_type], 'mp4')
			m.save()
			os.remove(m.file.path.replace('mp4', 'wmv'))
		elif file_type in video_types.keys():
			os.system(
			 "ffmpeg -i '" + MEDIA_user + filename + "' -vcodec libx264 -profile:v baseline -s 672x576 '" + MEDIA_user + filename.replace(video_types[file_type],'mp4')+"' -analyzeduration 2147483647 -probesize 2147483647"
			)
			
			m.file.name = m.file.name.replace(video_types[file_type], 'mp4')
			m.save()
			os.system(
				"qtfaststart '" + MEDIA_user + filename + "' '" + MEDIA_user + filename.replace(video_types[file_type],'mp4')+"'"
			)
			if video_types[file_type] != 'mp4':
				os.remove(m.file.path.replace('mp4', video_types[file_type]))
	#create thumbnail
	filename = m.file.name
	os.system(
		"ffmpeg -itsoffset -4  -i '" + MEDIA_user + filename + "' -vcodec mjpeg -vframes 1 -an -f rawvideo -s 320x240 '" + MEDIA_user + filename + ".jpg'"
	)

	#get the running time and store it
	duration = os.popen(
		'ffmpeg -i "'+MEDIA_user+ filename + '" 2>&1 | grep Duration | cut -d " " -f 4 | sed s/,//').read()
	duration = duration.replace("\n", "")
	duration = duration.rsplit('.')
	duration = duration[0].rsplit(':')
	if duration[0] == '00':
		del duration[0]
		duration = ':'.join(duration)
		m.duration = duration
		m.save()
	# uploader = str(User.objects.get(username=m.user))
	# send_mail('Your video,  {{ m.name }}, has been uploaded!', 'This message confirms that your video, {{ m.name }}, was successfully uploaded to Mycompany TV.', 'it@Mycompany.com', [uploader,])
