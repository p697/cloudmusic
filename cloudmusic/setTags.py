try:
    import mutagen
    mutagen_available = True
except:
    mutagen_available = False

try:   
    from PIL import Image
    pil_available = True
except:
    pil_available = False

import urllib
import io

def resize_the_cover_picture(pic_url):
    data = urllib.request.urlopen(pic_url).read()
    if not pil_available:
        return data
    if len(data)>3e6:
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        img = img.resize((500, 500), Image.ANTIALIAS)
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='JPEG', quality=95)
        return byte_arr.getvalue()
    else:
        return data


def set_tags_for_mp3(mp_path,pic_url='',artist='',album='',music_name=''):
    if not mutagen_available:
        print("mutagen not available, won't set tags")
        return
    
    audio = mutagen.File(mp_path)
    if pic_url:
        audio.tags.add(
            mutagen.id3.APIC(
                encoding=3,  
                mime='image/jpeg',  
                type=3,  
                desc=u'Cover',
                data=resize_the_cover_picture(pic_url)
            )
        )
    if artist:
        audio.tags.add(
            mutagen.id3.TPE1(
                encoding=3,
                text=artist
            )
        )
    if album:
        audio.tags.add(
            mutagen.id3.TALB(
                encoding=3,
                text=album
            )
        )
    if music_name:
        audio.tags.add(
            mutagen.id3.TIT2(
                encoding=3,
                text=music_name
            )
        )
    audio.save()


def set_tags_for_m4a(mp_path,pic_url='',artist='',album='',music_name=''):
    if not mutagen_available:
        print("mutagen not available, won't set tags")
        return

    audio = mutagen.File(mp_path)
    if pic_url:
        audio.tags['covr'] = [
            mutagen.mp4.MP4Cover(
                resize_the_cover_picture(pic_url),
                imageformat=mutagen.mp4.MP4Cover.FORMAT_JPEG
            )
        ]
    if artist:
        audio.tags['\xa9ART'] = artist
    if album:
        audio.tags['\xa9alb'] = album
    if music_name:
        audio.tags['\xa9nam'] = music_name
    audio.save()

def set_tags_for_flac(mp_path,pic_url='',artist='',album='',music_name=''):
    if not mutagen_available:
        print("mutagen not available, won't set tags")
        return

    audio = mutagen.File(mp_path)
    if pic_url:
        pic = mutagen.flac.Picture()
        pic.type = 3
        pic.mime = 'image/jpeg'
        pic.data = resize_the_cover_picture(pic_url)
        audio.add_picture(pic)
    if artist:
        audio.tags['artist'] = artist
    if album:
        audio.tags['album'] = album
    if music_name:
        audio.tags['title'] = music_name
    audio.save()
