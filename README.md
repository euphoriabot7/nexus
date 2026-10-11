<p align="center">
  <b>English</b> | <a href="README_zh.md">中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_ko.md">한국어</a> | <a href="README_ar.md">العربية</a> | <a href="README_es.md">Español</a> | <a href="README_id.md">Bahasa Indonesia</a>
</p>

<p align="center">
  <img src="app/assets/icon.svg" width="120" alt="NEXUS logo"/>
</p>

<h1 align="center">NEXUS</h1>

<p align="center">
  A self-hosted desktop AI chat console. <b>No dependencies</b>, any OpenAI-compatible provider, everything stays on your machine.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/dependencies-none-3fb950?style=flat" alt="No dependencies">
  <img src="https://img.shields.io/badge/providers-any%20OpenAI--compatible-7a8dff?style=flat" alt="OpenAI compatible">
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick start</a> &nbsp;&middot;&nbsp;
  <a href="#-features">Features</a> &nbsp;&middot;&nbsp;
  <a href="#-screenshots">Screenshots</a> &nbsp;&middot;&nbsp;
  <a href="#-control-panel">Control panel</a> &nbsp;&middot;&nbsp;
  <a href="#-providers">Providers</a> &nbsp;&middot;&nbsp;
  <a href="#-local-models">Local models</a> &nbsp;&middot;&nbsp;
  <a href="#-agent-mode">Agent mode</a> &nbsp;&middot;&nbsp;
  <a href="#-lan">LAN</a> &nbsp;&middot;&nbsp;
  <a href="#-shortcuts">Shortcuts</a> &nbsp;&middot;&nbsp;
  <a href="#-structure">Structure</a>
</p>

---

NEXUS is a desktop chat console you run yourself: multi-chat, multi-provider, persistent history, streaming,
file and image attachments, an *artifacts*-style code preview pane and a dashboard with your real token usage and cost.

It works with **any service compatible with the OpenAI API** (OpenAI, OpenRouter, Groq, DeepSeek, Mistral, xAI,
Gemini, local Ollama and LM Studio…). You pick your provider and paste your key inside the app; there are no files to edit.

Nothing leaves your machine: the backend listens on `127.0.0.1` and the only outbound connection is the request to
the provider you chose.

## 🚀 Quick start

```bash
git clone https://github.com/euphoriabot7/nexus.git
cd nexus
python3 server.py
```

Open <http://127.0.0.1:8765> and the first-run wizard asks for your provider and key. That's it — **no dependencies to
install** (Python 3.9+ only, standard library all the way).

Want its own window (no browser chrome) and a menu entry?

```bash
bash run.sh              # starts the backend and opens a chromium --app window
bash install-desktop.sh  # adds a launcher to the app menu and desktop
bash stop.sh             # stops the backend
```

**On Windows** (no need for WSL): double-click `run.bat`. It looks for Python 3.9+, starts the backend and opens the
app window with Edge or Chrome in *app mode*. `install-windows.bat` adds the shortcut to the desktop and the Start
menu, and `stop.bat` stops the backend. You can also keep using the website at <http://127.0.0.1:8765> from any browser.

## ⚡ Features

- Multiple chats: search, pin, rename, duplicate, clear, delete, export.
- Per-chat model, favourites ★ and search across the provider's model list.
- Persistent SQLite history; nothing is lost when you close it.
- Token-by-token streaming, metrics (tokens, latency), stop and regenerate.
- **Edit and resend** any of your messages.
- **Attachments**: drag, paste or use the 📎 button (text and images).
- **Code preview**: when a reply contains HTML/CSS/JS, a side pane renders the result **while it is being written**,
  or a “View result” card under the message. Files written by the agent show up the same way. Can be turned off.
- **Global search** across every message, with highlighting and jump-to-message.
- **Prompt templates**, a **command palette** (Ctrl+P), voice dictation and read-aloud.
- Per-chat statistics, desktop notification and sound when a reply lands, 6 accent colours, JSON import/export.
- **Interface in 7 languages** (English, Spanish, Chinese, Japanese, Korean, Arabic and Indonesian), switchable from the top bar; Arabic flips the layout to RTL.
- **Local models without an API key**: NEXUS installs Ollama or LM Studio, downloads the model you pick (35 small models, uncensored ones included) and leaves it ready to chat.
- **Attachments that stay** — send images or documents and they are saved with the conversation (thumbnail or file chip, click to open or download); they survive reloads and are resent when you regenerate.

