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
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20WSL-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick start</a> &nbsp;&middot;&nbsp;
  <a href="#-features">Features</a> &nbsp;&middot;&nbsp;
  <a href="#-screenshots">Screenshots</a> &nbsp;&middot;&nbsp;
  <a href="#-control-panel">Control panel</a> &nbsp;&middot;&nbsp;
  <a href="#-providers">Providers</a> &nbsp;&middot;&nbsp;
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
      prompts.json         example prompt library (25 prompts)
      app/                 UI (HTML + CSS + JS, no dependencies)
      assets/shots/        screenshots used in this README
      run.sh / stop.sh     start and stop
      install-desktop.sh   menu and desktop launchers
      lan-allow.sh         opens the port in ufw (optional)

    ~/.config/nexus/config.json        providers, keys and default model
    ~/.config/nexus/models_cache.json  model lists fetched from the provider
    ~/.local/share/nexus/nexus.db      chats, messages and templates (SQLite)
    ~/.local/share/nexus/server.log    backend log

Environment: `NEXUS_PORT` (8765), `NEXUS_DATA`, `NEXUS_CONFIG_DIR`, `NEXUS_LAN=0`.
```

## 📝 Notes

- Keys are **not** in the repository: they live on your machine (`~/.config/nexus/config.json`, mode 0600) or in env vars.
- Agent mode runs commands in the chat's working folder: it is your own machine, use it with care.
- Requires Python 3.9+ and a browser. Tested on Linux (Mint/Ubuntu); on macOS and Windows/WSL it works the same
    (run `python3 server.py` and open the browser yourself there).
- The interface ships in **7 languages** (English, Spanish, Chinese, Japanese, Korean, Arabic and Indonesian); switch from the top bar or Settings. Arabic also flips the layout to right-to-left.

## 📄 License

MIT — see [LICENSE](LICENSE).
