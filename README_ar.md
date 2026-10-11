<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_ko.md">한국어</a> | <b>العربية</b> | <a href="README_es.md">Español</a> | <a href="README_id.md">Bahasa Indonesia</a>
</p>

<p align="center">
  <img src="app/assets/icon.svg" width="120" alt="NEXUS logo"/>
</p>

<h1 align="center">NEXUS</h1>

<p align="center">
  وحدة تحكم دردشة ذكاء اصطناعي مكتبية تُستضاف ذاتيًا. <b>بدون أي تبعيات</b>، وأي مزوّد متوافق مع OpenAI، وكل شيء يبقى على جهازك.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/dependencies-none-3fb950?style=flat" alt="No dependencies">
  <img src="https://img.shields.io/badge/providers-any%20OpenAI--compatible-7a8dff?style=flat" alt="OpenAI compatible">
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-بداية-سريعة">بداية سريعة</a> &nbsp;&middot;&nbsp;
  <a href="#-الميزات">الميزات</a> &nbsp;&middot;&nbsp;
  <a href="#-لقطات-الشاشة">لقطات الشاشة</a> &nbsp;&middot;&nbsp;
  <a href="#-لوحة-التحكم">لوحة التحكم</a> &nbsp;&middot;&nbsp;
  <a href="#-المزودون">المزودون</a> &nbsp;&middot;&nbsp;
  <a href="#-modelos-locales">Modelos locales</a> &nbsp;&middot;&nbsp;
  <a href="#-وضع-الوكيل">وضع الوكيل</a> &nbsp;&middot;&nbsp;
  <a href="#-الشبكة-المحلية">الشبكة المحلية</a> &nbsp;&middot;&nbsp;
  <a href="#-اختصارات">اختصارات</a> &nbsp;&middot;&nbsp;
  <a href="#-البنية">البنية</a>
</p>

---

NEXUS وحدة تحكم دردشة تشغّلها بنفسك: محادثات متعددة، مزودون متعددون، سجل دائم، بث مباشر،
مرفقات ملفات وصور، لوحة معاينة كود على طريقة *artifacts*، ولوحة تحكم تُظهر استهلاكك وتكلفتك الحقيقية.

يعمل مع **أي خدمة متوافقة مع واجهة OpenAI** (OpenAI، OpenRouter، Groq، DeepSeek، Mistral، xAI، Gemini،
وOllama و LM Studio محليًا…). تختار المزوّد وتلصق المفتاح داخل التطبيق، ولا تحتاج إلى تحرير أي ملف.

لا شيء يخرج من جهازك: الخادم يستمع على `127.0.0.1`، والاتصال الخارجي الوحيد هو الطلب إلى المزوّد الذي اخترته.

## 🚀 بداية سريعة

```bash
git clone https://github.com/euphoriabot7/nexus.git
cd nexus
python3 server.py
```

افتح <http://127.0.0.1:8765> وسيطلب منك معالج الإعداد الأول المزوّد والمفتاح. لا شيء غير ذلك — **لا توجد تبعيات لتثبيتها**
(بايثون 3.9 أو أحدث فقط، وكل شيء من المكتبة القياسية).

تريد نافذة خاصة بلا شريط متصفح وعنصرًا في القائمة؟

```bash
bash run.sh              # يشغّل الخادم ويفتح نافذة chromium بوضع --app
bash install-desktop.sh  # ينشئ اختصارًا في قائمة التطبيقات وسطح المكتب
bash stop.sh             # يوقف الخادم
```

## ⚡ الميزات

- محادثات متعددة: بحث، تثبيت، إعادة تسمية، نسخ، تفريغ، حذف، تصدير.
- موديل لكل محادثة، ومفضلة ★، وبحث في قائمة موديلات المزوّد.
- سجل دائم في SQLite؛ لا شيء يُفقد عند الإغلاق.
- بث كلمة بكلمة، ومؤشرات (الرموز، زمن الاستجابة)، وإيقاف وإعادة توليد.
- **تعديل أي رسالة لك وإعادة إرسالها**.
- **المرفقات**: بالسحب أو اللصق أو زر 📎 (نصوص وصور).
- **معاينة الكود**: إذا احتوى الرد على HTML/CSS/JS تُعرض النتيجة في لوحة جانبية **أثناء الكتابة**،
  أو عبر بطاقة «عرض النتيجة» أسفل الرسالة. ملفات الوكيل تظهر بالطريقة نفسها، ويمكن تعطيل ذلك.
