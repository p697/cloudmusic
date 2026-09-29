"""Small manual example. Automated tests live in tests/ and never run this file."""

import cloudmusic


if __name__ == "__main__":
    try:
        for music in cloudmusic.search("白日", 5):
            print(music.id, music.name)
    except cloudmusic.CloudMusicError as error:
        print(error)
