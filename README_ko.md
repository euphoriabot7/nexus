<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a> | <a href="README_ja.md">日本語</a> | <b>한국어</b> | <a href="README_ar.md">العربية</a> | <a href="README_es.md">Español</a> | <a href="README_id.md">Bahasa Indonesia</a>
</p>

<p align="center">
  <img src="app/assets/icon.svg" width="120" alt="NEXUS logo"/>
</p>

<h1 align="center">NEXUS</h1>

<p align="center">
  셀프 호스팅 데스크톱 AI 채팅 콘솔. <b>의존성 없음</b>, OpenAI 호환 서비스라면 무엇이든, 데이터는 모두 내 컴퓨터에 남습니다.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/dependencies-none-3fb950?style=flat" alt="No dependencies">
  <img src="https://img.shields.io/badge/providers-any%20OpenAI--compatible-7a8dff?style=flat" alt="OpenAI compatible">
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-빠른-시작">빠른 시작</a> &nbsp;&middot;&nbsp;
  <a href="#-기능">기능</a> &nbsp;&middot;&nbsp;
  <a href="#-스크린샷">스크린샷</a> &nbsp;&middot;&nbsp;
  <a href="#-제어판">제어판</a> &nbsp;&middot;&nbsp;
  <a href="#-공급자">공급자</a> &nbsp;&middot;&nbsp;
  <a href="#-النماذج-المحلية">النماذج المحلية</a> &nbsp;&middot;&nbsp;
  <a href="#-에이전트-모드">에이전트 모드</a> &nbsp;&middot;&nbsp;
  <a href="#-lan">LAN</a> &nbsp;&middot;&nbsp;
  <a href="#-단축키">단축키</a> &nbsp;&middot;&nbsp;
  <a href="#-구성">구성</a>
</p>

---

NEXUS는 직접 실행하는 채팅 콘솔입니다. 여러 채팅, 여러 공급자, 영구 기록, 스트리밍, 파일·이미지 첨부,
*artifacts* 스타일 코드 미리보기 패널, 그리고 실제 사용량과 비용을 보여주는 대시보드를 갖추고 있습니다.

**OpenAI API와 호환되는 모든 서비스**에서 동작합니다(OpenAI, OpenRouter, Groq, DeepSeek, Mistral, xAI, Gemini,
로컬 Ollama와 LM Studio 등). 앱 안에서 공급자를 고르고 키를 붙여넣으면 끝입니다. 편집할 파일이 없습니다.

데이터는 밖으로 나가지 않습니다. 백엔드는 `127.0.0.1`에서 대기하고, 외부 통신은 선택한 공급자로 보내는 요청뿐입니다.

## 🚀 빠른 시작

```bash
git clone https://github.com/euphoriabot7/nexus.git
cd nexus
python3 server.py
```

<http://127.0.0.1:8765> 를 열면 첫 실행 마법사가 공급자와 키를 묻습니다. **설치할 의존성이 없습니다**
(Python 3.9+ 만 필요, 전부 표준 라이브러리).

브라우저 창 없이 독립 창과 메뉴 항목을 원하시면:

```bash
bash run.sh              # 백엔드를 시작하고 chromium --app 창을 엽니다
bash install-desktop.sh  # 앱 메뉴와 바탕화면에 바로가기 생성
bash stop.sh             # 백엔드 중지
```

## ⚡ 기능

- 여러 채팅: 검색, 고정, 이름 변경, 복제, 비우기, 삭제, 내보내기.
- 채팅별 모델 선택, 즐겨찾기 ★, 모델 목록 검색.
- SQLite 영구 기록. 닫아도 사라지지 않습니다.
- 토큰 단위 스트리밍, 지표(토큰, 지연), 중지와 재생성.
- 내 메시지를 **편집해 다시 보내기**.
- **첨부**: 드래그, 붙여넣기 또는 📎 버튼(텍스트와 이미지).
- **코드 미리보기**: 답변에 HTML/CSS/JS가 있으면 오른쪽 패널이 **작성되는 동안** 결과를 렌더링합니다.
  메시지 아래 “결과 보기” 카드로도 열 수 있고, 에이전트가 쓴 파일도 같은 방식입니다. 끌 수 있습니다.
