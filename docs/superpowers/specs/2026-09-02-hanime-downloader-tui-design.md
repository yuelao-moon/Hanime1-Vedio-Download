# Hanime Downloader Linux 终端程序设计

日期：2026-09-02

## 目标

在现有 Hanime Media Center 的页面请求、视频直链解析和系列列表解析能力基础上，新增一个可独立复制到 Linux 使用的 `uv` 项目。新项目是无浏览器、无 Web 前端的交互式终端程序，支持保存 Cookie、持久化设置、下载单个视频、下载多个视频和下载系列视频。

新项目位于仓库的 `hanime_downloader_cli/`，不修改或替换现有 Windows 桌面应用。首版只接受 Hanime1 视频页面地址，不扩展为通用视频网站下载器。

## 非目标

- 不包含 FastAPI、HTML、JavaScript 或 CSS。
- 不包含 Playwright、Chromium 或其他浏览器自动化。
- 不依赖 Gopeed。
- 不移植账号登录、评论、收藏、浏览和搜索功能。
- 不在程序内获取或刷新 Cloudflare Cookie。
- 不为 M3U8 实现纯 Python 解封装或转码器。

## 项目结构

```text
hanime_downloader_cli/
├── pyproject.toml
├── uv.lock
├── README.md
├── src/hanime_downloader/
│   ├── __init__.py
│   ├── cli.py
│   ├── settings.py
│   ├── cookies.py
│   ├── client.py
│   ├── parser.py
│   ├── series.py
│   ├── downloader.py
│   └── ffmpeg.py
└── tests/
```

各模块职责：

- `cli.py`：菜单、输入校验、任务调度和最终汇总。
- `settings.py`：设置模型、默认值、校验及原子持久化。
- `cookies.py`：Cookie 请求头解析、读取及安全覆盖保存。
- `client.py`：Hanime1 页面和下载页请求、Cookie/代理注入及 Cloudflare 页面识别。
- `parser.py`：纯 HTML 解析，提取标题、媒体地址和页面内播放清单。
- `series.py`：生成系列任务列表、保持页面顺序并按页面 URL 去重。
- `downloader.py`：普通媒体流式下载、断点续传、文件提交和并发控制。
- `ffmpeg.py`：M3U8 的 FFmpeg 可用性检查和安全子进程调用。

## 运行与终端界面

项目使用 Python 3.11+ 和 `uv`：

```bash
cd hanime_downloader_cli
uv sync
uv run hanime-downloader
```

程序使用普通滚动式终端菜单，不使用全屏 TUI，从而兼容 SSH、Docker 控制台和常见 Linux 终端：

```text
Hanime Downloader

1. 设置
2. 保存/更新 Cookie
3. 下载视频
0. 退出
```

下载子菜单：

```text
1. 下载单个视频
2. 下载多个视频
3. 下载系列视频
0. 返回
```

先前讨论过的独立 `hanime-cookie` 和 `hanime-download` 命令由统一交互入口取代。Cookie、设置和所有下载操作都从 `hanime-downloader` 菜单进入。

## 设置

设置菜单包含：

- 下载目录，默认 `./downloads`。
- 下载线程数，含义是同时下载的视频任务数量，默认 `3`，范围 `1` 至 `16`。
- 是否使用代理，布尔值。
- HTTP 代理地址，只接受合法的 `http://` 或 `https://` URL。

单个 MP4 使用一个 HTTP 连接；“下载线程数”不表示单文件分段连接数。关闭代理时保留代理地址，便于以后重新启用。启用代理后，页面解析、MP4 下载和 FFmpeg M3U8 下载使用同一个代理。

设置文件遵循 XDG 目录规范：

```text
$XDG_CONFIG_HOME/hanime-downloader/settings.json
```

未设置 `XDG_CONFIG_HOME` 时使用：

```text
~/.config/hanime-downloader/settings.json
```

相对下载目录以程序启动时的当前工作目录为基准；输入中的 `~` 会展开为用户主目录。设置通过同目录临时文件写入并原子替换。设置文件缺失时使用默认值；文件损坏或字段非法时显示原因并在当前会话使用默认值，不自动覆盖损坏文件，直到用户在设置菜单中主动保存。

## Cookie 工作流

