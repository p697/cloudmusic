"""Cross-platform, streamed and atomic downloads."""

import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from .exceptions import DownloadError, UnavailableError
from .validation import integer


def _filename(music, audio_type):
    extension = str(audio_type or "").lower()
    if not re.fullmatch(r"[a-z0-9]{1,8}", extension):
        raise DownloadError("音频文件类型无效")
    name = "{} - {}".format(music.name, " ".join(music.artist))
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .") or music.id
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        prefix + str(i) for prefix in ("COM", "LPT") for i in range(1, 10)
    }
    if name.split(".")[0].upper() in reserved:
        name = "_" + name
    # Bound UTF-8 bytes as well as character length for macOS/Linux filenames.
    name = name.encode("utf-8")[:180].decode("utf-8", errors="ignore").rstrip(" .")
    return "{}.{}".format(name, extension)


def download(dirs, music, *, audio=None):
    audio = audio if audio is not None else music._playback.get(music.id)
    url = audio.get("url")
    if not url:
        raise UnavailableError("当前账号或地区无法获取音频：{}".format(music.id))
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise DownloadError("音频地址必须是 HTTP 或 HTTPS")
    temporary = None
    options = music._options
    try:
        target_dir = Path(dirs or "cloudmusic").expanduser().resolve()
        target = target_dir / _filename(music, audio.get("type"))
        target_dir.mkdir(parents=True, exist_ok=True)
        # Never forward account cookies to a CDN or to a redirect destination.
        with requests.Session() as session:
            session.proxies.update(options.get("proxies") or {})
            session.headers["User-Agent"] = "Mozilla/5.0"
            with session.get(url, stream=True, timeout=options.get("timeout", (5, 20))) as response:
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()
                if "text/" in content_type or "json" in content_type:
                    raise DownloadError("下载地址返回了错误页面，未覆盖目标文件")
                received = 0
                with tempfile.NamedTemporaryFile(
                    dir=target_dir, prefix=".cloudmusic-", suffix=".part", delete=False
                ) as handle:
                    temporary = Path(handle.name)
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        if chunk:
                            handle.write(chunk)
                            received += len(chunk)
                length = response.headers.get("Content-Length")
                try:
                    expected = int(length) if length is not None else None
                except ValueError:
                    raise DownloadError("音频响应的 Content-Length 无效") from None
                if not received or (
                    length and not response.headers.get("Content-Encoding") and received != expected
                ):
                    raise DownloadError("音频下载不完整，未覆盖目标文件")
        os.replace(temporary, target)
        temporary = None
        return str(target)
    except requests.RequestException as exc:
        raise DownloadError("音频下载失败或超时，未覆盖目标文件") from exc
    except OSError as exc:
        raise DownloadError("音频文件写入失败，请检查目录权限和剩余空间") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class Downloader:
    def __init__(self, procs=2, dirs=""):
        self.data = []
        self.dirs = dirs
        self.procs = integer(procs, "procs", 1)
        self.results = []
        self.errors = {}

    def start(self):
        from .musicObj import Music

        if any(not isinstance(music, Music) for music in self.data):
            raise ValueError("data 中的每一项必须是 Music 对象")
        self.results, self.errors = [], {}
        with ThreadPoolExecutor(max_workers=min(self.procs, 32)) as pool:
            futures = {
                pool.submit(music.download, self.dirs): index
                for index, music in enumerate(self.data)
            }
            completed = {}
            for future in as_completed(futures):
                index = futures[future]
                try:
                    completed[index] = future.result()
                except Exception as exc:
                    self.errors[index] = exc
            self.results = [completed[index] for index in sorted(completed)]
        if self.errors:
            raise DownloadError(
                "{} 首歌曲下载失败；详见 loader.errors，成功文件见 loader.results".format(
                    len(self.errors)
                )
            )
        return str(Path(self.dirs or "cloudmusic").expanduser().resolve())
