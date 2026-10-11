<p align="center">
  <a href="README.md">English</a> | <b>中文</b> | <a href="README_ja.md">日本語</a> | <a href="README_ko.md">한국어</a> | <a href="README_ar.md">العربية</a> | <a href="README_es.md">Español</a> | <a href="README_id.md">Bahasa Indonesia</a>
</p>

<p align="center">
  <img src="app/assets/icon.svg" width="120" alt="NEXUS logo"/>
</p>

<h1 align="center">NEXUS</h1>

<p align="center">
  自托管的桌面 AI 聊天控制台。<b>零依赖</b>，支持任何兼容 OpenAI 的服务，所有数据都留在你自己的机器上。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/dependencies-none-3fb950?style=flat" alt="No dependencies">
  <img src="https://img.shields.io/badge/providers-any%20OpenAI--compatible-7a8dff?style=flat" alt="OpenAI compatible">
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a> &nbsp;&middot;&nbsp;
  <a href="#-功能">功能</a> &nbsp;&middot;&nbsp;
  <a href="#-截图">截图</a> &nbsp;&middot;&nbsp;
  <a href="#-控制面板">控制面板</a> &nbsp;&middot;&nbsp;
  <a href="#-服务商">服务商</a> &nbsp;&middot;&nbsp;
  <a href="#-ローカルモデル">ローカルモデル</a> &nbsp;&middot;&nbsp;
  <a href="#-智能体模式">智能体模式</a> &nbsp;&middot;&nbsp;
  <a href="#-局域网">局域网</a> &nbsp;&middot;&nbsp;
  <a href="#-快捷键">快捷键</a> &nbsp;&middot;&nbsp;
  <a href="#-目录结构">目录结构</a>
</p>

---

NEXUS 是你自己运行的聊天控制台：多会话、多服务商、持久历史、流式输出、文件与图片附件、
*artifacts* 风格的代码预览侧栏，以及显示真实用量与花费的控制面板。

它兼容**任何遵循 OpenAI API 的服务**（OpenAI、OpenRouter、Groq、DeepSeek、Mistral、xAI、Gemini，以及本地的 Ollama、LM Studio……）。
在应用里选择服务商、粘贴密钥即可，不需要改任何配置文件。

数据不会离开你的机器：后端只监听 `127.0.0.1`，唯一的对外连接就是发往你所选服务商的请求。

## 🚀 快速开始

```bash
git clone https://github.com/euphoriabot7/nexus.git
cd nexus
python3 server.py
```

打开 <http://127.0.0.1:8765>，首次向导会询问服务商和密钥。**无需安装任何依赖**（只需 Python 3.9+，全部使用标准库）。

想要独立窗口（无浏览器工具栏）和菜单图标？

```bash
bash run.sh              # 启动后端并以 chromium --app 方式打开窗口
bash install-desktop.sh  # 在应用菜单和桌面创建快捷方式
bash stop.sh             # 停止后端
```

## ⚡ 功能

- 多会话：搜索、置顶、重命名、复制、清空、删除、导出。
- 每个会话可单独选择模型，支持收藏 ★ 和模型搜索。
- SQLite 持久历史，关闭后不会丢失。
- 逐字流式输出、用量指标（token、延迟）、停止与重新生成。
- **编辑并重发**任何属于你的消息。
- **附件**：拖拽、粘贴或点击 📎（文本和图片）。
- **代码预览**：回复中带 HTML/CSS/JS 时，侧栏会在**生成过程中**实时渲染结果，或在消息下方显示“查看结果”卡片。
  智能体写入的文件同样如此。可随时关闭。
- **全局搜索**所有消息，带高亮和跳转。
- **提示词模板**、**命令面板**（Ctrl+P）、语音输入与朗读。
- 会话统计、完成时的桌面通知与提示音、6 种主题色、JSON 导入导出。
- **界面支持 7 种语言**（英语、西班牙语、中文、日语、韩语、阿拉伯语、印尼语），可在顶栏切换；阿拉伯语会切换为从右到左。
- **附件会保留**——图片和文档随对话一起保存（缩略图或文件卡片，点击可打开或下载），刷新后仍在，重新生成时会再次发送。

