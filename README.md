# Hanime Media Center

本地运行的 Hanime 视频解析与下载工具。当前后端已切换为 **Python + FastAPI**，前端继续使用原生 HTML / CSS / JavaScript，下载能力通过 Gopeed API 接力完成。

---

## 快速开始

**前置条件**：Python 3.11+，系统已安装 Edge 或 Chrome；如需下载，请先启动 Gopeed 并打开 API。

```powershell
powershell -ExecutionPolicy Bypass -File run-python-backend.ps1
```

浏览器访问 `http://localhost:58080`。

---

## 功能

### 浏览与解析

- **分类浏览**：按分类抓取站点内容，分页浏览封面和标题
- **视频解析**：输入视频页面地址，解析可播放/下载的视频源
- **Cloudflare 验证**：默认 HTTP 快速抓取；被拦截时按设置打开 Edge / Chrome / Chromium，并保持浏览器常驻复用

### 下载中心

- **下载队列**：实时显示进度、速度、状态
- **暂停/恢复/取消**：支持单个和批量操作
- **历史记录**：保存任务状态，支持重试失败任务
- **Gopeed 接力**：通过 Gopeed HTTP API 创建和轮询下载任务

### 设置

- **下载目录**：自定义视频保存路径
- **并发控制**：调整最大同时下载数
- **Gopeed API**：配置主机、端口、令牌和单任务连接数
- **验证浏览器**：自动检测本机 Edge / Chrome / Chromium，设置 Cloudflare 验证时打开的浏览器
- **缓存清理**：清除下载历史并重置抓取状态

---

## 技术栈

### 前端

- 原生 HTML / CSS / JavaScript
- Hls.js
- 自定义暗色 UI

### 后端

- **Python 3.11+**
- **FastAPI / uvicorn**：本地 Web 服务和 API
- **httpx**：异步 HTTP 抓取
- **Playwright**：按需打开用户选择的浏览器完成 Cloudflare 验证，并在后端运行期间保持会话
- **selectolax**：HTML 解析
- **SSE**：下载快照实时推送

### 下载引擎

- 后端维护下载队列和状态快照
- 实际下载由 Gopeed API 执行
- 支持 Gopeed 连接数配置和任务轮询

---

## 项目结构

```text
python_backend/
├── app/
│   ├── main.py          # FastAPI 入口和 API 路由
│   ├── scraper.py       # HTTP 优先抓取，Playwright 验证兜底
│   ├── parser.py        # HTML 解析
│   ├── downloads.py     # 下载队列、SSE、Gopeed API
│   ├── settings.py      # 设置与历史数据
│   └── browsers.py      # 本地浏览器检测
├── tests/               # Python 测试
├── run.py               # 后端启动入口
└── smoke.py             # 本地 API smoke 测试

src/main/resources/static/
├── index.html
├── app.js
└── style.css
```

---

## 本地数据目录

默认数据目录为 `%LOCALAPPDATA%\HanimeMediaCenter\`：

- `settings.json` — 用户配置
- `download-history.json` — 下载历史
- `.playwright_data/` — Playwright 独立浏览器配置目录

可通过启动参数指定隔离目录：

```powershell
powershell -ExecutionPolicy Bypass -File run-python-backend.ps1 -AppHome "D:\HanimeData"
```

---

## 验证

```powershell
python -m pytest python_backend/tests -v
python python_backend/smoke.py
python -m compileall -q python_backend
```

---

## 免责声明

- 本项目是一个本地运行的个人工具，不是云端服务
- 抓取能力依赖目标站点状态、网络环境和 Cloudflare 验证
- 仅用于个人学习和研究，请遵守目标网站的使用条款
