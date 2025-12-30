# Voice Recorder 新手指南 (Onboarding Guide)

如果你想在自己的电脑上运行这就 Voice Recorder 项目，请按照以下步骤操作。

---

## 1. 环境准备 (Prerequisites)

在开始之前，请确保你的电脑安装了以下软件：

1.  **Python 3.9+**: [下载 Python](https://www.python.org/downloads/)
    *   *安装时请勾选 "Add Python to PATH"*
2.  **Git**: [下载 Git](https://git-scm.com/downloads)
3.  **FFmpeg**: (必须安装，否则无法处理音频)
    *   [下载 FFmpeg](https://ffmpeg.org/download.html)
    *   *确保将 FFmpeg 的 `bin` 文件夹添加到系统的 PATH 环境变量中*。在终端输入 `ffmpeg -version` 确认安装成功。

---

## 2. 获取代码 (Get Code)

由于本项目依赖一个公共工具库 `Util`，你需要建立如下的文件夹结构：

```
Any_Folder/
├── Util/                  <-- 必须存在，包含 multimedia_to_text 模块
└── voice_recorder/        <-- 本项目
```

### 步骤：

1.  如果在 GitHub 上有 `Util` 库，请将其 Clone 到 `voice_recorder` 的**同级目录**。
    *   或者向开发者索要 `Util` 文件夹的副本。
2.  Clone 本项目 `voice_recorder`。

---

## 3. 安装依赖 (Install Dependencies)

1.  打开终端 (CMD 或 PowerShell)。
2.  进入 `voice_recorder` 目录。
3.  运行以下命令安装 Python 库：

```bash
pip install -r requirements.txt
```

*(如果使用 PyTorch GPU 版本以获得更快的转录速度，请参考 PyTorch 官网安装对应 CUDA 版本的 torch)*

---

## 4. 配置凭证 (Setup Credentials)

本项目需要两个关键凭证才能正常工作。

### A. Google Drive API Key (用于上传文档)
1.  去 [Google Cloud Console](https://console.cloud.google.com/) 创建一个项目。
2.  启用 **Google Drive API** 和 **Google Docs API**。
3.  创建一个 **Service Account** 并下载 JSON 密钥文件。
4.  将该文件重命名为 `key.json`。
5.  将其放入项目目录：`backend/credential/key.json`。
    *   *注意：如果没有 `credential` 文件夹，请新建一个。*
6.  **重要**：打开你的 Google Drive 目标文件夹，点击"分享"，将 Service Account 的邮箱地址（在 json 文件里能找到）添加为**编辑者**。

### B. GitHub Token (用于网页录音上传)
1.  去 GitHub -> Settings -> Developer Settings -> Personal access tokens (Classic)。
2.  生成一个新 Token，勾选 `repo` 权限。
3.  打开本项目提供的网页版录音机（例如 `https://your-username.github.io/voice_recorder/`）。
4.  点击右上角或底部的 **Settings**。
5.  填入你的 Token 并保存。

---

## 5. 运行 (Run)

### 方式一：一键运行 (Windows)
双击项目根目录下的 `run_sync.bat` 文件。

它会自动：
1.  从 GitHub 拉取最新的录音文件。
2.  调用 Whisper 进行转录。
3.  上传结果到 Google Drive。
4.  清理已处理的音频文件。

### 方式二：命令行运行
```bash
python backend/sync_and_process.py
```

---

## 6. 常见问题
- **找不到 WhisperTranscriber**: 请检查 `Util` 文件夹是否在 `voice_recorder` 的上一级目录。
- **Google 权限错误**: 请确认你已经把 Service Account 的邮箱加到了 Google Drive 文件夹的分享列表里。
