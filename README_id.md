<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_ko.md">한국어</a> | <a href="README_ar.md">العربية</a> | <a href="README_es.md">Español</a> | <b>Bahasa Indonesia</b>
</p>

<p align="center">
  <img src="app/assets/icon.svg" width="120" alt="NEXUS logo"/>
</p>

<h1 align="center">NEXUS</h1>

<p align="center">
  Konsol chat AI desktop yang Anda jalankan sendiri. <b>Tanpa dependensi</b>, semua penyedia yang kompatibel dengan OpenAI, dan semuanya tetap di komputer Anda.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/dependencies-none-3fb950?style=flat" alt="No dependencies">
  <img src="https://img.shields.io/badge/providers-any%20OpenAI--compatible-7a8dff?style=flat" alt="OpenAI compatible">
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-mulai-cepat">Mulai cepat</a> &nbsp;&middot;&nbsp;
  <a href="#-fitur">Fitur</a> &nbsp;&middot;&nbsp;
  <a href="#-tangkapan-layar">Tangkapan layar</a> &nbsp;&middot;&nbsp;
  <a href="#-panel-kendali">Panel kendali</a> &nbsp;&middot;&nbsp;
  <a href="#-penyedia">Penyedia</a> &nbsp;&middot;&nbsp;
  <a href="#-model-lokal">Model lokal</a> &nbsp;&middot;&nbsp;
  <a href="#-mode-agen">Mode agen</a> &nbsp;&middot;&nbsp;
  <a href="#-jaringan-lokal">Jaringan lokal</a> &nbsp;&middot;&nbsp;
  <a href="#-pintasan">Pintasan</a> &nbsp;&middot;&nbsp;
  <a href="#-struktur">Struktur</a>
</p>

---

NEXUS adalah konsol chat yang Anda jalankan sendiri: banyak chat, banyak penyedia, riwayat permanen, streaming,
lampiran berkas dan gambar, panel pratinjau kode bergaya *artifacts*, serta dasbor pemakaian dan biaya Anda yang sebenarnya.

Bekerja dengan **layanan apa pun yang kompatibel dengan API OpenAI** (OpenAI, OpenRouter, Groq, DeepSeek, Mistral, xAI,
Gemini, Ollama dan LM Studio lokal…). Anda memilih penyedia dan menempelkan kunci di dalam aplikasi, tanpa menyunting berkas.

Tidak ada yang keluar dari komputer Anda: backend hanya mendengarkan di `127.0.0.1` dan satu-satunya koneksi keluar
adalah permintaan ke penyedia yang Anda pilih.

## 🚀 Mulai cepat

```bash
git clone https://github.com/euphoriabot7/nexus.git
cd nexus
python3 server.py
```

Buka <http://127.0.0.1:8765> dan panduan pertama kali akan meminta penyedia serta kunci Anda. **Tidak ada dependensi
yang perlu dipasang** (cukup Python 3.9+, semuanya pustaka standar).

Ingin jendela sendiri (tanpa bilah peramban) dan entri di menu?

```bash
bash run.sh              # menjalankan backend dan membuka jendela chromium --app
bash install-desktop.sh  # membuat pintasan di menu aplikasi dan desktop
bash stop.sh             # menghentikan backend
```

## ⚡ Fitur

- Banyak chat: cari, pin, ganti nama, duplikat, kosongkan, hapus, ekspor.
- Model per chat, favorit ★, dan pencarian pada daftar model penyedia.
- Riwayat permanen di SQLite; tidak hilang saat ditutup.
- Streaming token demi token, metrik (token, latensi), hentikan dan buat ulang.
- **Sunting dan kirim ulang** pesan Anda.
- **Lampiran**: seret, tempel, atau tombol 📎 (teks dan gambar).
- **Pratinjau kode**: bila balasan memuat HTML/CSS/JS, panel samping merender hasilnya **saat sedang ditulis**,
  atau kartu “Lihat hasil” di bawah pesan. Berkas yang ditulis agen tampil dengan cara yang sama. Bisa dimatikan.