## 🖼 截图

<p align="center">
  <img src="assets/shots/01-chat.png" width="820" alt="聊天界面，右侧为实时预览侧栏">
  <br><sub>聊天界面，右侧为实时预览侧栏</sub>
</p>
<p align="center">
  <img src="assets/shots/02-asistente.png" width="820" alt="首次向导：选择服务商、粘贴密钥并测试">
  <br><sub>首次向导：选择服务商、粘贴密钥并测试</sub>
</p>
<p align="center">
  <img src="assets/shots/03-panel.png" width="820" alt="控制面板：用量、花费、每日活动与按模型统计">
  <br><sub>控制面板：用量、花费、每日活动与按模型统计</sub>
</p>
<p align="center">
  <img src="assets/shots/04-movil.png" width="820" alt="移动端布局，同一应用通过局域网访问">
  <br><sub>移动端布局，同一应用通过局域网访问</sub>
</p>

## 📊 控制面板

点击左下角 **Panel** 或按 **Ctrl+D**。共五个标签页：

**概览** — 输入/输出 token、调用次数、预估花费、工具使用、每日活动图、按模型表格以及小时/星期热力图。
  支持 7 / 30 / 90 天 / 1 年区间与 **导出 CSV**。
**任务** — 在后台把工作交给智能体（标题、指令、目录、工具、模型），实时查看状态、输出与 token。需要智能体模式。
**项目** — 文件浏览器与**预览**：`.html` 实时渲染（含相对路径的 CSS/JS），图片直接显示，代码以文本展示。
**日志** — 活动历史（创建会话、聊天/智能体回合、任务、应用会话），可按类型筛选。
**局域网** — 在手机或另一台电脑上访问的地址与访问令牌。

## 🔑 服务商与密钥

首次运行时，或从 **设置 → 服务商与密钥**，选择服务商、粘贴密钥并点击 **测试连接**。应用会读取服务商的真实模型列表，
并发起一次最小请求来验证是否可用。

配置保存在你自己的机器上，仅你可读：

```
~/.config/nexus/config.json      (0600)
```

```json
{ "default": { "provider": "openai", "model": "gpt-4o-mini" },
  "providers": { "openai": { "base_url": "https://api.openai.com/v1", "api_key": "sk-..." } } }
```

也可以使用常见环境变量（`OPENAI_API_KEY`、`OPENROUTER_API_KEY`、`GROQ_API_KEY`、`DEEPSEEK_API_KEY`……）。
示例目录在 `providers.json`；你可以在应用里添加任何其他服务并填写其 base URL（LiteLLM、vLLM、自建网关、
Ollama 的 `http://127.0.0.1:11434/v1`……）。

## 🧩 本地模型（无需 API 密钥）