“保存/更新 Cookie”菜单使用隐藏输入接收从浏览器开发者工具复制的完整 `Cookie` 请求头：

```text
name=value; name2=value2
```

程序解析并校验至少存在一个非空的 `name=value` 项。保存时使用临时文件和原子替换，每次完整覆盖旧 Cookie，不合并历史内容。Cookie 文件位于：

```text
$XDG_CONFIG_HOME/hanime-downloader/cookies.json
```

未设置 `XDG_CONFIG_HOME` 时使用 `~/.config/hanime-downloader/cookies.json`。在支持 POSIX 权限的平台上，目录限制为当前用户可访问，Cookie 文件权限设置为 `0600`。

下载操作只读取 Cookie，不提示输入、不自动刷新、不修改 Cookie 文件。Cookie 值不得出现在日志、进度、异常或汇总中。Cookie 只发送给 `hanime1.me`，绝不转发到第三方视频 CDN 或 FFmpeg。Cookie 缺失或请求返回 Cloudflare 验证页时，程序说明原因并提示用户退出到主菜单单独更新 Cookie。

## 页面解析

输入必须是合法的 HTTP(S) Hanime1 视频页面地址。客户端使用 `curl_cffi` 的 Chrome 兼容指纹模式，请求当前视频页；当 URL 包含视频 ID 时并发请求对应下载页。请求携带已保存 Cookie、固定的浏览器兼容 User-Agent、Referer 和可选 HTTP 代理。

解析器从下载页优先提取直链，其次从视频页中的下载表格、`source` 元素或 MP4/M3U8 URL 提取。解析结果至少包含：

- 页面 URL。
- 视频 ID。
- 标题。
- MP4 或 M3U8 地址。
- 页面播放清单中的剧集 URL、标题和顺序。

页面解析保持纯函数和无网络依赖。系列列表规则复用现有项目的侧栏播放清单选择器，兼容带缩略图和不带缩略图的新版布局。

## 下载模式

### 单个下载

用户输入一个视频页面地址。程序解析页面和媒体直链后创建一个下载任务。

### 多个下载

用户输入用英文逗号分隔的多个页面地址。程序按以下规则处理：

1. 按逗号拆分。
2. 去除每项首尾空白。
3. 丢弃空项。
4. 校验每个地址。
5. 按首次出现顺序去重。
6. 将有效地址加入公共任务队列。

某个地址非法时，在开始下载前列出非法项并要求用户重新输入，避免静默丢失任务。

### 系列下载

用户输入系列中任意一集的页面地址。程序解析当前页面的播放清单，先纳入当前视频，再按页面播放清单顺序加入其他剧集，并按标准化页面 URL 去重。每一集在实际执行时重新解析媒体直链，避免预先解析的地址过期。

如果最终只识别到当前视频，程序报告“未识别到可批量下载的系列视频”，不把它伪装成成功的系列任务。

## 并发与任务生命周期

单个、多个和系列下载共用同一任务模型。多个和系列模式通过 `asyncio.Semaphore` 按设置中的下载线程数限制同时运行的视频任务数量。每个任务相互隔离；一个任务失败不会取消其他任务。

页面请求和可重试下载错误默认最多尝试三次，并采用短暂递增退避。明确的输入错误、Cookie 缺失、Cloudflare 验证页、FFmpeg 缺失和不可写目录不做无意义重试。

用户按 `Ctrl+C` 时停止创建新任务并取消当前网络操作，保留可继续使用的临时文件，然后返回非零退出状态。

## MP4 和普通直链下载

普通媒体使用独立的 `httpx.AsyncClient`，不复用包含站点 Cookie 的页面客户端。请求携带媒体页面 Referer、浏览器兼容 User-Agent 和可选 HTTP 代理。

下载流程：

1. 最终目标不存在时创建同目录临时文件。
2. 临时文件存在时按已有字节数发送 `Range` 请求。
3. 服务端返回有效的 `206` 和匹配的 `Content-Range` 时追加下载。
4. 服务端忽略 Range 或返回不匹配内容时安全截断临时文件并从头下载。
5. 实时显示标题、已下载大小、总大小、速度和预计剩余时间。
6. 完成后校验已知的 Content-Length 或 Content-Range 总长度。
7. 使用原子替换将临时文件提交为最终文件。

