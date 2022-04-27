from . import musicObj
import os
import urllib
import threadpool
import time
import sys



def download(dirs, music):
	if len(music.artist) == 1:
		artist = music.artist[0]
	else:
		artist = ""
		for ar in music.artist:
			artist += ar + " "
	music.name = music.name.replace("/", "&")
	music.name = music.name.replace("*", "&")
	if not artist is None:
		artist = artist.replace("/", "&")
		artist = artist.replace("*", "&")
	name = music.name + " - " + artist + "." + music.type

	if not dirs:

		if sys.platform == "darwin":
			path1 = "cloudmusic/"
			path2 = "/cloudmusic"
			path3 = "/"
		else :
			path1 = "cloudmusic\\"
			path2 = "\\cloudmusic"
			path3 = "\\"

		dirs = path1 + name
		defalut_dirs = str(os.getcwd()) + path2
		isExist = os.path.exists(defalut_dirs)
		if not isExist:
			os.makedirs(defalut_dirs)
	else :
		dirs += path3 + name

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

	print("dowload finish - " + music.id)

	return str(os.getcwd()) + dirs


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


	 


