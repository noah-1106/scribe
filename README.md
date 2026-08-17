# scribe · 本地录音转写工具

> 把任何音频/视频文件拖进浏览器，几秒后拿到带逐句时间戳的文字稿和 SRT 字幕；
> 或者直接点录音按钮，**边说边出字**。
> **全程本机运行，文件不出电脑。** 中 / 英 / 粤自动识别。

- 模型：SenseVoice-Small（阿里，897MB）+ FSMN-VAD（3.9MB），均内置
- 解码：内置 ffmpeg（63MB，`bin/ffmpeg`），无需系统安装任何依赖
- 性能：纯 CPU，实测 **25 倍实时**（126 秒口播约 5 秒转完），模型常驻免重复加载
- 说话人分离：CAM++ 声纹聚类（28MB 按需加载），勾选即用；不开不加载，保持轻
- 前端：内置单页 Web 界面，双模式（🎙 实时录音 / 📂 上传文件）
- 项目化：每次转写自动归入项目目录，录音自动生成项目名、可重命名

---

## 两种获取方式

### A. 拷贝版（整个文件夹拷走即跑，推荐个人/团队内部使用）

整个 `scribe/` 目录（约 1.9GB）是**完全自包含**的：
模型、ffmpeg、Python 依赖（`.venv/`，864MB）全部内置。

```bash
# 拷到任何位置（外置硬盘 / 另一台同架构 Mac），直接运行：
cd scribe
./start.sh
```

> ⚠️ `.venv/` 绑定 **macOS arm64 + Python 3.9**。
> 拷到 Intel Mac 或 Windows 不能用 venv，请走方式 B 或重装依赖。

### B. GitHub 版（源码分发，需自行安装依赖和模型）

仓库**不包含** `.venv/`、`models/`、`bin/ffmpeg`（见 `.gitignore`）。
克隆后按「依赖要求」一节装好依赖、下载模型，再 `./start.sh`。

---

## 依赖要求

### 拷贝版（方式 A）

**零依赖**——Python 包、模型、ffmpeg 全部内置在文件夹内。
唯一要求：**macOS arm64（Apple Silicon）**，Python 3.9 解释器由 venv 自带。

### GitHub 版（方式 B）

