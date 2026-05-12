# Hanime Media Center

本地运行的 Hanime 视频解析与下载工具。提供分类浏览、视频解析、下载队列管理、历史记录去重、失败自动重试、检测更新等功能。

---

## 快速开始

### 方式一：直接运行

1. 从 [Releases](https://github.com/yuelao-moon/Hanime1-Vedio-Download/releases) 下载 `HanimeMediaCenter-*.exe`
2. 双击运行，程序自动解压并启动本地 Web 服务（含内置 Java 21 运行环境）
3. 浏览器访问启动日志中显示的地址（默认 `http://localhost:58080`）

### 方式二：源码编译运行

**前置条件**：JDK 21+，Maven 3.6+

```bash
mvn spring-boot:run
```

浏览器访问 `http://localhost:58080`。

### 方式三：自打包 EXE

```bash
powershell -ExecutionPolicy Bypass -File package-exe.ps1
```

输出到 `dist/HanimeMediaCenter.exe`（含内置 JRE 的安装程序）。

---

## 功能

### 浏览与解析

- **分类浏览**：按分类抓取站点内容，分页浏览封面和标题
- **视频解析**：输入视频页面地址，解析可播放/下载的视频源
- **系列视频**：在详情区域查看同系列条目，支持一键加入下载

### 下载中心

- **下载队列**：实时显示进度、速度、状态
- **暂停/恢复/取消**：支持单个和批量操作，取消后立即进入历史记录
- **失败自动重试**：下载失败自动重试最多 3 次，30 秒无进度也判定为超时重试
- **历史记录**：仅保留已完成/下载失败两种标签；按标题去重，文件存在则覆盖为已完成
- **全部重试**：一键重试所有失败任务
- **本地文件跳过**：目标文件已存在时跳过下载直接标记完成

### 设置

- **下载目录**：自定义视频保存路径
- **并发控制**：调整最大同时下载数
- **缓存清理**：清除浏览器抓取缓存
- **检查更新**：从 GitHub Release 检查新版本

### 视觉优化

- **封面智能显示**：自动检测图片横竖方向，横图铺满宽度，竖图自适应高度
- **状态标签简化**：历史中只保留"已完成"（绿）和"下载失败"（按钮可重试）

---

## 技术栈

### 前端

- 原生 HTML / CSS / JavaScript（无框架）
- Hls.js（m3u8 流播放）
- 自定义玻璃态 UI 风格

### 后端

- **Java 21** + **Spring Boot 3.2.4**
- **Playwright for Java**：驱动系统 Edge/Chrome 浏览器，处理 Cloudflare 验证
- **Jsoup**：从抓取的 HTML 中提取结构化数据
- **SSE (SseEmitter)**：实时推送下载进度

### 下载引擎

- 任务队列（`LinkedBlockingQueue` + `ConcurrentHashMap`）
- 多线程并行下载（12 workers）
- 解析串行化（`resolveLock`）：多任务并发时视频解析排队使用 Playwright，不阻塞下载插槽
- 超时看门狗（30 秒无进度自动重试）
- 文件存在性校验（`Files.exists + Files.size > 0`），本地已有视频则跳过下载直接完成
- 断点续传（清理部分文件后重试）

### 打包

- **Maven**：项目构建
- **jlink**：创建最小 JRE
- **jpackage**：生成 Windows 安装程序（含内置 JRE，~50MB）

---

## 项目结构

```
src/main/java/com/wangver/hanime/
├── controller/
│   └── ApiController.java          # REST API 入口
│   └── DownloadController.java     # 下载相关端点
├── service/
│   ├── DownloadService.java        # 下载队列、重试、超时、历史去重
│   ├── HanimeParserService.java    # 视频解析、Playwright 抓取
│   ├── PlaywrightBrowserService.java # 浏览器管理
│   ├── SettingsManager.java        # 配置读写
│   ├── AppVersion.java             # 版本号 + GitHub 仓库信息
│   └── ...
├── model/
│   ├── DownloadTaskView.java       # 下载任务视图
│   ├── DownloadStatus.java         # 状态枚举
│   ├── AppSettings.java            # 设置模型
│   └── ...
└── resource/static/
    ├── index.html                  # 主页面
    ├── app.js                      # 前端交互逻辑
    └── style.css                   # 界面样式
```

---

## 关键特性说明

### 下载重试机制

```
下载异常/超时
  ├─ retryCount < 3 → QUEUED → 重新入队
  │   errorMessage: "下载失败/超时，第N次重试中"
  └─ retryCount >= 3 → FAILED → 进入历史记录
      errorMessage: "已重试3次，下载失败/超时"
```

- 网络波动、Cloudflare 拦截、服务器超时均会触发重试
- 重试前自动清理残留的部分文件
- 30 秒进度看门狗：进度无变化超过 30 秒自动触发重试

### 历史记录去重

```
每次添加记录或打开下载中心时:
  1. 按标题分组
  2. 检查文件是否实际存在于磁盘
     ├─ 存在 → 覆盖为 COMPLETED
     └─ 不存在 → 优先保留 FAILED（显示错误信息）
  3. 同一标题只保留一条记录
```

### 检测更新

- 通过 GitHub Releases API 检查版本
- 设置面板中点击"检查更新"
- 后端自动对比版本号，有更新则显示下载链接

---

## 版本号维护

发新版时需同步修改两处：

| 文件 | 位置 |
|------|------|
| `src/main/java/.../AppVersion.java` | `VERSION = "1.0.0"` |
| `pom.xml` | `<version>1.0.0-SNAPSHOT</version>` |

然后在 GitHub 创建 Release（tag 格式 `v1.1.0`），用户即可通过"检查更新"检测到。

---

## 本地数据目录

程序运行数据保存在 `%LOCALAPPDATA%\HanimeMediaCenter\`：

- `settings.json` — 用户配置（下载目录、并发数等）
- `download-history.json` — 下载历史
- `bundle/` — EXE 自解压的运行时文件
- `playwright-data/` — 浏览器缓存

---

## 免责声明

- 本项目是一个**本地运行的个人工具**，不是云端服务
- 抓取能力依赖系统已安装的 Edge 或 Chrome 浏览器
- 仅用于个人学习和研究，请遵守目标网站的使用条款
