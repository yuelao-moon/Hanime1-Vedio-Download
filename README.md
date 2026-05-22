# Hanime Media Center

Hanime Media Center 是一个本地运行的视频解析、浏览和下载管理工具。程序启动后会在本机开启 Web 服务，并自动打开浏览器访问控制台。

后端使用 Python + FastAPI，前端是原生 HTML/CSS/JavaScript。下载任务由内置队列管理，实际下载可交给 Gopeed API 执行。

## 功能概览

- 分类、搜索、作者主页和播放清单浏览
- 视频详情解析、在线播放地址探测、相关视频和评论展示
- 评论回复、头像、点赞数和回复数解析
- 页面缓存，支持设置缓存数量和清除页面缓存
- 下载队列、任务历史、暂停、恢复、取消和重试
- Gopeed HTTP API 接力下载
- Edge / Chrome / Chromium 自动检测，用于必要时完成人机验证
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
powershell -ExecutionPolicy Bypass -File run-python-backend.ps1
```

默认地址：

```text
http://127.0.0.1:58080/
```

指定数据目录：

```powershell
powershell -ExecutionPolicy Bypass -File run-python-backend.ps1 -AppHome "D:\HanimeData"
```

## 打包为单 exe

项目提供了 Windows 一键打包脚本：

```powershell
powershell -ExecutionPolicy Bypass -File build-windows-onefile.ps1
```

脚本会执行：

- 安装/确认 Python 依赖和 PyInstaller
- 编译检查 Python 文件
- 检查前端 `app.js` 语法
- 使用 `HanimeMediaCenter.spec` 打包
- 输出单文件程序到 `dist\HanimeMediaCenter.exe`

如果不想在打包前运行测试：

```powershell
powershell -ExecutionPolicy Bypass -File build-windows-onefile.ps1 -SkipTests
```

清理旧构建并重新打包：

```powershell
powershell -ExecutionPolicy Bypass -File build-windows-onefile.ps1 -Clean
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

- `settings.json`：下载目录、Gopeed、浏览器和页面缓存设置
- `download-history.json`：下载历史
- `.playwright_data\`：浏览器验证会话数据

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
python -m pytest python_backend/tests -v
python -m compileall -q python_backend
node --check src\main\resources\static\app.js
python python_backend\smoke.py
```

`smoke.py` 会启动本地测试服务并验证主要 API 是否可用。

## 项目结构

```text
python_backend/
├── app/
│   ├── main.py          # FastAPI 应用和 API 路由
│   ├── scraper.py       # HTTP 抓取和 Playwright 验证兜底
│   ├── parser.py        # 页面、评论、回复和视频信息解析
│   ├── downloads.py     # 下载队列、SSE 和 Gopeed API
│   ├── settings.py      # 用户设置和本地数据路径
│   ├── browsers.py      # 本机浏览器检测
│   └── paths.py         # 源码/打包后的静态资源定位
├── desktop.py           # exe 桌面启动入口
├── run.py               # 源码服务启动入口
├── requirements.txt     # Python 依赖
└── tests/               # 自动化测试

src/main/resources/static/
├── index.html
├── app.js
└── style.css

HanimeMediaCenter.spec       # PyInstaller 配置
build-windows-onefile.ps1    # Windows 单 exe 打包脚本
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

### Cloudflare 或人机验证失败

在设置里切换浏览器通道，例如 Edge、Chrome 或 Chromium。验证浏览器需要本机已安装，并且不要在验证过程中关闭弹出的浏览器窗口。

### 下载任务创建失败

确认 Gopeed 已启动、HTTP API 可访问，端口和 Token 与设置一致。

### exe 体积较大

这是单文件打包的正常现象。程序包含 Python 运行时、后端依赖和前端静态资源，但不内置 Edge/Chrome 浏览器本体。

## 免责声明

本项目仅作为本地个人工具使用。请遵守目标网站的使用条款和所在地法律法规。抓取和解析结果受网络环境、站点结构和验证策略影响，不能保证长期稳定。
