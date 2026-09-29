# cloudmusic

一个轻量的网易云音乐 Python 客户端：查询歌曲、专辑、歌单、歌词、评论和用户公开资料，并下载当前账号有权访问的完整音频。

支持 Python 3.10–3.14。保留 `getMusic()`、`getPlaylist()`、`search()` 等原有调用方式。

> 仓库维护版本为 **0.2.0**。在发布到 PyPI 之前，`pip install cloudmusic` 仍可能安装旧的 0.1.1。请按下面的源码安装方式使用当前版本。历史 HTML/PDF 文档对应 0.1.1，当前接口以本 README 为准。

## 安装

```bash
git clone https://github.com/p697/cloudmusic.git
cd cloudmusic
python -m pip install .
```

运行时仅依赖 `requests` 和 `pycryptodomex`，不再要求 `lxml` 或 `threadpool`。

## 快速开始

```python
import cloudmusic

music = cloudmusic.getMusic(1347630432)
print(music.name, music.artist, music.album)
print(music.getLyrics())  # [原文歌词, 翻译歌词]；缺失项为空字符串

results = cloudmusic.search("白日", number=5)
for song in results:
    print(song.id, song.name)

playlist = cloudmusic.getPlaylist(310729011)
print(len(playlist))
```

歌曲信息与音频权限相互独立。获取歌曲名称、专辑、歌词或评论不需要先获取播放地址。访问 `music.url`、`size`、`type`、`level` 或 `freeTrialInfo` 时，才获取音频信息；同一批歌曲共享批量请求。音频信息缓存 60 秒，以减少重复请求和过期链接。

```python
try:
    print(music.url)    # 没有播放权限时可能为 None；接口风控会抛出 APIError
    print(music.level)  # 服务实际返回的品质，可能低于请求品质
    path = music.download(dirs="./downloads")
    print(path)        # 已保存文件的绝对路径
except cloudmusic.CloudMusicError as error:
    print(error)
```

下载采用流式写入和临时文件替换。只有成功完成下载才覆盖同名目标文件；失败会保留已有文件并清理临时文件。仅有试听音频时抛出 `UnavailableError`，不会把试听片段当成完整歌曲保存。

## 配置会话

默认匿名访问。需要账号权限时，可以显式传入自己的 cookie；库不包含任何内置登录凭据，不自动读取浏览器或环境中的凭据。

```python
import os
import cloudmusic

with cloudmusic.Client(
    cookie=os.environ.get("NETEASE_COOKIE"),
    timeout=(5, 20),  # 连接超时、单次读取超时，单位秒
    level="higher",
    # proxies={"https": "http://127.0.0.1:7890"},
) as client:
    music = client.getMusic(1347630432)
    songs = client.search("白日", 5)

# 返回的 Music/User 对象保留配置；关闭 Client 后仍可按需调用。
print(music.getLyrics())
```

`cookie` 支持 cookie 字符串或字典。`Client` 复用查询连接并保留服务端更新的会话 cookie，使用完毕后应调用 `close()` 或用 `with` 管理。网络错误和风控错误不会自动反复重试；同批音频遇到验证/登录限制后，在 60 秒内复用该错误，避免批量任务重复触发限制。音频 CDN 请求不携带网易云登录 cookie。

该项目依赖网易云的非官方接口。接口返回内容受登录状态、隐私设置、地区和音频权限限制；升级客户端不能保证获取所有歌曲、无限评论或指定音质。不要将 cookie 提交到 Git 或输出到公开日志。

## API

以下函数也可以通过 `Client` 调用：

| 函数 | 返回值 |
| --- | --- |
| `getMusic(id)` | 一个 `Music` 对象 |
| `getMusic([id, ...])` | `Music` 列表，保留输入顺序和重复 ID；单元素列表仍返回列表；空列表返回 `[]` |
| `getPlaylist(id)` | 按歌单顺序排列的 `Music` 列表 |
| `getAlbum(id)` | 按专辑顺序排列的 `Music` 列表 |
| `search(content, number=5)` | 最多 `number` 个不重复的搜索结果；支持分页；无结果返回 `[]` |
| `getUser(id)` | `User` 对象 |

ID 支持正整数或整数字符串。无效参数抛出 `ValueError`；歌曲 ID 不存在时抛出 `NotFoundError`，其 `ids` 字段包含缺失 ID。歌单返回数量与服务报告的总数不一致时抛出 `IncompleteResultError`，不会静默当作完整歌单。

```python
try:
    songs = cloudmusic.getPlaylist(310729011)
except cloudmusic.IncompleteResultError as error:
    print(error.actual_count, error.expected_count)
    songs = error.partial_result  # 调用方明确选择是否使用已获取部分
```

### Music

元数据属性：`id`（字符串）、`name`、`artist`、`artistId`、`album`、`albumId`、`picUrl`。

按需获取的音频属性：`url`、`size`、`type`、`level`、`freeTrialInfo`。

