# CapsWriter-Offline For Linux

> **按住 CapsLock 说话，松开就上屏。就这么简单。**

**CapsWriter-Offline** 是一个**完全离线**的语音输入工具。

> 📌 **Windows 用户请注意**：本仓库是 Linux 适配版本。如果你是 Windows 用户，请前往 [原项目](https://github.com/HaujetZhao/CapsWriter-Offline) 下载官方版本，功能更完整（支持托盘、全局快捷键等）。

> 本仓库当前包含了 Linux 适配改动（尤其是 X11 实时输入、终端粘贴兼容）。

**前言：最近买了一个迷你主机，装上了linux mint ，发现似乎没有好用的语音输入法，故此将曾在windows上使用过的这个项目进行改造，以适配linux，各位觉得好用的话务必点个star支持一下^_^**

## 🤖 给大模型看的快速配置提示词（推荐配置方法）

如果你想把这个仓库链接直接发给 claude code / codex / opencode 之类的agent，让它一步步帮你配置 Linux 环境，可以直接复制下面这段话：

（一般来说直接让他git clone,然后自己搞，都能搞好，搞不好就把报错信息给他，让他自己解决）
```text
你是我的 Linux 助手。请基于这个仓库 README，指导我在 Linux Mint（X11）上把项目从 0 配置到可用。

要求：
1) 先检查我的环境（Python、pip、ffmpeg、xclip/xsel、wmctrl/xprop、X11 会话）
2) 再给出“可直接复制执行”的命令，按顺序完成依赖安装
3) 指导我下载并放置模型到正确目录
4) 分别启动 server 和 client（实时模式 + 文件转录模式）
5) 如果失败，按报错给出最短排障路径
6) 优先使用本仓库 README 中的 Linux 说明，不要假设 Windows 操作步骤

请先输出“检查清单”，再输出“逐步命令”，最后输出“常见报错应对”。
```

建议把你的实际环境也补充给大模型，例如：
- 发行版：Linux Mint 22
- 会话：X11
- 终端：GNOME Terminal / Codex Terminal
- 是否已安装模型：是 / 否

---

## 🐧 Linux 快速开始（我没按这个验证过。。。最好还是让ai搞）

### 1. 安装依赖

```bash
# Debian/Ubuntu/Mint
sudo apt update
sudo apt install -y ffmpeg xclip xsel wmctrl x11-utils python3-tk
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements-server.txt -r requirements-client.txt
```

### 3. 下载模型

模型需要单独下载，解压到 `models/` 对应目录：

| 模型 | 下载链接 | 说明 |
|------|----------|------|
| **Fun-ASR-Nano**（推荐） | [Models Release](https://github.com/HaujetZhao/CapsWriter-Offline/releases/tag/models) | 旗舰模型，准确率最高 |
| SenseVoice-Small | 同上 | 速度超快，准确率稍逊 |
| Paraformer | 同上 | v1 主导模型，兼容备份 |

下载后解压，例如：
```bash
# 解压到 models/Fun-ASR-Nano/Fun-ASR-Nano-GGUF/
```

### 4. 启动服务端

```bash
python3 start_server.py
```

### 5. 启动客户端

```bash
python3 start_client.py
```

### 6. 开始使用

按住快捷键说话（Linux 默认是 `Right Shift`，可在 `config_client.py` 中修改），松开即上屏。

---

## ✨ 核心功能（以实物为准，具体的可以参考原项目，写的很详细；目前基本功能都能实现，配置文件可以配置一些功能）

- **语音输入**：按住快捷键说话，松开即输入
- **文件转录**：音视频文件拖入客户端，生成 `.srt` 字幕、`.txt` 文本、`.json` 时间戳
- **数字 ITN**：自动将「十五六个」转为「15~16 个」
- **热词增强**：支持 `hot-server.txt` 语境增强、`hot.txt` 强制替换、`hot-rule.txt` 正则替换
- **LLM 角色**：支持润色、翻译、代码助手等自定义角色
- **日记归档**：按日期保存语音和识别结果

---

## 💻 平台支持

| 系统 | 支持情况 |
|------|----------|
| **Linux (X11)** | ✅ 完整支持（服务端 + 客户端 + 实时模式 + 文件转录） |
| **Linux (Wayland)** | ⚠️ 暂不支持（Wayland 全局输入限制） |
| **Windows** | ❌ 请前往 [原项目](https://github.com/HaujetZhao/CapsWriter-Offline) |
| **MacOS** | ❌ 暂不支持 |

---

## ⚙️ 配置说明

所有设置在 `config_server.py` 和 `config_client.py` 中：

```python
# 修改快捷键（如 right shift, capslock, right ctrl 等）
shortcut = "right shift"

# 切换为"点一下录音，再点一下停止"模式
hold_mode = False

# 开启/关闭 LLM 助手
llm_enabled = True
```

---

## 🎤 模型切换

在 `config_server.py` 中修改 `model_type`：

```python
model_type = "funasr_nano"    # 旗舰模型（默认）
# model_type = "sensevoice"   # 速度超快
# model_type = "paraformer"   # 兼容备份
```

---

## 🛠️ 常见问题

**Q: 按了快捷键没反应？**
A: 确认 `start_client.py` 正在运行。检查终端是否有报错。

**Q: Linux 下终端里不粘贴 / 报 `Could not setup clipboard`？**  
A: 先安装剪贴板依赖：`xclip` 和 `xsel`。客户端会优先用粘贴模式输出；在终端窗口会自动使用 `Ctrl+Shift+V` 路径。若剪贴板不可用，会降级为模拟打字（稳定性可能下降）。

**Q: Codex/终端里报 `Failed to paste image ... incorrect type received from clipboard`？**  
A: 这是终端把 `Ctrl+V` 当作其他粘贴行为导致的。当前版本已针对终端做了快捷键路由（优先 `Ctrl+Shift+V`），请更新后重启客户端再试。

**Q: Linux 实时模式为什么只写 X11？**  
A: 当前实时热键监听是按 X11 路径适配的。Wayland 的全局输入限制更严格，不同桌面实现差异大，暂未在本项目中做统一支持。

**Q: 终端里报 `Could not setup clipboard`？**

A: 安装剪贴板依赖：
```bash
sudo apt install -y xclip xsel
```

**Q: 识别结果没字？**

A: 
1. 到 `年份/月份/assets/` 检查录音文件是否存在
2. 检查麦克风权限
3. 建议使用桌面 USB 麦克风

**Q: 可以用显卡加速吗？**

A: Fun-ASR-Nano 默认开启显卡加速（Encoder 用 DirectML，Decoder 用 Vulkan）。如果效果不好，可在 `config_server.py` 中设置：
```python
dml_enable = False
vulkan_enable = False
```

**Q: 转录太慢？**

A: 
1. 切换到 `sensevoice` 或 `paraformer` 模型
2. 降低 `num_threads` 设置
3. 禁用显卡加速试试

**Q: 如何更换快捷键？**

A: 编辑 `config_client.py`，修改 `shortcut` 字段：
```python
shortcut = "right ctrl"  # 可选：capslock, right shift, right ctrl, 等
```

**Q: LLM 角色怎么用？**

A: 在语音**开头**说出角色名。例如配置了「翻译」角色，录音时说「翻译，今天天气好」，就会交由 LLM 翻译后输出。

**Q: 如何隐藏黑窗口？**

A: Linux 版本暂无托盘功能。可以使用终端复用器（如 `tmux`）或切换到其他工作区。

---

## 📁 项目结构

```
CapsWriter-Offline-For-Linux/
├── core_client.py          # 客户端入口
├── core_server.py          # 服务端入口
├── start_client.py         # 启动脚本（客户端）
├── start_server.py         # 启动脚本（服务端）
├── config_client.py        # 客户端配置
├── config_server.py        # 服务端配置
├── hot.txt                 # 热词替换
├── hot-rule.txt            # 正则替换规则
├── hot-server.txt          # 服务端热词
├── hot-rectify.txt         # 纠错历史
├── requirements-client.txt # 客户端依赖
├── requirements-server.txt # 服务端依赖
├── models/                 # 模型目录（需自行下载）
└── LLM/                    # LLM 角色配置
```

---


## ❤️ 致谢

本项目基于以下优秀的开源项目：

- [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx)
- [FunASR](https://github.com/alibaba-damo-academy/FunASR)

---

## 📌 关于本版本

| 项目 | 说明 |
|------|------|
| **维护者** | RunMintOn |
| **基于原项目** | https://github.com/HaujetZhao/CapsWriter-Offline |
| **主要改动** | Linux X11 适配、终端粘贴兼容、无头模式支持 |
| **许可证** | 沿用原项目许可证 |

---
![alt text](_cgi-bin_mmwebwx-bin_webwxgetmsgimg__&MsgID=6425653961976367050&skey=@crypt_431f9fb2_14a21e9b1635b0dd6412384b65565fef&mmweb_appid=wx_webfilehelper.jpeg)
**我是runminton ，一个热爱创造的在读学生，
如有问题，欢迎提 Issue！**
