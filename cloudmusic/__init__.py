from .__version__ import __version__
from .cloudmusic import Client, createLoader, getAlbum, getMusic, getPlaylist, getUser, help, search
from .exceptions import (
    APIError,
    CloudMusicError,
    DownloadError,
    IncompleteResultError,
    NotFoundError,
    RequestError,
    ResponseError,
    UnavailableError,
)
from .musicObj import Music
from .userObj import User

__all__ = [
    "Client",
    "Music",
    "User",
    "getMusic",
    "getPlaylist",
    "getAlbum",
    "getUser",
    "search",
    "createLoader",
    "help",
    "__version__",
    "CloudMusicError",
    "APIError",
    "RequestError",
    "ResponseError",
    "NotFoundError",
    "UnavailableError",
    "IncompleteResultError",
    "DownloadError",
]