## 🖼 Screenshots

<p align="center">
  <img src="assets/shots/01-chat.png" width="820" alt="Chat with the live preview pane on the right">
  <br><sub>Chat with the live preview pane on the right</sub>
</p>
<p align="center">
  <img src="assets/shots/02-asistente.png" width="820" alt="First-run wizard: pick a provider, paste the key, test it">
  <br><sub>First-run wizard: pick a provider, paste the key, test it</sub>
</p>
<p align="center">
  <img src="assets/shots/03-panel.png" width="820" alt="Control panel: usage, cost, daily activity and per-model table">
  <br><sub>Control panel: usage, cost, daily activity and per-model table</sub>
</p>
<p align="center">
  <img src="assets/shots/04-movil.png" width="820" alt="Mobile layout, same app over your LAN">
  <br><sub>Mobile layout, same app over your LAN</sub>
</p>

## 📊 Control panel

**Panel** button (bottom left) or **Ctrl+D**. Five tabs:

**Summary** — input/output tokens, calls, estimated cost, tool usage, daily activity chart, per-model table and an
  hour/weekday heatmap. Ranges of 7 / 30 / 90 days / 1 year and **CSV export**.
**Tasks** — hand a job to the agent in the background (title, prompt, folder, tools, model) and follow its state, output
  and tokens live. Requires agent mode.
**Project** — file browser with **preview**: `.html` renders live (with its relative CSS/JS), images are shown and code
  as text.
**Log** — activity history (chats created, chat/agent turns, tasks, app sessions) with a type filter.
**LAN** — address to open it from your phone or another computer, plus the token.

## 🔑 Your provider and your key

On first run, or from **Settings → Providers and keys**, you choose the provider, paste the key and hit **Test connection**.
The app fetches the provider's real model list and makes a minimal call to prove it works.

The configuration is stored on your machine, readable only by you:

```
~/.config/nexus/config.json      (0600)
```

```json
{ "default": { "provider": "openai", "model": "gpt-4o-mini" },
  "providers": { "openai": { "base_url": "https://api.openai.com/v1", "api_key": "sk-..." } } }
```

