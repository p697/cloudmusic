from . import musicObj
from . import setTags
import urllib
import os
import threadpool
import time
import re


def download(dirs, music):
	if len(music.artist) == 1:
		artist = music.artist[0]
	else:
		artist = ""
		for ar in music.artist:
			artist += ar + " "
	name = music.name + " - " + artist + "." + music.type
	name = re.sub(r'[\\/*?:"<>|]', " ", name)

	if not dirs:
		dirs = os.path.join('cloudmusic', 'name')
		defalut_dirs = os.path.join(os.getcwd() , 'cloudmusic')
		isExist = os.path.exists(defalut_dirs)
		if not isExist:
			os.makedirs(defalut_dirs)
	else :
		dirs = os.path.join(dirs, name)

	# 超时重连
	for t in range(5):
		try:
			resp = urllib.request.urlopen(music.url, timeout=5)
			respHtml = resp.read()
			break
		except Exception as e:
			if t == 4:
				print("download failed - " + music.id)
				return None
			print("Error: " + str(e) + " - " + "reconnect time: " + str(t))
		time.sleep(1)


	binfile = open(dirs, "wb")
	binfile.write(respHtml)
	binfile.close()

	try:
		if music.type == "mp3":
			setTags.set_tags_for_mp3(dirs, music.picUrl, artist, music.album, music.name)
		elif music.type == 'm4a':
			setTags.set_tags_for_m4a(dirs, music.picUrl, artist, music.album, music.name)
		elif music.type == 'flac':
			setTags.set_tags_for_flac(dirs, music.picUrl, artist, music.album, music.name)
	except Exception as e:
		print("set tags failed - " + music.id)
		print("Error: " + str(e))
		
	print("dowload finish - " + music.id)

	return os.path.join(os.getcwd(), dirs)


class Downloader():
	def __init__(self, procs, dirs):
		self.data = []
		self.dirs = dirs
		self.procs = procs

	def start(self):
		if not self.data:
			print("data 为空")
			return None
		print("processing...")

		func_var = []
		for music in self.data:
			if not isinstance(music, musicObj.Music):
				print(str(music) + "is not Music object")
				return None
			var = [self.dirs, music]
			func_var.append((var, None))

		pool = threadpool.ThreadPool(self.procs)
		requests = threadpool.makeRequests(download, func_var) 
		[pool.putRequest(req) for req in requests] 
		pool.wait()

		return self.dirs




		# pool = multiprocessing.Pool(self.procs)
		# for music in self.data:
		# 	if not isinstance(music, musicObj.Music):
		# 		print(str(music) + "is not Music object")
		# 		continue
		# 	pool.apply_async(download, (self.dirs, music))
		# pool.close()
		# pool.join()
		# print("finish!")


	 


