"""Errors callers can handle without depending on an upstream response shape."""


class CloudMusicError(Exception):
    """Base class for service and download errors."""


class RequestError(CloudMusicError):
    def __init__(self, message, status_code=None):
        self.status_code = status_code
        super().__init__(message)


class APIError(CloudMusicError):
    def __init__(self, code, message=""):
        self.code = code
        self.message = message or "网易云接口拒绝了请求"
        super().__init__("{} (code={})".format(self.message, code))


class ResponseError(CloudMusicError):
    """The service returned an unexpected or malformed response."""


class NotFoundError(CloudMusicError):
    def __init__(self, ids):
        self.ids = list(ids)
        super().__init__("未找到歌曲或用户：{}".format(", ".join(map(str, self.ids))))


class UnavailableError(CloudMusicError):
    """An audio file is unavailable for the current account or region."""


class IncompleteResultError(CloudMusicError):
    def __init__(self, message, partial_result, expected_count=None):
        self.partial_result = partial_result
        self.expected_count = expected_count
        self.actual_count = len(partial_result)
        super().__init__(message)


class DownloadError(CloudMusicError):
    pass