- **بحث شامل** في كل الرسائل مع تمييز والانتقال إلى الرسالة.
- **قوالب الأوامر**، و**لوحة الأوامر** (Ctrl+P)، وإملاء صوتي وقراءة بصوت عالٍ.
- إحصاءات لكل محادثة، وتنبيه صوتي ومرئي عند الانتهاء، وستة ألوان، وتصدير/استيراد JSON.
- **الواجهة بسبع لغات** (الإنجليزية والإسبانية والصينية واليابانية والكورية والعربية والإندونيسية) تُبدَّل من الشريط العلوي، والعربية تجعل الواجهة من اليمين إلى اليسار.
- **مرفقات تبقى** — الصور والمستندات التي ترسلها تُحفظ مع المحادثة (مصغّرة أو بطاقة ملف، اضغط للفتح أو التنزيل)، وتبقى بعد إعادة التحميل وتُعاد إرسالها عند إعادة التوليد.

## 🖼 لقطات الشاشة

<p align="center">
  <img src="assets/shots/01-chat.png" width="820" alt="المحادثة مع لوحة المعاينة الحيّة على اليمين">
  <br><sub>المحادثة مع لوحة المعاينة الحيّة على اليمين</sub>
</p>
<p align="center">
  <img src="assets/shots/02-asistente.png" width="820" alt="معالج الإعداد الأول: اختيار المزوّد ولصق المفتاح واختباره">
  <br><sub>معالج الإعداد الأول: اختيار المزوّد ولصق المفتاح واختباره</sub>
</p>
<p align="center">
  <img src="assets/shots/03-panel.png" width="820" alt="لوحة التحكم: الاستهلاك والتكلفة والنشاط اليومي وجدول لكل موديل">
  <br><sub>لوحة التحكم: الاستهلاك والتكلفة والنشاط اليومي وجدول لكل موديل</sub>
</p>
<p align="center">
  <img src="assets/shots/04-movil.png" width="820" alt="تصميم الهاتف، التطبيق نفسه عبر الشبكة المحلية">
  <br><sub>تصميم الهاتف، التطبيق نفسه عبر الشبكة المحلية</sub>
</p>

## 📊 لوحة التحكم

زر **Panel** أسفل اليسار أو **Ctrl+D**. خمس علامات تبويب:

**الملخص** — رموز الإدخال/الإخراج، عدد الاستدعاءات، التكلفة التقديرية، استخدام الأدوات، مخطط النشاط اليومي،
  جدول لكل موديل، وخريطة حرارية بالساعة واليوم. مدى 7 / 30 / 90 يومًا / سنة، و**تصدير CSV**.
**المهام** — أوكِل عملًا للوكيل في الخلفية (عنوان، تعليمات، مجلد، أدوات، موديل) وتابع حالته ومخرجاته ورموزه مباشرة.
  يتطلب وضع الوكيل.
**المشروع** — مستعرض ملفات مع **معاينة**: ملفات `.html` تُعرض حيّة مع CSS/JS النسبية، والصور كما هي، والكود كنص.
**السجل** — تاريخ النشاط (إنشاء محادثات، جولات دردشة/وكيل، مهام، جلسات التطبيق) مع تصفية بالنوع.
**الشبكة المحلية** — العنوان للدخول من الهاتف أو جهاز آخر، والرمز.

## 🔑 المزوّد والمفتاح

عند الاستخدام الأول، أو من **الإعدادات → المزودون والمفاتيح**، تختار المزوّد وتلصق المفتاح وتضغط **اختبار الاتصال**.
يجلب التطبيق قائمة الموديلات الحقيقية وينفّذ طلبًا صغيرًا للتأكد من عمله.

يُحفظ الإعداد على جهازك ولا يقرأه غيرك:

```
~/.config/nexus/config.json      (0600)
```

```json
{ "default": { "provider": "openai", "model": "gpt-4o-mini" },
  "providers": { "openai": { "base_url": "https://api.openai.com/v1", "api_key": "sk-..." } } }
```

يمكنك أيضًا استخدام متغيرات البيئة المعتادة (`OPENAI_API_KEY`، `OPENROUTER_API_KEY`، `GROQ_API_KEY`، `DEEPSEEK_API_KEY`…).
الفهرس التجريبي في `providers.json`، ويمكنك إضافة أي خدمة أخرى برابطها الأساسي
(LiteLLM، vLLM، بوابة خاصة، `http://127.0.0.1:11434/v1` لـ Ollama…).

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

## 🤖 وضع الوكيل (اختياري)