The usual environment variables work too (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY`…).
The example catalogue lives in `providers.json`; you can add any other service with its base URL (LiteLLM, vLLM, a
self-hosted gateway, `http://127.0.0.1:11434/v1` for Ollama…).

## 🧩 Local models (no API key)

No API key? NEXUS can run a **local model** on your own machine: no account, no cost, and nothing leaves the
computer once the model is downloaded. It handles the whole thing for you: it detects and installs
**[Ollama](https://ollama.com)** (or **[LM Studio](https://lmstudio.ai)**), downloads the model with a progress
bar and leaves the provider configured so you can chat right away.

Open 🧩 in the top bar, or *Settings → Local models*.

**Two ways in:**

- **Ollama** (recommended): NEXUS installs it (Linux: official script with your password; **Windows**: it downloads
  and runs `OllamaSetup.exe`; macOS: the official download), then pulls the model you pick.
- **LM Studio**: NEXUS detects it, starts its local server and can download models with the `lms` command. Each card
  tells you the Hugging Face repo to use.

**The catalogue** (35 models, all 3 GB or less, sizes checked against the real Ollama registry and the Hugging Face
files) is aimed at light machines and has a strong focus on **uncensored** models (Dolphin and *abliterated* ones),
with an honest note on every card about what it can and cannot do:

| Model | Size | Uncensored | Tools |
|---|---|---|---|
| Qwen2.5 0.5B abliterated | 379 MB | yes | no |
| TinyDolphin 1.1B (Q4/Q6) | 637 MB / 862 MB | yes | no |
| Dolphin 3.0 Llama 3.2 1B (Q4) ᴴᶠ | 770 MB | yes | no |
| Llama 3.2 1B abliterated | 911 MB | yes | no |
| Qwen2.5 1.5B abliterated | 940 MB | yes | no |
| Qwen3 1.7B abliterated | 1.06 GB | yes | no |
| Qwen2.5 Coder 1.5B abliterated | 1.07 GB | yes | no |
| Dolphin Phi 2.7B (Q2/Q4) | 1.12 / 1.53 GB | yes | no |
| StableLM Zephyr 3B | 1.53 GB | permissive | no |
| Dolphin 3.0 Llama 3.2 3B (Q3) ᴴᶠ | 1.61 GB | yes | no |
| Qwen2.5 / Qwen2.5-Coder 3B abliterated | 1.84 GB | yes | no |
| Dolphin 3.0 Qwen2.5 3B (Q4/Q5) ᴴᶠ | 1.84 / 2.12 GB | yes | no |
| Dolphin 3.0 Llama 3.2 3B (Q4/Q5) ᴴᶠ | 1.93 / 2.22 GB | yes | no |
| Hermes 3 Llama 3.2 3B ᴴᶠ · Ollama | 1.93 GB | permissive | **yes** |
| Llama 3.2 3B abliterated | 2.14 GB | yes | no |
| Qwen3 4B · Qwen3 1.7B | 2.38 / 1.30 GB | no | **yes** |
| Spark X2.5 4B heretic | 2.48 GB | yes | yes |
| MiniCPM5 2B heretic | 2.56 GB | yes | no |
| Wizard Vicuna 7B uncensored (Q2) | 2.69 GB | yes | no |
| Dolphin Mistral 7B (Q2) · OpenHermes 2.5 7B (Q2) | 2.94 GB | yes / permissive | no |

ᴴᶠ = not in the Ollama library: it is pulled from Hugging Face (`ollama pull hf.co/user/repo:Q4_K_M`), which the
Download button does for you.


**Local models in agent mode.** NEXUS prepares Hermes for you the first time you use a local model in agent
mode: it registers the provider endpoint (`hermes config set providers.ollama.base_url …`), asks Ollama for a
64k window (`model.ollama_num_ctx`, Hermes' minimum) and turns off streaming for that provider, because Hermes
hangs with Ollama when streaming tool calls. Then it drops the whole thing on the model: **agent mode needs a
model that declares tool calling**, and you can check it yourself with `ollama show <model>` (look for `tools` in
*Capabilities*). `qwen3:1.7b` (1.3 GB), `qwen3:4b`, `hermes3:3b` and the `huihui_ai` *abliterated* family do;
**models pulled from Hugging Face (`hf.co/…`) do not** (they only declare `completion`, and Ollama answers
*HTTP 400: does not support tools*), so those are for chat only. Two warnings: a small model may declare tools and
still use them badly, and a local agent turn runs on your CPU, so it takes a while — with little free RAM it will
not fit at all.
**Only for agent mode**: a local model needs to understand *tool calling* to touch files or run commands. Very few
small models do. The cards marked *tool calling* (**Hermes 3 3B**, **Qwen3 1.7B/4B**, **Spark X2.5 4B**) are the ones
worth trying; anything else is for chatting, writing, summarising and translating. It also runs on your CPU, so it is
slow — for real agent work you are better off with an API provider.

## ✨ Specialists (ready-made assistants)

You do not have to explain anything twice. NEXUS ships with **13 specialists**: ready-made assistants that
bring their own instructions, the tools they need, their recommended models and their starter prompts.

| Specialist | What it is for | Works as agent |
|---|---|---|
| 🗂️ **Butler of the machine** | Explores, finds, reads and sorts files on your computer | yes |
| 🧑‍💻 **Programmer** | Reads your project, changes it, runs the tests and tells you what it touched | yes |
| 📊 **Data analyst** | Turns your CSV and spreadsheets into decisions and charts | yes |
| 🧾 **Bookkeeper** | Orders invoices and expenses, works out margins and taxes | yes |
| 🔍 **SEO specialist** | Search intent, keywords, titles and structure, with the reason behind each one | no |
| ✍️ **Sales copywriter** | Ads, product pages and emails with conversion structure | no |
| 📣 **Social media** | A whole month of posts planned in one session | no |
| 📜 **Contract reviewer** | Explains in plain words what you are signing, and what to ask before signing | no |
| 🎓 **Tutor** | Teaches you from your own notes and checks that you understood | no |
| 🎧 **Customer support** | Short, human replies to complaints and returns | no |
| 🌍 **Translator** | Translates and adapts the tone to each market | no |
| 🧭 **Business consultant** | Three options with cost, risk and what he would do with his own money | no |
| 🏠 **Everyday helper** | Errands, lists, emails and plans, without lectures | no |

Open the **✨** button in the top bar. Each card has **Start** (it opens a chat already set up), **Edit** and
**Delete**, and you can create your own specialist with the form at the bottom: name, hook, instructions, tools,
local and cloud model, and its starter prompts. The starter prompts show up as buttons above the text box, so
you never stare at an empty screen.

**First contact, in one click.** The first card offers *Set up and start*: NEXUS installs Ollama if you do not
have it, downloads the lightest uncensored model that also knows how to use tools, leaves the provider
configured and opens the chat with the butler. Nothing to configure by hand and no API key.

## 🤖 Agent mode (optional)

In **agent mode** NEXUS runs [Hermes](https://hermes-agent.nousresearch.com) with real tools: it reads and writes files,
runs commands and browses. If you don't have it installed, the app offers to install it with a button in the wizard
(`Settings → Providers and keys → Agent mode`). Without Hermes, NEXUS works exactly the same: the agent button is simply hidden.

Switch modes with the **Chat / Agent** pill in the top bar. Chat mode is the model answering directly; attachments
(text files and images) go to the model, and images need a vision model.

## 📱 LAN access (phone, tablet, another computer)

The server listens on the whole network (`0.0.0.0`). From outside this machine you need the **token** shown in
Panel → LAN:

```
http://YOUR_IP:8765/login?token=YOUR_TOKEN
```

That sets a cookie and won't ask again. Without the token, any external request answers **401**. To disable network
access entirely: `NEXUS_LAN=0 python3 server.py`. On Linux with ufw, `sudo bash lan-allow.sh` opens the port for your subnet.

On a phone the app switches to a mobile layout by itself: drawer history, bigger controls, bottom sheets and safe-area
padding. Tip: in Chrome, *⋮ → Add to home screen* to get it full screen.

## ⌨ Shortcuts

```text
    Ctrl+N     new chat              Ctrl+P    command palette
    Ctrl+K     change model          Ctrl+F    search chats and messages
    Ctrl+D     control panel         Ctrl+B    show/hide history
    Alt+↑ / ↓  previous / next chat
    Alt+1…9    jump to chat number
    Enter      send (Shift+Enter = newline)
    ?          shortcut help         Esc       close windows, stop read-aloud
```

## 🗂 Structure

```text
    nexus/
      server.py            backend (Python standard library only)
      providers.json       example provider catalogue
      local_models.json    catalogue of small local models (Ollama / LM Studio)
      local_models.py      local model helpers (install, download, configure)
      prompts.json         example prompt library (25 prompts)
      app/                 UI (HTML + CSS + JS, no dependencies)
      assets/shots/        screenshots used in this README
      run.sh / stop.sh     start and stop (Linux, macOS)
      run.bat / stop.bat   start and stop (Windows; install-windows.bat makes shortcuts)
      install-desktop.sh   menu and desktop launchers
      lan-allow.sh         opens the port in ufw (optional)

    ~/.config/nexus/config.json        providers, keys and default model
    ~/.config/nexus/models_cache.json  model lists fetched from the provider
    ~/.local/share/nexus/nexus.db      chats, messages and templates (SQLite)
    ~/.local/share/nexus/server.log    backend log

Environment: `NEXUS_PORT` (8765), `NEXUS_DATA`, `NEXUS_CONFIG_DIR`, `NEXUS_LAN=0`.
```

## 📝 Notes

- **Self-test included**: `python3 tools/pruebas/auditoria_servidor.py` runs 40+ checks against a running server (odd inputs, full flows, attachments, import/export, specialists, providers, tasks) and tells you what fails. `repaso_funcional.py` exercises chats and specialists with your local model.
- **Runs on Windows, macOS and Linux** with just Python 3.9+: on Windows `run.bat` opens the app in its own window, and `install-windows.bat` puts a shortcut on the desktop. Updates are built in (*Settings → Updates*, or `update.bat` / `update.sh`): it pulls the latest version from GitHub and never touches your chats or keys.
- Keys are **not** in the repository: they live on your machine (`~/.config/nexus/config.json`, mode 0600) or in env vars.
- Agent mode runs commands in the chat's working folder: it is your own machine, use it with care.
- Requires Python 3.9+ and a browser. Runs on **Windows, Linux and macOS**: on Windows double-click `run.bat`
    (Edge or Chrome opens in app mode), on Linux/macOS use `run.sh`.
- The interface ships in **7 languages** (English, Spanish, Chinese, Japanese, Korean, Arabic and Indonesian); switch from the top bar or Settings. Arabic also flips the layout to right-to-left.

## 📄 License

MIT — see [LICENSE](LICENSE).