- **Pencarian global** di semua pesan, dengan sorotan dan lompat ke pesan.
- **Templat prompt**, **palet perintah** (Ctrl+P), dikte suara dan baca nyaring.
- Statistik per chat, notifikasi dan suara saat selesai, 6 warna aksen, impor/ekspor JSON.
- **Antarmuka dalam 7 bahasa** (Inggris, Spanyol, Mandarin, Jepang, Korea, Arab, Indonesia), bisa diganti dari bilah atas; bahasa Arab membalik tata letak.
- **Lampiran menetap** — gambar atau dokumen yang dikirim tersimpan bersama percakapan (thumbnail atau kartu file, klik untuk membuka/mengunduh), tetap ada setelah muat ulang dan dikirim ulang saat membuat ulang.

## 🖼 Tangkapan layar

<p align="center">
  <img src="assets/shots/01-chat.png" width="820" alt="Chat dengan panel pratinjau langsung di kanan">
  <br><sub>Chat dengan panel pratinjau langsung di kanan</sub>
</p>
<p align="center">
  <img src="assets/shots/02-asistente.png" width="820" alt="Panduan pertama kali: pilih penyedia, tempel kunci, uji">
  <br><sub>Panduan pertama kali: pilih penyedia, tempel kunci, uji</sub>
</p>
<p align="center">
  <img src="assets/shots/03-panel.png" width="820" alt="Panel kendali: pemakaian, biaya, aktivitas harian, tabel per model">
  <br><sub>Panel kendali: pemakaian, biaya, aktivitas harian, tabel per model</sub>
</p>
<p align="center">
  <img src="assets/shots/04-movil.png" width="820" alt="Tampilan ponsel, aplikasi yang sama lewat jaringan lokal">
  <br><sub>Tampilan ponsel, aplikasi yang sama lewat jaringan lokal</sub>
</p>

## 📊 Panel kendali

Tombol **Panel** (kiri bawah) atau **Ctrl+D**. Lima tab:

**Ringkasan** — token masuk/keluar, jumlah panggilan, perkiraan biaya, pemakaian alat, grafik aktivitas harian,
  tabel per model, dan peta panas per jam dan hari. Rentang 7 / 30 / 90 hari / 1 tahun serta **ekspor CSV**.
**Tugas** — serahkan pekerjaan ke agen di latar belakang (judul, perintah, folder, alat, model) dan pantau status,
  keluaran, serta token secara langsung. Perlu mode agen.
**Proyek** — penjelajah berkas dengan **pratinjau**: `.html` dirender langsung (termasuk CSS/JS relatifnya), gambar
  ditampilkan, kode sebagai teks.
**Log** — riwayat aktivitas (chat dibuat, giliran chat/agen, tugas, sesi aplikasi) dengan filter jenis.
**Jaringan lokal** — alamat untuk membukanya dari ponsel atau komputer lain, beserta tokennya.

## 🔑 Penyedia dan kunci Anda

Saat pertama kali, atau dari **Pengaturan → Penyedia dan kunci**, pilih penyedia, tempel kunci, lalu tekan **Uji koneksi**.
Aplikasi mengambil daftar model asli dari penyedia dan melakukan satu panggilan minimal untuk memastikan berfungsi.

Konfigurasinya disimpan di komputer Anda dan hanya Anda yang bisa membacanya:

```
~/.config/nexus/config.json      (0600)
```

```json
{ "default": { "provider": "openai", "model": "gpt-4o-mini" },
  "providers": { "openai": { "base_url": "https://api.openai.com/v1", "api_key": "sk-..." } } }
```