في **وضع الوكيل** يشغّل NEXUS برنامج [Hermes](https://hermes-agent.nousresearch.com) بأدوات حقيقية: يقرأ ويكتب الملفات
وينفّذ الأوامر ويتصفح. إن لم يكن مثبتًا، يعرض التطبيق زرًا لتثبيته في المعالج
(`الإعدادات → المزودون والمفاتيح → وضع الوكيل`). وبدون Hermes يعمل NEXUS كما هو، ويُخفى زر الوكيل فقط.

بدّل الأوضاع بزر **Chat / Agent** في الشريط العلوي. وضع الدردشة هو رد الموديل مباشرة، وتُرسل المرفقات (نصوص وصور) مع الرسالة،
وتحتاج الصور إلى موديل يدعم الرؤية.

## 📱 الدخول من الشبكة المحلية (هاتف، لوح، جهاز آخر)

يستمع الخادم على كل الشبكة (`0.0.0.0`). من خارج هذا الجهاز تحتاج **الرمز** الظاهر في Panel → الشبكة المحلية:

```
http://عنوانك:8765/login?token=الرمز
```

يحفظ ذلك ملف تعريف ولن يُطلب مرة أخرى. بدون الرمز يجيب أي طلب خارجي بـ **401**.
لإيقاف النشر على الشبكة: `NEXUS_LAN=0 python3 server.py`. وعلى لينكس مع ufw يفتح `sudo bash lan-allow.sh` المنفذ لشبكتك الفرعية.

على الهاتف يتحول التطبيق تلقائيًا إلى تصميم الهاتف: سجل منسدل، أزرار أكبر، لوحات سفلية، واحترام مناطق الأمان.
نصيحة: في كروم *⋮ → إضافة إلى الشاشة الرئيسية* لاستخدامه بملء الشاشة.

## ⌨ اختصارات

```text
    Ctrl+N     محادثة جديدة          Ctrl+P    لوحة الأوامر
    Ctrl+K     تغيير الموديل          Ctrl+F    بحث في المحادثات والرسائل
    Ctrl+D     لوحة التحكم            Ctrl+B    إظهار/إخفاء السجل
    Alt+↑ / ↓  المحادثة السابقة / التالية
    Alt+1…9    الانتقال إلى المحادثة رقم n
    Enter      إرسال (Shift+Enter سطر جديد)
    ?          المساعدة               Esc       إغلاق النوافذ، إيقاف القراءة
```

## 🗂 البنية

```text
    nexus/
      server.py            الخادم (المكتبة القياسية لبايثون فقط)
      providers.json       فهرس المزودين التجريبي
      prompts.json         مكتبة أوامر جاهزة (25)
      app/                 الواجهة (HTML + CSS + JS، بلا تبعيات)
      assets/shots/        اللقطات المستخدمة في هذا الملف
      run.sh / stop.sh     التشغيل والإيقاف
      install-desktop.sh   اختصارات القائمة وسطح المكتب
      lan-allow.sh         فتح المنفذ في ufw (اختياري)

    ~/.config/nexus/config.json        المزودون والمفاتيح والموديل الافتراضي
    ~/.config/nexus/models_cache.json  قوائم الموديلات من المزوّد
    ~/.local/share/nexus/nexus.db      المحادثات والرسائل والقوالب (SQLite)
    ~/.local/share/nexus/server.log    سجل الخادم

متغيرات البيئة: `NEXUS_PORT` (8765)، `NEXUS_DATA`، `NEXUS_CONFIG_DIR`، `NEXUS_LAN=0`.
```

## 📝 ملاحظات

- المفاتيح **ليست** في المستودع: تبقى على جهازك (`~/.config/nexus/config.json`، بصلاحيات 0600) أو في متغيرات البيئة.
- وضع الوكيل ينفّذ أوامر في مجلد عمل المحادثة: إنه جهازك، فاستخدمه بحذر.
- يتطلب بايثون 3.9 أو أحدث ومتصفحًا. تم اختباره على لينكس (Mint/Ubuntu)، ويعمل كذلك على macOS و Windows/WSL
    (هناك شغّل `python3 server.py` وافتح المتصفح بنفسك).
- الواجهة متوفرة بـ**سبع لغات** (الإنجليزية والإسبانية والصينية واليابانية والكورية والعربية والإندونيسية) وتُبدَّل من الشريط العلوي أو الإعدادات، والعربية تجعل الواجهة من اليمين إلى اليسار.

## 📄 الرخصة

MIT — انظر [LICENSE](LICENSE).