| 依赖 | 要求 | 安装 |
|---|---|---|
| 操作系统 | macOS（arm64 已验证）/ Linux；Windows 需自行适配（见「平台支持」） | — |
| Python | **3.9+**（3.9 已验证） | 系统自带或 `brew install python@3.9` |
| Python 包 | 见 `requirements.txt`（funasr / torch / fastapi / uvicorn / soundfile / websockets 等） | `pip3 install -r requirements.txt` |
| ASR 模型 | SenseVoice-Small（897MB）放 `models/SenseVoiceSmall/` | `modelscope download --model iic/SenseVoiceSmall --local_dir models/SenseVoiceSmall` 或从 [ModelScope](https://modelscope.cn/models/iic/SenseVoiceSmall) 手动下载 |
| VAD 模型 | FSMN-VAD（3.9MB）放 `models/speech_fsmn_vad/` | `modelscope download --model iic/speech_fsmn_vad_zh-cn-16k-common-pytorch --local_dir models/speech_fsmn_vad` |
| 声纹模型（可选） | CAM++（28MB）放 `models/campplus_sv/`，仅说话人分离需要 | `modelscope download --model iic/speech_campplus_sv_zh-cn_16k-common --local_dir models/campplus_sv` |
| ffmpeg | 放 `bin/ffmpeg`，或系统 PATH 里装有 ffmpeg | `brew install ffmpeg`（Mac）/ [gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/)（Windows） |

> 模型加载均传 `disable_update=True`，且缓存目录钉在项目内——**不会回源联网下载**，
> 但必须先把模型文件按上表路径放好，否则启动报「模型文件缺失」。

---

## 快速上手（30 秒）

```bash
cd scribe
./start.sh
```

浏览器自动打开 **http://localhost:8399**，两种用法：

**🎙 实时录音转写**（默认页）：点红色录音钮 → 允许麦克风权限 → 自然说话。
说话几秒后出现半透明「暂显句」，停顿时变成定稿句；停止后自动落盘并可下载。
项目名在录音开始时自动生成（如 `录音 08-17 15:02`），可在输入框随时修改。

**📂 上传文件转写**：切到上传页 → 把音频或视频文件拖进虚线框 → 几秒后出现逐句文字。
项目名自动取文件名主干。

两种模式共用结果区，可一键复制全文或下载 TXT / SRT / JSON；
页面底部「📁 已保存项目」栏可查看、重命名历史项目。

> 首次启动加载模型约 15 秒（之后常驻，热启动约 2~3 秒）。

### 命令行用法（不启动浏览器 / 脚本批处理）

```bash
# 拷贝版用 .venv/bin/python；GitHub 版装好依赖后用 python3
python3 transcribe.py <音频或视频文件>            # 打印带时间戳文本
python3 transcribe.py xxx.mp4 --srt              # SRT 字幕
python3 transcribe.py xxx.mp3 --json             # JSON（含起止秒）
python3 transcribe.py xxx.m4a -o out.txt         # 写入文件
python3 transcribe.py xxx.mp3 --diarize          # 说话人标记（说话人 1/2/3…，CAM++ 按需加载）
```

> 视频文件（mp4/mov 等）会自动调用 ffmpeg 提取音轨，无需手动转换。

---

## 目录结构

```
scribe/
├── README.md                  ← 本文件
├── requirements.txt           ← Python 依赖清单（GitHub 版用）
├── .gitignore                 ← 排除 .venv/models/ffmpeg/产物
├── start.sh                   ← 一键启动（自动检测 .venv，fallback 系统 python3）
├── server.py                  ← 一体化服务：常驻模型 + Web/WS API + 托管前端 + 项目管理
├── transcribe.py              ← 转写核心 + CLI（VAD 切段 + 词级时间戳断句）
├── realtime.py                ← 实时转录核心：持久 ffmpeg 流式解码 + 流式 VAD + 在线说话人
├── diarize.py                 ← 说话人分离：CAM++ 声纹 + 余弦聚类
├── bin/
│   └── ffmpeg                 ← 内置音频解码器（63MB，macOS arm64）★ 拷贝版内置
├── .venv/                     ← Python 依赖（864MB，绑 macOS arm64 + py3.9）★ 拷贝版内置
├── frontend/
│   └── index.html             ← 单页前端（实时录音 / 上传 / 项目栏 / 下载）
├── models/                    ← ★ 拷贝版内置；GitHub 版需自行下载
│   ├── SenseVoiceSmall/       ← ASR 主模型（897MB，int8）
│   ├── speech_fsmn_vad/       ← 语音活动检测（3.9MB）
│   └── campplus_sv/           ← 说话人声纹（28MB，按需加载）
└── data/
    ├── tmp/                   ← 上传临时文件 + 解码中间产物（启动时钉为 TMPDIR）
    ├── cache/                 ← modelscope / huggingface / torch hub 缓存
    └── outputs/               ← 按项目分目录：<项目名>/<毫秒时间戳>.{txt,srt,json}
        └── <项目名>/meta.json  ← 项目元信息
```

★ = 不进 GitHub 仓库（`.gitignore` 排除），仅拷贝版自带。

---

## 它是怎么工作的（pipeline）

### 上传模式

```
音频/视频文件
   │  ① ffmpeg 归一化为 16kHz 单声道 wav
   ▼
FSMN-VAD                     ← 按静音切出语音段（得到全局偏移）
   │
   ▼
SenseVoice-Small             ← 每段识别 + 输出词级时间戳
   │
   ▼
合并层                        ← 词级时间戳 + 段偏移，按标点聚合成句
   │
   ▼
输出：带 [HH:MM:SS] 的文本 / SRT 字幕 / JSON → outputs/<项目名>/
```

### 实时录音模式

```
浏览器 MediaRecorder（每 0.5s 一块 webm/opus，仅首块带容器头）
   │  WebSocket /ws/live
   ▼
StreamDecoder                ← 每会话一个持久 ffmpeg：块按序写 stdin，采样从 stdout 流出
   │                          （逐块起进程必炸：后续块是无头分片，单独解码报 Invalid data）
   ▼
VadStream（FSMN-VAD 流式状态机）← 跨块记忆 FSMN 状态，输出流全局毫秒段边界
   │
   ├─ 段闭合 → 立即 SenseVoice 识别 → 广播「定稿句」
   ├─ 驻留段 → 服务器空闲 tick 每 1.5s 暂识别 → 广播「半透明暂显句」（闭合后被替换）
   └─ 前端停顿兜底：静音 ≥3.5s 且有暂显 → force_flush 冲成定稿句
   ▼
stop → 收割 ffmpeg 尾部采样 → VAD finish 收口 → 落盘 outputs/<项目名>/
```

说话人模式（可选，两种模式都支持）：勾选「标记说话人」后，每个**定稿句**再经 CAM++
提取 192 维声纹做余弦在线聚类（门限 0.45），输出自动加「说话人 N:」前缀
（TXT / SRT / JSON / 前端四色着色同步）。暂显句不参与聚类，防同人拆质心。

**关键设计**：
- 两个模型在服务启动时**常驻内存**，之后每次转写只有推理耗时，没有加载开销。
- 断句不靠 VAD 的粗略切分，而是**词级时间戳 + 标点聚合**（上传模式），
  或**流式 VAD 端点 + 停顿冲段**（实时模式），边界精确到 0.01 秒。
- 服务与 CLI 共用同一个 `transcribe.py` 核心，逻辑只有一份，不会跑偏。
- 上传临时文件**流式落盘**（1MB 一块），长视频不撑爆内存；
  磁盘写满时返回 `507 磁盘空间不足` 中文提示。

---

## 时长上限

| 层面 | 上限 |
|---|---|
| SenseVoice 单次推理（无 VAD） | 官方定位短语音模型，建议 ≤30 秒；funasr 动态 batch 上限 300 秒 |
| **本工具（VAD 切片路线）** | **无硬性时长上限**——音频先被 VAD 按静音切成小段（通常每段 <30s）逐段识别，整体时长只受内存限制；小时级播客/访谈直接拖入即可 |
| **实时录音模式** | 天然无限时长（边录边出，说完即转完），录音结束时只剩最后驻留段要补识别 |

> 实测：126 秒音频 5 秒转完（25 倍实时）；1 小时访谈预估 2~3 分钟出全文。

## 项目化管理

- **实时录音**：开始录音时自动生成项目名（如 `录音 08-17 15:02`），显示在录音面板输入框中，可随时修改；产物落 `outputs/<项目名>/`。
- **上传文件**：以文件名主干作为项目名，产物落 `outputs/<文件名主干>/`，零交互。
- 同一项目下多次录音/上传各自独立（毫秒时间戳命名，不覆盖、按时间排序）。
- 前端底部「已保存项目」栏展示所有项目（份数/更新时间/体积），支持重命名（重名自动加 `(2)` 后缀，绝不覆盖；路径消毒防注入）。
- 接口：`GET /api/projects` 列表；`POST /api/projects/rename` `{old,new}` 重命名。
- 旧的平铺产物文件仍可下载（向后兼容），新产物一律走项目目录。
- 重命名只改目录名，不回溯修改目录内已生成文件里的旧项目名字段（历史快照）。

## 平台支持

| 平台 | 拷贝版 | GitHub 版 | 说明 |
|---|---|---|---|
| **macOS（Apple Silicon）** | ✅ 开箱即用 | ✅ 装依赖即可 | 开发/验证平台，内置 ffmpeg 和 venv 均为 arm64 |
| **macOS（Intel）** | ❌ venv 不可用 | ⚠️ 理论可行未实测 | 需系统装 ffmpeg + 自行 pip install；内置 arm64 ffmpeg 会自动降级到系统 ffmpeg |
| **Windows** | ❌ 不可用 | ⚠️ 需适配（约半天工作量） | 见下节 |

### Windows 移植需要动的三处

| 障碍 | 现状 | 移植方案 |
|---|---|---|
| `bin/ffmpeg` 是 macOS arm64 二进制 | Windows 无法执行 | 下载 Windows 版 ffmpeg.exe 替换，或装到系统 PATH（代码已做「内置 → PATH → afconvert」三级降级） |
| `start.sh` 是 bash 脚本 | Windows 无 bash | 写一个 `start.bat`（`cd /d %~dp0` + `start http://localhost:8399` + `python server.py`）；或手动 `python server.py` |
| 音频解码兜底用了 `afconvert` | macOS 原生命令，Windows 没有 | 不影响——它是第三级兜底，代码用 `shutil.which` 探测，找不到自动跳过 |

**代码层面无其他平台耦合**：路径全部用 `pathlib`，临时目录用 `tempfile`，
推理走纯 CPU（无 CUDA/MPS 依赖），前端是纯 HTML/JS。
Python 依赖全部有 Windows 官方轮子，`pip install -r requirements.txt` 即可。

## 常见问题排查

| 现象 | 原因 | 解法 |
|---|---|---|
| 打开页面提示「服务未启动」 | 服务没在跑 | 终端运行 `./start.sh` |
| 上传后报「解码失败」 | 文件格式特殊 / 损坏 | 确认是音视频文件；如仍失败把文件名后缀告诉我 |
| 上传大文件报「磁盘空间不足」 | 磁盘满了 | `/api/health` 查 `disk_free_gb`，清理空间 |
| 录音时报「ffmpeg 解码失败 Invalid data」 | 旧版逐块解码 bug | 已修复（持久流式解码），强制刷新页面（Cmd+Shift+R） |
| 录音时不出字、停后才出 | 旧版队列 bug | 已修复，强制刷新页面 |
| 页面一直「模型加载中」 | 首次加载未完成 | 等约 15 秒；超过 1 分钟看终端 `server.log` |
| 想换端口 | 8399 被占 | `SCRIBE_PORT=9000 ./start.sh` |
| 转写结果是空的 | 音频里没人声 / 纯音乐 | 属正常，VAD 检测不到语音段 |
| 说话人归属漂移 | 短促插话（<2s）/ 多人同时说话 | 已知边界，说话人模式默认关闭即因此 |
| GitHub 版启动报「模型文件缺失」 | 模型没下载 | 按「依赖要求」下载模型放 `models/` 下 |

---

## 隐私与离线

- 完全离线可用，不联网、不上传任何数据
- 模型加载传 `disable_update=True`，缓存钉在项目内，不会回源请求 ModelScope/HuggingFace
- 所有音频处理在本机完成，产物只写入 `data/outputs/`

---

## 设计决策记录（为什么这么做）

| 决策 | 理由 | 排除项 |
|---|---|---|
| 内置 ffmpeg 而非要求系统安装 | 「开箱即用」，不污染用户环境 | Homebrew 安装（门槛+污染源） |
| 模型常驻内存 | 消除每次 15s 冷启动，转写只剩纯推理 | 每次请求重新加载 |
| 单页内置前端 | 无需 node/npm，一个 HTML 文件搞定交互 | 独立前端工程（过度设计） |
| 词级时间戳断句（上传） | 句子边界精确到 0.01s，远好于 VAD 段级切分 | `merge_vad`（会把句子粘成一坨） |
| 持久 ffmpeg 流解码（实时） | 浏览器 MediaRecorder 后续块无容器头，逐块解码必炸 | 逐块起 ffmpeg 进程（实测报 Invalid data） |
| 服务器驱动 partial（实时） | 浏览器后台标签页节流 setInterval，前端计时不可靠 | 纯前端 flush 计时 |
| CLI 与服务共用核心 | 单一事实源，避免两套逻辑漂移 | 服务里重写一套转写逻辑 |
| 说话人分离做成可选开关 | 单人录音零开销（模型不加载）；<2s 插话归属不可信，不应默认开启 | 默认开启 / pyannote（重+授权门槛） |
| 项目目录毫秒时间戳命名 | 同项目多次录音各自独立、不覆盖、按时间排序 | 秒级时间戳（理论碰撞）/ 自增序号（无法排序） |
| 所有缓存/临时目录钉到项目内 | 外置盘部署时系统盘零写入，防 100% 满盘崩溃 | 依赖系统 TMPDIR（macOS shell 自带，setdefault 不生效必须强制覆盖） |
| 拷贝版内置 .venv | 整个文件夹拷走即跑，零安装 | 依赖系统 Python 环境（换机即失效） |
| GitHub 版排除 .venv/models/ffmpeg | 仓库轻量（仅源码 <1MB），重资产由用户按需下载 | 全量上传（几个 GB 不适合 Git 托管） |