| 方法 | 行为 |
| --- | --- |
| `download(dirs="", level=None)` | 默认保存到当前目录的 `cloudmusic` 文件夹；`level=None` 沿用创建对象时的请求品质（默认 `higher`） |
| `getLyrics()` | 返回 `[原文, 翻译]`，缺失项为空字符串 |
| `getHotComments(number=15)` | 最多 15 条热评 |
| `getComments(number)` | 按时间从新到旧，使用游标分页；不足时返回可获取的数量 |
| `getCommentsCount()` | 服务报告的评论总数 |

品质参数保留 `standard`、`higher`、`exhigh`、`lossless`。实际品质由接口和账号权限决定。指定音质不会丢失下载目录，文件扩展名取服务实际返回值。

评论字段：`commentId`、`likeCount`、`content`、`time`、`userId`、`nickName`、`avatarUrl`、`vipType`、`userType`。用户已注销或字段缺失时，昵称和头像可以为空。若服务表示还有数据但分页无法继续，抛出带 `partial_result` 的 `IncompleteResultError`，避免无限循环或重复结果。

### User

属性：`id`、`level`、`listenSongs`、`createTime`、`nickname`（也支持 `nickName`）、`avatarUrl`、`city`、`province`、`vipType`、`birthday`、`signature`、`fans`、`follows`、`eventCount`、`playlistCount`、`sex`。部分资料可能因隐私设置缺失。

- `getPlaylist()`：分页获取可访问的用户歌单，返回信息字典列表。字段包括 `id`、`name`、`creatorId`、`playCount`、`createTime`、`coverImgUrl`、`updateTime`、`tags`。
- `getRecord(recordType=0)`：0 为所有时间，正整数为最近一周；返回 `{"score": ..., "music": Music}` 列表，只请求所需周期。

### 批量下载

```python
loader = cloudmusic.createLoader(procs=2, dirs="./downloads")
loader.data = cloudmusic.getPlaylist(310729011)
try:
    loader.start()
except cloudmusic.DownloadError:
    print(loader.errors)  # 失败项：以 data 中的索引为键
print(loader.results)     # 成功保存的绝对路径，按输入顺序排列
```

最多同时使用 32 个工作线程。文件名会处理跨平台非法字符和过长名称；同名歌曲仍会覆盖同一目标文件，请选择适当的目录管理下载结果。

### 错误类型

均继承 `CloudMusicError`，无效调用参数使用标准 `ValueError`。

| 类型 | 含义 |
| --- | --- |
| `RequestError` | 网络/超时/非 200 HTTP 响应；`status_code` 在 HTTP 失败时可用 |
| `APIError` | 网易云业务错误；保留 `code` 和 `message`，包括风控、验证或登录要求 |
| `ResponseError` | JSON 或响应结构异常 |
| `NotFoundError` | 指定歌曲不存在，保留 `ids` |
| `UnavailableError` | 没有完整音频可供下载 |
| `IncompleteResultError` | 歌单不完整或分页停止前进；保留 `partial_result` |
| `DownloadError` | 文件下载未完整完成或批量下载部分失败 |

## 测试与开发

```bash
python -m pip install -e '.[test]'
python -m pytest --cov=cloudmusic --cov-branch --cov-report=term-missing
python -m ruff check cloudmusic tests
python -m build
```

默认测试禁止外部联网，并通过本地 HTTP 服务验证流式下载、错误响应、中断、临时文件清理和已有文件保护。CI 在 Linux、macOS、Windows 上运行 Python 3.10、3.12、3.14 的测试，以及独立 wheel 安装检查。

真实接口测试显式启用，依赖当前网络环境和服务状态，不参与必过 CI：

```bash
python -m pytest --live -m live -v
```

真实测试默认匿名，不修改账号内容，也不批量下载音频。远端拒绝会表现为测试失败，不会被记为成功。若已在本机配置测试账号的 `NETEASE_COOKIE` 环境变量，可以明确启用登录态测试：

```bash
python -m pytest --live --cookie-env NETEASE_COOKIE -m live -v --tb=short
```

未传 `--cookie-env` 时测试不会读取任何登录 cookie。具体实测范围和限制见 [验收记录](docs/verification.md)。

## 从 0.1.1 迁移

- Python 最低版本更新为 3.10。
- 原有高层函数和对象属性保留，修正了单元素列表返回类型。
- 音频属性按需读取；网络/权限错误可能在访问这些属性时出现。
- 下载默认沿用对象品质；明确传入 `level="standard"` 时会请求该品质。
- 错误不再以字符串、打印信息、`None` 或意外 `KeyError` 混合返回；请处理相应异常。
- `query.py` 内部旧 HTML 抓取函数已移除。内部模块不是稳定 API。
- 尚未自动发布到 PyPI。

历史贡献参考：[PR #14](https://github.com/p697/cloudmusic/pull/14)、[PR #17](https://github.com/p697/cloudmusic/pull/17)、[PR #21](https://github.com/p697/cloudmusic/pull/21)。本轮吸收了跨平台路径和音质目录传递的修复方向；封面/标签写入功能暂未纳入。

MIT License · @p697