- **전체 검색**: 모든 메시지에서 찾기, 강조 표시와 해당 위치로 이동.
- **프롬프트 템플릿**, **명령 팔레트**(Ctrl+P), 음성 입력과 읽어주기.
- 채팅별 통계, 완료 알림과 소리, 6가지 강조 색, JSON 가져오기/내보내기.
- **인터페이스 7개 언어 지원**(영어, 스페인어, 중국어, 일본어, 한국어, 아랍어, 인도네시아어). 상단 바에서 바꿀 수 있고 아랍어는 오른쪽에서 왼쪽으로 표시됩니다.
- **첨부 파일 유지** — 이미지나 문서를 보내면 대화와 함께 저장되고(썸네일 또는 파일 칩, 클릭해서 열기·다운로드) 새로고침 후에도 남아 있으며 다시 생성할 때 재전송됩니다.

## 🖼 스크린샷

<p align="center">
  <img src="assets/shots/01-chat.png" width="820" alt="채팅과 오른쪽 실시간 미리보기 패널">
  <br><sub>채팅과 오른쪽 실시간 미리보기 패널</sub>
</p>
<p align="center">
  <img src="assets/shots/02-asistente.png" width="820" alt="첫 실행 마법사: 공급자 선택, 키 입력, 연결 테스트">
  <br><sub>첫 실행 마법사: 공급자 선택, 키 입력, 연결 테스트</sub>
</p>
<p align="center">
  <img src="assets/shots/03-panel.png" width="820" alt="제어판: 사용량, 비용, 일별 활동, 모델별 표">
  <br><sub>제어판: 사용량, 비용, 일별 활동, 모델별 표</sub>
</p>
<p align="center">
  <img src="assets/shots/04-movil.png" width="820" alt="모바일 화면, LAN으로 접속한 같은 앱">
  <br><sub>모바일 화면, LAN으로 접속한 같은 앱</sub>
</p>

## 📊 제어판

왼쪽 아래 **Panel** 버튼 또는 **Ctrl+D**. 탭이 다섯 개 있습니다:

**요약** — 입력/출력 토큰, 호출 수, 예상 비용, 도구 사용, 일별 활동 그래프, 모델별 표, 요일×시간 히트맵.
  7 / 30 / 90일 / 1년 범위와 **CSV 내보내기**.
**작업** — 에이전트에게 백그라운드 작업을 맡기고(제목, 지시, 폴더, 도구, 모델) 상태·출력·토큰을 실시간으로 확인합니다.
  에이전트 모드가 필요합니다.
**프로젝트** — 파일 탐색기와 **미리보기**: `.html`은 상대 CSS/JS까지 실시간 렌더링, 이미지는 그대로, 코드는 텍스트로 표시합니다.
**로그** — 활동 기록(채팅 생성, 채팅/에이전트 턴, 작업, 앱 세션)과 유형 필터.
**LAN** — 휴대폰이나 다른 컴퓨터에서 접속할 주소와 토큰.

## 🔑 공급자와 키

첫 실행 시 또는 **설정 → 공급자와 키**에서 공급자를 고르고 키를 붙여넣은 뒤 **연결 테스트**를 누릅니다.
앱이 실제 모델 목록을 가져오고 최소 요청으로 동작을 확인합니다.

설정은 내 컴퓨터에 나만 읽을 수 있게 저장됩니다:

```
~/.config/nexus/config.json      (0600)
```

```json
{ "default": { "provider": "openai", "model": "gpt-4o-mini" },
  "providers": { "openai": { "base_url": "https://api.openai.com/v1", "api_key": "sk-..." } } }
```

일반적인 환경 변수도 사용할 수 있습니다(`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY` 등).
예시 카탈로그는 `providers.json`에 있습니다. 앱에서 base URL만 넣어 다른 서비스도 추가할 수 있습니다
(LiteLLM, vLLM, 자체 게이트웨이, Ollama의 `http://127.0.0.1:11434/v1` 등).

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