Variabel lingkungan biasa juga berlaku (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY`…).
Katalog contoh ada di `providers.json`; Anda bisa menambahkan layanan lain dengan base URL-nya
(LiteLLM, vLLM, gerbang sendiri, `http://127.0.0.1:11434/v1` untuk Ollama…).

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

## 🤖 Mode agen (opsional)

Dalam **mode agen** NEXUS menjalankan [Hermes](https://hermes-agent.nousresearch.com) dengan alat sungguhan: membaca dan menulis
berkas, menjalankan perintah, dan menjelajah. Bila belum terpasang, aplikasi menawarkan memasangnya lewat tombol di panduan
(`Pengaturan → Penyedia dan kunci → Mode agen`). Tanpa Hermes, NEXUS tetap berfungsi sama; tombol agen hanya disembunyikan.

Ganti mode dengan pil **Chat / Agent** di bilah atas. Mode chat adalah jawaban langsung dari model; lampiran
(berkas teks dan gambar) dikirim ke model, dan gambar memerlukan model dengan kemampuan visi.

## 📱 Akses jaringan lokal (ponsel, tablet, komputer lain)

Server mendengarkan di seluruh jaringan (`0.0.0.0`). Dari luar komputer ini Anda memerlukan **token** yang tampil di
Panel → Jaringan lokal:

```
http://IP_ANDA:8765/login?token=TOKEN_ANDA
```

Itu menyimpan cookie dan tidak akan diminta lagi. Tanpa token, permintaan eksternal menjawab **401**.
Untuk mematikan akses jaringan: `NEXUS_LAN=0 python3 server.py`. Di Linux dengan ufw, `sudo bash lan-allow.sh` membuka port untuk subnet Anda.

Di ponsel aplikasi otomatis beralih ke tata letak seluler: riwayat berbentuk laci, kontrol lebih besar, sheet bawah, dan
area aman. Tips: di Chrome, *⋮ → Tambahkan ke layar utama* agar tampil penuh layar.

## ⌨ Pintasan

```text
    Ctrl+N     chat baru             Ctrl+P    palet perintah
    Ctrl+K     ganti model           Ctrl+F    cari chat dan pesan
    Ctrl+D     panel kendali         Ctrl+B    tampilkan/sembunyikan riwayat
    Alt+↑ / ↓  chat sebelumnya / berikutnya
    Alt+1…9    lompat ke chat nomor n
    Enter      kirim (Shift+Enter = baris baru)
    ?          bantuan pintasan      Esc       tutup jendela, hentikan bacaan
```

## 🗂 Struktur

```text
    nexus/
      server.py            backend (hanya pustaka standar Python)
      providers.json       katalog penyedia contoh
      prompts.json         pustaka prompt contoh (25)
      app/                 antarmuka (HTML + CSS + JS, tanpa dependensi)
      assets/shots/        tangkapan layar untuk README ini
      run.sh / stop.sh     menjalankan dan menghentikan
      install-desktop.sh   pintasan menu dan desktop
      lan-allow.sh         membuka port di ufw (opsional)

    ~/.config/nexus/config.json        penyedia, kunci, dan model bawaan
    ~/.config/nexus/models_cache.json  daftar model dari penyedia
    ~/.local/share/nexus/nexus.db      chat, pesan, dan templat (SQLite)
    ~/.local/share/nexus/server.log    log backend

Variabel lingkungan: `NEXUS_PORT` (8765), `NEXUS_DATA`, `NEXUS_CONFIG_DIR`, `NEXUS_LAN=0`.
```

## 📝 Catatan

- Kunci **tidak** ada di repositori: tersimpan di komputer Anda (`~/.config/nexus/config.json`, mode 0600) atau variabel lingkungan.
- Mode agen menjalankan perintah di folder kerja chat: itu komputer Anda sendiri, gunakan dengan hati-hati.
- Memerlukan Python 3.9+ dan peramban. Diuji di Linux (Mint/Ubuntu); di macOS dan Windows/WSL sama saja
    (di sana jalankan `python3 server.py` dan buka peramban sendiri).
- Antarmuka tersedia dalam **7 bahasa** (Inggris, Spanyol, Mandarin, Jepang, Korea, Arab, dan Indonesia); ubah dari bilah atas atau Pengaturan. Bahasa Arab juga membalik tata letak ke kanan-ke-kiri.

## 📄 Lisensi

MIT — lihat [LICENSE](LICENSE).
