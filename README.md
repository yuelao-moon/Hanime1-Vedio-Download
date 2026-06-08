# Hanime Media Center

Hanime Media Center 是一个本地运行的视频解析、浏览和下载管理工具。程序启动后会在本机开启 Web 服务，并自动打开浏览器访问控制台。

后端使用 Python + FastAPI，前端是原生 HTML/CSS/JavaScript。下载任务由内置队列管理，实际下载可交给 Gopeed API 执行。

## 功能概览

- 分类、搜索、作者主页和播放清单浏览
- 视频详情解析、在线播放地址探测、相关视频和评论展示
- 评论回复、头像、点赞数和回复数解析
- 登录账号、个人主页、稍后观看、喜欢影片、播放清单、订阅和观看历史
- 页面缓存、本地缓存清理和下载历史持久化
- 下载队列、任务历史、暂停、恢复、取消和重试
- Gopeed HTTP API 接力下载
- 图片和视频默认使用解析出的原始直链，并使用 `no-referrer` 策略避免本地 Referer 防盗链
- Cookie 失效时可打开浏览器抓取并持久化 Cookie
- 单 exe 打包运行，静态前端资源内置到程序中

## 直接运行源码

### 环境要求

- Windows 10/11
- Python 3.11+
- Edge、Chrome 或 Chromium 中至少一个
- 可选：Gopeed，只有需要下载时才必须启动

### 安装依赖

```powershell
python -m pip install -r python_backend\requirements.txt
```

### 启动

```powershell
python python_backend\run.py
```

默认地址：

```text
http://127.0.0.1:58080/
```

指定数据目录：

```powershell
python python_backend\run.py --app-home "D:\HanimeData"
```

## 打包为单 exe

安装运行依赖和 PyInstaller 后打包：

```powershell
python -m pip install -r python_backend\requirements.txt
python -m pip install pyinstaller
pyinstaller --clean --noconfirm HanimeMediaCenter.spec
```

打包命令会执行：

- 使用 `HanimeMediaCenter.spec` 打包
- 输出单文件程序到 `dist\HanimeMediaCenter.exe`

打包前建议先验证：

```powershell
python -m pip install -r python_backend\requirements-dev.txt
python -m pytest python_backend\tests -q
python -m compileall -q python_backend
node --check src\main\resources\static\app.js
```

## 运行 exe

打包完成后运行：

```powershell
.\dist\HanimeMediaCenter.exe
```

指定端口或数据目录：

```powershell
.\dist\HanimeMediaCenter.exe --port 58081 --app-home "D:\HanimeData"
```

程序启动后会自动打开：

```text
http://127.0.0.1:58080/
```

如果端口已被占用，程序会直接打开已有服务页面。

## 本地数据

默认数据目录：

```text
%LOCALAPPDATA%\HanimeMediaCenter\
```

常见文件：

- `settings.json`：下载目录、Gopeed、快捷键和页面缓存设置
- `hanime_media_center.db`：页面缓存、下载历史和观看历史等本地持久化数据
- `cf_cookies.json`：HTTP 请求复用的 Cookie 缓存

这些数据不会打进 exe，便于升级程序时保留设置和历史。

## Gopeed 下载配置

使用下载功能前，请先启动 Gopeed 并开启 HTTP API。然后在设置里确认：

- Gopeed 主机，默认 `127.0.0.1`
- Gopeed 端口，默认 `9999`
- Token，如果 Gopeed 未配置 Token 可留空
- 单任务连接数
- 下载目录

只解析和浏览视频时不需要启动 Gopeed。

## 验证命令

```powershell
python -m pip install -r python_backend\requirements-dev.txt
python -m pytest python_backend\tests -q
python -m compileall -q python_backend
node --check src\main\resources\static\app.js
```

## 项目结构

```text
python_backend/
├── app/
│   ├── main.py          # FastAPI 应用和 API 路由
│   ├── scraper.py       # HTTP 抓取、登录 Cookie 和数据接口请求
│   ├── parser.py        # 页面、评论、回复和视频信息解析
│   ├── downloads.py     # 下载队列、SSE 和 Gopeed API
│   ├── local_db.py      # SQLite 本地持久化
│   ├── cookie_refresh.py # 浏览器抓取 Cookie
│   ├── settings.py      # 用户设置和本地数据路径
│   └── paths.py         # 源码/打包后的静态资源定位
├── desktop.py           # exe 桌面启动入口
├── run.py               # 源码服务启动入口
├── requirements.txt     # 运行依赖
├── requirements-dev.txt # 开发和测试依赖
└── tests/               # 自动化测试

src/main/resources/static/
├── index.html
├── app.js
└── style.css

HanimeMediaCenter.spec       # PyInstaller 配置
dist/HanimeMediaCenter.exe   # 打包后的单文件程序
```

## 常见问题

### 打开 exe 后没有页面

检查是否被安全软件拦截，或手动访问：

```text
http://127.0.0.1:58080/
```

### 端口被占用

换一个端口启动：

```powershell
.\dist\HanimeMediaCenter.exe --port 58081
```

### HTTP 请求被 Cloudflare 拦截

在设置中点击刷新 Cookie。程序会打开浏览器访问站点，抓取可用 Cookie 后保存到本地；之后所有站点请求都会带上 Cookie。

### 图片或视频直链无法加载

程序会在页面级设置 `Referrer-Policy: no-referrer`，避免本地地址作为 Referer 触发防盗链。若仍无法播放，通常是远端链接过期、网络不可达或站点策略变化。

### 下载任务创建失败

确认 Gopeed 已启动、HTTP API 可访问，端口和 Token 与设置一致。

### exe 体积较大

这是单文件打包的正常现象。程序包含 Python 运行时、后端依赖、Playwright Cookie 抓取支持和前端静态资源。

## 免责声明

本项目仅作为本地个人工具使用。请遵守目标网站的使用条款和所在地法律法规。抓取和解析结果受网络环境、站点结构和验证策略影响，不能保证长期稳定。