最终文件已存在且非空时默认跳过。下载界面提供本次操作的“强制覆盖”选择；启用后先写新临时文件，只有下载成功才替换现有最终文件，避免失败时丢失原文件。

文件名来自解析标题和媒体类型。程序移除控制字符、路径分隔符和不安全名称，确保最终路径始终位于设置的下载目录内。

## M3U8 下载

M3U8 使用系统安装的 FFmpeg。程序先通过 `shutil.which("ffmpeg")` 检查可用性，再使用参数数组直接创建子进程，不通过 shell 拼接命令。默认使用流复制 `-c copy` 输出 MP4，不重新编码。

FFmpeg 使用媒体页面 Referer、浏览器兼容 User-Agent 和已启用的 HTTP 代理，但不接收 Hanime1 Cookie。输出先写入同目录临时 MP4，只有 FFmpeg 成功退出且文件非空时才原子提交。FFmpeg 缺失或失败只标记当前任务失败，不影响队列中的其他普通媒体任务。

## 代理边界

首版只支持 HTTP/HTTPS 代理，不支持 SOCKS。启用后：

- `curl_cffi` 页面请求使用该代理。
- `httpx` 媒体请求使用该代理。
- FFmpeg 通过其 HTTP 代理选项或仅对子进程设置的代理环境使用该代理。

代理凭据如果包含在 URL 中，不得写入日志或异常。代理地址只保存在设置文件中；README 会提醒用户对包含凭据的设置文件自行限制权限。

## 状态、结果和退出语义

`rich` 用于菜单、状态表和下载进度。任务状态包括等待、解析、下载、已跳过、成功和失败。下载结束后显示：

- 成功任务及文件路径。
- 因最终文件已存在而跳过的任务。
- 失败任务及不含敏感信息的原因。

只要本批次有失败任务，下载操作结束时显示失败汇总；程序仍返回主菜单供用户继续操作。用户从主菜单退出时，如果本次会话曾出现未解决的下载失败，则进程返回非零退出码，否则返回零。

## 依赖

运行依赖：

- `curl-cffi`
- `selectolax`
- `httpx`
- `rich`

FFmpeg 是仅用于 M3U8 的系统依赖。项目不安装或打包 FFmpeg。开发依赖至少包含 `pytest` 和 `pytest-asyncio`。所有 Python 依赖和控制台入口在 `pyproject.toml` 中声明并由 `uv.lock` 锁定。

## 测试与验收

自动化测试覆盖：

- Cookie 请求头解析、权限、敏感值不回显和原子覆盖。
- 设置默认值、保存、损坏回退、下载目录、线程范围和代理校验。
- 当前及新版页面布局中的单视频、媒体直链和系列列表解析。
- 多地址逗号拆分、去空、输入校验和顺序去重。
- 并发任务峰值不超过下载线程数。
- MP4 新下载、断点续传、Range 被忽略时重启、已存在跳过和强制覆盖。
- FFmpeg 缺失、成功退出、失败退出和临时文件提交。
- Cookie 缺失、Cloudflare 页面、网络错误和代理错误。
- 系列中单集失败后继续执行及最终汇总。

使用本地 HTTP 测试服务器完成真实字节下载和断点续传验收，不能只依赖 Mock、代码检查或编译。基本命令为：

```bash
cd hanime_downloader_cli
uv sync
uv run pytest -q
uv run hanime-downloader
```

若开发机存在 WSL 或 Linux 容器，额外在 Linux 环境执行 `uv sync`、测试和菜单启动冒烟测试。如果没有可用 Linux 环境，交付说明必须明确标注 Linux 尚未在本机实测，不得把跨平台代码检查表述成实际 Linux 验证。

## 文档交付

README 包含：

- Linux 上安装 `uv` 和 FFmpeg 的示例。
- `uv sync` 和程序启动方法。
- 主菜单与三个下载模式示例。
- 从浏览器开发者工具复制 Cookie 请求头的步骤和安全提醒。
- 设置文件、Cookie 文件和默认下载目录位置。
- Cloudflare、代理、FFmpeg、文件权限和断点续传常见问题。
- 仅下载用户有权保存内容并遵守站点条款及当地法律的免责声明。