没有 API 密钥？NEXUS 可以在你自己的电脑上运行一个**本地模型**：无需账号、没有费用，模型下载完成后
数据也不会离开电脑。它会替你处理一切：检测并安装 **[Ollama](https://ollama.com)**（或
**[LM Studio](https://lmstudio.ai)**），带进度条下载模型，并自动配置好服务商，
让你立刻就能开始对话。

点击顶部栏的 🧩，或打开 *设置 → 本地模型*。

**两种方式：**

- **Ollama**（推荐）：NEXUS 会安装它（Linux：用你的密码运行官方脚本；**Windows**：下载并运行
  `OllamaSetup.exe`；macOS：官方下载包），然后拉取你选择的模型。
- **LM Studio**：NEXUS 会检测它，启动其本地服务器，并可以用 `lms` 命令下载模型。每张卡片
  都会告诉你对应的 Hugging Face 仓库。

**模型目录**（35 个模型，全部不超过 3 GB，大小均已对照真实的 Ollama 仓库和 Hugging Face
文件核实）面向轻量设备，重点收录**无审查**模型（Dolphin 和 *abliterated* 系列），
并在每张卡片上如实标注它能做什么、不能做什么：

| 模型 | 大小 | 无审查 | 工具 |
|---|---|---|---|
| Qwen2.5 0.5B abliterated | 379 MB | 是 | 否 |
| TinyDolphin 1.1B (Q4/Q6) | 637 MB / 862 MB | 是 | 否 |
| Dolphin 3.0 Llama 3.2 1B (Q4) ᴴᶠ | 770 MB | 是 | 否 |
| Llama 3.2 1B abliterated | 911 MB | 是 | 否 |
| Qwen2.5 1.5B abliterated | 940 MB | 是 | 否 |
| Qwen3 1.7B abliterated | 1.06 GB | 是 | 否 |
| Qwen2.5 Coder 1.5B abliterated | 1.07 GB | 是 | 否 |
| Dolphin Phi 2.7B (Q2/Q4) | 1.12 / 1.53 GB | 是 | 否 |
| StableLM Zephyr 3B | 1.53 GB | 宽松许可 | 否 |
| Dolphin 3.0 Llama 3.2 3B (Q3) ᴴᶠ | 1.61 GB | 是 | 否 |
| Qwen2.5 / Qwen2.5-Coder 3B abliterated | 1.84 GB | 是 | 否 |
| Dolphin 3.0 Qwen2.5 3B (Q4/Q5) ᴴᶠ | 1.84 / 2.12 GB | 是 | 否 |
| Dolphin 3.0 Llama 3.2 3B (Q4/Q5) ᴴᶠ | 1.93 / 2.22 GB | 是 | 否 |
| Hermes 3 Llama 3.2 3B ᴴᶠ · Ollama | 1.93 GB | 宽松许可 | **是** |
| Llama 3.2 3B abliterated | 2.14 GB | 是 | 否 |
| Qwen3 4B · Qwen3 1.7B | 2.38 / 1.30 GB | 否 | **是** |
| Spark X2.5 4B heretic | 2.48 GB | 是 | 是 |
| MiniCPM5 2B heretic | 2.56 GB | 是 | 否 |
| Wizard Vicuna 7B 无审查版 (Q2) | 2.69 GB | 是 | 否 |
| Dolphin Mistral 7B (Q2) · OpenHermes 2.5 7B (Q2) | 2.94 GB | 是 / 宽松许可 | 否 |

ᴴᶠ = 不在 Ollama 官方库中：它从 Hugging Face 拉取（`ollama pull hf.co/user/repo:Q4_K_M`），
下载按钮会替你完成这一步。


**智能体模式下的本地模型。** 你第一次在智能体模式下使用本地模型时，NEXUS 会替你准备好 Hermes：
注册服务商端点（`hermes config set providers.ollama.base_url …`），向 Ollama 请求
64k 上下文（`model.ollama_num_ctx`，Hermes 的最低要求），并对该服务商关闭流式输出，因为
Hermes 在流式传输工具调用时会与 Ollama 卡住。剩下的就看模型本身：**智能体模式需要一个
声明支持工具调用（tool calling）的模型**，你可以用 `ollama show <model>` 自行检查（看
*Capabilities* 里的 `tools`）。`qwen3:1.7b`（1.3 GB）、`qwen3:4b`、`hermes3:3b` 以及 `huihui_ai`
的 *abliterated* 系列都支持；**从 Hugging Face（`hf.co/…`）拉取的模型不支持**（它们只声明
`completion`，Ollama 会返回 *HTTP 400: does not support tools*），所以这些只能用于聊天。两点提醒：
小模型可能声明了工具却用得很糟；而且一次本地智能体回合跑在你的 CPU 上，所以很慢——空闲内存不足时根本放不下。
**仅适用于智能体模式**：本地模型需要理解*工具调用*才能操作文件或执行命令，而很少有小型模型能做到。
标记为*工具调用*的卡片（**Hermes 3 3B**、**Qwen3 1.7B/4B**、**Spark X2.5 4B**）值得一试；
其余的就用于聊天、写作、总结和翻译。它还跑在你的 CPU 上，所以很慢——真正的智能体工作，最好还是用 API 服务商。

## 🤖 智能体模式（可选）

在**智能体模式**下，NEXUS 会运行 [Hermes](https://hermes-agent.nousresearch.com) 并使用真实工具：读写文件、执行命令、浏览网页。
如果尚未安装，向导里有一个按钮可以帮你安装（`设置 → 服务商与密钥 → 智能体模式`）。
没有 Hermes 也一样能用，只是隐藏智能体按钮。

用顶部的 **Chat / Agent** 切换模式。聊天模式就是模型直接回答；附件（文本文件与图片）会一起发送，图片需要支持视觉的模型。

## 📱 局域网访问（手机、平板、另一台电脑）

服务器监听整个网络（`0.0.0.0`）。从本机以外访问需要 **Panel → 局域网** 里显示的令牌：

```
http://你的IP:8765/login?token=你的令牌
```

访问一次后会保存 cookie，之后不再询问。没有令牌时，任何外部请求返回 **401**。
完全关闭网络访问：`NEXUS_LAN=0 python3 server.py`。Linux 下使用 ufw 时，`sudo bash lan-allow.sh` 为你的子网开放端口。

在手机上应用会自动切换为移动布局：抽屉式历史、更大的控件、底部弹层和安全区域适配。
提示：Chrome 中 *⋮ → 添加到主屏幕*，即可全屏使用。

## ⌨ 快捷键

```text
    Ctrl+N     新建会话             Ctrl+P    命令面板
    Ctrl+K     切换模型             Ctrl+F    搜索会话与消息
    Ctrl+D     控制面板             Ctrl+B    显示/隐藏历史
    Alt+↑ / ↓  上一个 / 下一个会话
    Alt+1…9    跳转到第 n 个会话
    Enter      发送（Shift+Enter 换行）
    ?          快捷键帮助           Esc       关闭窗口、停止朗读
```

## 🗂 目录结构

```text
    nexus/
      server.py            后端（仅使用 Python 标准库）
      providers.json       示例服务商目录
      prompts.json         示例提示词库（25 条）
      app/                 前端（HTML + CSS + JS，无依赖）
      assets/shots/        本 README 使用的截图
      run.sh / stop.sh     启动与停止
      install-desktop.sh   菜单与桌面快捷方式
      lan-allow.sh         在 ufw 中开放端口（可选）

    ~/.config/nexus/config.json        服务商、密钥与默认模型
    ~/.config/nexus/models_cache.json  从服务商获取的模型列表
    ~/.local/share/nexus/nexus.db      会话、消息与模板（SQLite）
    ~/.local/share/nexus/server.log    后端日志

环境变量：`NEXUS_PORT`（8765）、`NEXUS_DATA`、`NEXUS_CONFIG_DIR`、`NEXUS_LAN=0`。
```

## 📝 说明

- 密钥**不在**仓库中：它们保存在你的机器上（`~/.config/nexus/config.json`，权限 0600）或环境变量里。
- 智能体模式会在会话的工作目录中执行命令：这是你自己的机器，请谨慎使用。
- 需要 Python 3.9+ 和浏览器。已在 Linux（Mint/Ubuntu）测试；macOS 与 Windows/WSL 用法相同
    （在那里直接运行 `python3 server.py` 并手动打开浏览器）。
- 界面支持 **7 种语言**（英语、西班牙语、中文、日语、韩语、阿拉伯语和印尼语），可在顶栏或设置中切换；阿拉伯语会自动切换为从右到左。

## 📄 许可证

MIT — 见 [LICENSE](LICENSE)。
