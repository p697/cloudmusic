import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import cloudmusic
from cloudmusic.download import _filename, download
from cloudmusic.exceptions import DownloadError, UnavailableError


@pytest.fixture
def server():
    seen = []
    content = b"audio-data" * 20000

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(dict(self.headers))
            if self.path == "/error":
                self.send_error(503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html" if self.path == "/html" else "audio/mpeg")
            payload = b"" if self.path == "/empty" else content
            self.send_header(
                "Content-Length", str(len(payload) + (1 if self.path == "/short" else 0))
            )
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=httpd.serve_forever, daemon=True)
    worker.start()
    try:
        yield "http://127.0.0.1:{}".format(httpd.server_port), content, seen
    finally:
        httpd.shutdown()
        httpd.server_close()
        worker.join(timeout=5)


def music(url):
    return cloudmusic.Music(
        1,
        url,
        "higher",
        10,
        "mp3",
        {
            "name": "歌/曲:*?",
            "artist": ["歌手"],
            "album": "专辑",
        },
        options={"cookie": {"MUSIC_U": "do-not-forward"}, "timeout": (1, 2)},
    )


def test_streamed_download_to_custom_directory_and_no_cookie(server, tmp_path):
    base, expected, seen = server
    destination = tmp_path / "new" / "directory"
    value = music(base + "/ok")
    result = Path(value.download(destination))
    assert result.is_absolute() and result.parent == destination
    assert result.read_bytes() == expected
    assert result.name == "歌_曲___ - 歌手.mp3"
    assert value.name == "歌/曲:*?"
    assert not list(destination.glob("*.part"))
    assert "Cookie" not in seen[0]


def test_default_directory(server, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = Path(music(server[0] + "/ok").download())
    assert result.parent == tmp_path / "cloudmusic"


@pytest.mark.parametrize("path", ["/error", "/html", "/empty", "/short"])
def test_failed_download_does_not_replace_existing_file(server, tmp_path, path):
    value = music(server[0] + path)
    target = tmp_path / _filename(value, "mp3")
    target.write_bytes(b"keep existing")
    with pytest.raises(DownloadError):
        value.download(tmp_path)
    assert target.read_bytes() == b"keep existing"
    assert sorted(p.name for p in tmp_path.iterdir()) == [target.name]


def test_long_unicode_and_reserved_filenames():
    value = music("https://example.invalid")
    value.name = "长" * 500
    assert len(_filename(value, "mp3").encode()) <= 184
    value.name = "CON.txt"
    assert _filename(value, "mp3").startswith("_")
    with pytest.raises(DownloadError):
        _filename(value, "../mp3")
    value.name = ".."
    value.artist = []
    assert "/" not in _filename(value, "mp3")


def test_invalid_audio_address(tmp_path):
    with pytest.raises(UnavailableError):
        download(tmp_path, music(None))
    with pytest.raises(DownloadError):
        download(tmp_path, music("file:///etc/passwd"))


def test_batch_loader_success_and_failure(monkeypatch, tmp_path):
    loader = cloudmusic.createLoader(2, tmp_path)
    loader.data = [music("a"), music("b")]
    monkeypatch.setattr(cloudmusic.Music, "download", lambda self, dirs: str(Path(dirs) / self.id))
    assert loader.start() == str(tmp_path)
    assert len(loader.results) == 2
    loader.data[1].id = "2"

    def fail_one(self, dirs):
        if self.id == "2":
            raise UnavailableError("unavailable")
        return "saved"

    monkeypatch.setattr(cloudmusic.Music, "download", fail_one)
    with pytest.raises(DownloadError):
        loader.start()
    assert loader.results == ["saved"] and 1 in loader.errors
    loader.data = ["not music"]
    with pytest.raises(ValueError):
        loader.start()
    loader.data = []
    assert loader.start() == str(tmp_path)
    assert not loader.results and not loader.errors
    with pytest.raises(ValueError):
        cloudmusic.createLoader(0)
