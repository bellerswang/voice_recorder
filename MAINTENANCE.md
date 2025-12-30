# Voice Recorder 维护指南

## 项目概述

这是一个语音记录工具，支持：
- 📱 手机网页录音 → 上传到 GitHub
- 💻 本地电脑 → 自动转文字 → 保存到 Google Drive

---

## 🔑 需要定期检查/更新的内容

| 项目 | 位置 | 何时更新 |
|------|------|----------|
| **GitHub PAT** | 手机浏览器 (Settings) | Token 过期或重新生成时 |
| **Google API Key** | `backend/credential/key.json` | 很少需要更新 |

---

## 📁 重要文件说明

| 文件 | 作用 | 是否可删除 |
|------|------|------------|
| `backend/credential/key.json` | Google Drive 上传凭证 | ❌ 不要删 |
| `logs/processed_state.json` | 记录已处理的文件 | ⚠️ 删除会重新处理所有文件 |
| `backend/sync_and_process.py` | 核心处理脚本 | ❌ 不要删 |
| `index.html` | 手机录音网页 | ❌ 不要删 |
| `run_sync.bat` | 一键运行脚本 | ❌ 不要删 |

---

## 🔄 日常使用流程

### 录音（手机）
1. 打开 https://bellerswang.github.io/voice_recorder/
2. **选择文件夹**（可选）：从 "Recording Folder" 下拉菜单选择分类
3. 点击蓝色圆形按钮开始录音
4. 再次点击停止并上传

### 转换（电脑）
1. 双击 `run_sync.bat`
2. 自动：拉取录音 → 转文字 → 上传到 Google Drive → 删除已处理的录音

---

## ⚠️ 常见问题

| 问题 | 解决方案 |
|------|----------|
| 手机上传失败 | 点击 "Settings"，重新输入 GitHub Token |
| 本地转换失败 | 确保 `backend/credential/key.json` 存在 |
| 重复处理旧文件 | 检查 `logs/processed_state.json` 是否被误删 |
| GPU 警告 | 正常现象，用 CPU 也能运行，只是稍慢 |

---

## 📍 关键配置

如需修改，编辑 `backend/sync_and_process.py`：

```python
# Google Drive 目标文件夹 ID
GDRIVE_FOLDER_ID = '1c6IZkrEqOQnzF3hyByxQGYgyVyeUfxsu'

# 文档名称前缀
DOC_BASE_NAME = "Voice Transcripts"

# 单个文档最大字符数（超过后自动创建新卷）
MAX_DOC_SIZE = 800000
```

---

## 📂 Google Drive 位置

转录文件保存在：
https://drive.google.com/drive/folders/1c6IZkrEqOQnzF3hyByxQGYgyVyeUfxsu

文件命名格式：
- `Voice Transcripts - Vol 1`
- `Voice Transcripts - Vol 2`
- ...

---

## ✅ 无需维护的部分

- GitHub Pages 托管 - 自动运行
- Whisper 模型 - 自动下载和缓存
- 前端代码 - 已稳定

---

## 🔧 如何更新 GitHub Token

### 手机上：
1. 打开录音网页
2. 点击 "Settings"
3. 输入新 Token
4. 点击 "Save Token"

### 获取新 Token：
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. 勾选 `repo` 权限
4. 复制 `ghp_...` 开头的字符串

---

## 📁 文件夹管理

### 什么是文件夹功能?

你可以将录音分类到不同的文件夹，例如：
- `LifeVoice` - 日常个人记录
- `WorkNotes` - 工作会议笔记
- `Ideas` - 灵感想法

每个文件夹的转录会保存到独立的 Google 文档系列中。

### 如何添加新文件夹？

1. **编辑配置文件** `folders.json`：

```json
{
  "folders": [
    {
      "id": "LifeVoice",
      "name": "Life Voice",
      "description": "Personal daily recordings",
      "default": true,
      "gdrive_folder_id": "1c6IZkrEqOQnzF3hyByxQGYgyVyeUfxsu"
    },
    {
      "id": "WorkNotes",
      "name": "Work Notes",
      "description": "工作会议笔记",
      "default": false,
      "gdrive_folder_id": "你的Google Drive文件夹ID"
    }
  ]
}
```

2. **重新加载网页** - 新文件夹自动出现在下拉菜单中

3. **开始录音** - 选择文件夹后录音，系统会自动处理

### 文档命名规则

每个文件夹有独立的文档系列：
- `LifeVoice` → "Life Voice Transcripts - Vol 1"
- `WorkNotes` → "Work Notes Transcripts - Vol 1"

### 配置说明

| 字段 | 说明 | 必填 |
|------|------|------|
| `id` | 文件夹标识符（英文，无空格） | 是 |
| `name` | 下拉菜单显示名称 | 是 |
| `description` | 鼠标悬停提示文本 | 否 |
| `default` | 是否为默认选中 | 否 |
| `gdrive_folder_id` | Google Drive 文件夹 ID | 是 |