**The catalogue** (29 models, all 3 GB or less, sizes checked against the real Ollama registry and the Hugging Face
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
model that supports tool calling**. Checked against Ollama itself: `qwen3:1.7b` (1.3 GB), `qwen3:4b` (2.4 GB) and
`hermes3:3b` (1.9 GB) do; **models pulled from Hugging Face (`hf.co/…`) do not** (Ollama answers *HTTP 400: does
not support tools*), so those are for chat only. And it runs on your CPU: a local agent turn takes a while.
**Only for agent mode**: a local model needs to understand *tool calling* to touch files or run commands. Very few
small models do. The cards marked *tool calling* (**Hermes 3 3B**, **Qwen3 1.7B/4B**, **Spark X2.5 4B**) are the ones
worth trying; anything else is for chatting, writing, summarising and translating. It also runs on your CPU, so it is
slow — for real agent work you are better off with an API provider.

## 🤖 에이전트 모드(선택)

**에이전트 모드**에서 NEXUS는 [Hermes](https://hermes-agent.nousresearch.com)를 실행해 실제 도구를 씁니다:
파일 읽기/쓰기, 명령 실행, 웹 탐색. 설치되어 있지 않다면 마법사의 버튼으로 설치할 수 있습니다
(`설정 → 공급자와 키 → 에이전트 모드`). Hermes가 없어도 NEXUS는 그대로 동작하며 에이전트 버튼만 숨겨집니다.

상단의 **Chat / Agent** 알약으로 전환합니다. 채팅 모드는 모델이 바로 답하는 방식이고, 첨부(텍스트와 이미지)는 모델로 전달됩니다.
이미지는 비전 지원 모델이 필요합니다.

## 📱 LAN 접속(휴대폰, 태블릿, 다른 컴퓨터)

서버는 네트워크 전체(`0.0.0.0`)에서 대기합니다. 다른 기기에서는 Panel → LAN에 표시되는 **토큰**이 필요합니다:

```
http://내IP:8765/login?token=토큰
```

한 번 접속하면 쿠키가 저장되어 다시 묻지 않습니다. 토큰이 없으면 외부 요청은 **401**을 반환합니다.
네트워크 공개를 끄려면 `NEXUS_LAN=0 python3 server.py`. Linux에서 ufw를 쓴다면 `sudo bash lan-allow.sh`가 서브넷에 포트를 열어 줍니다.

휴대폰에서는 자동으로 모바일 레이아웃이 됩니다: 서랍형 기록, 큰 버튼, 하단 시트, 안전 영역 여백.
팁: Chrome에서 *⋮ → 홈 화면에 추가* 하면 전체 화면 앱처럼 쓸 수 있습니다.

## ⌨ 단축키

```text
    Ctrl+N     새 채팅              Ctrl+P    명령 팔레트
    Ctrl+K     모델 변경            Ctrl+F    채팅과 메시지 검색
    Ctrl+D     제어판               Ctrl+B    기록 보기/숨기기
    Alt+↑ / ↓  이전 / 다음 채팅
    Alt+1…9    n번째 채팅으로
    Enter      전송 (Shift+Enter 줄바꿈)
    ?          도움말               Esc       창 닫기, 읽기 중지
```

## 🗂 구성

```text
    nexus/
      server.py            백엔드 (Python 표준 라이브러리만)
      providers.json       예시 공급자 카탈로그
      prompts.json         예시 프롬프트 모음(25개)
      app/                 프런트엔드 (HTML + CSS + JS, 의존성 없음)
      assets/shots/        이 README의 스크린샷
      run.sh / stop.sh     시작과 중지
      install-desktop.sh   메뉴와 바탕화면 바로가기
      lan-allow.sh         ufw에서 포트 열기 (선택)

    ~/.config/nexus/config.json        공급자, 키, 기본 모델
    ~/.config/nexus/models_cache.json  공급자에서 가져온 모델 목록
    ~/.local/share/nexus/nexus.db      채팅, 메시지, 템플릿 (SQLite)
    ~/.local/share/nexus/server.log    백엔드 로그

환경 변수: `NEXUS_PORT`(8765), `NEXUS_DATA`, `NEXUS_CONFIG_DIR`, `NEXUS_LAN=0`.
```

## 📝 참고

- 키는 **저장소에 없습니다**: 내 컴퓨터(`~/.config/nexus/config.json`, 권한 0600)나 환경 변수에 있습니다.
- 에이전트 모드는 채팅의 작업 폴더에서 명령을 실행합니다. 내 컴퓨터이니 주의해서 사용하세요.
- Python 3.9+ 와 브라우저가 필요합니다. Linux(Mint/Ubuntu)에서 테스트했습니다. macOS와 Windows/WSL도 동일합니다
    (거기서는 `python3 server.py`를 실행하고 브라우저를 직접 여세요).
- 인터페이스는 **7개 언어**(영어, 스페인어, 중국어, 일본어, 한국어, 아랍어, 인도네시아어)를 지원하며 상단 바나 설정에서 바꿀 수 있습니다. 아랍어는 오른쪽에서 왼쪽 레이아웃으로 전환됩니다.

## 📄 라이선스

MIT — [LICENSE](LICENSE) 참고.
