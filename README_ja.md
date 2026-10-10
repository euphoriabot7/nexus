<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a> | <b>日本語</b> | <a href="README_ko.md">한국어</a> | <a href="README_ar.md">العربية</a> | <a href="README_es.md">Español</a> | <a href="README_id.md">Bahasa Indonesia</a>
</p>

<p align="center">
  <img src="app/assets/icon.svg" width="120" alt="NEXUS logo"/>
</p>

<h1 align="center">NEXUS</h1>

<p align="center">
  セルフホスト型のデスクトップ AI チャットコンソール。<b>依存関係ゼロ</b>、OpenAI 互換のどのサービスでも動作し、データはすべて手元に残ります。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/dependencies-none-3fb950?style=flat" alt="No dependencies">
  <img src="https://img.shields.io/badge/providers-any%20OpenAI--compatible-7a8dff?style=flat" alt="OpenAI compatible">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20WSL-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-クイックスタート">クイックスタート</a> &nbsp;&middot;&nbsp;
  <a href="#-機能">機能</a> &nbsp;&middot;&nbsp;
  <a href="#-スクリーンショット">スクリーンショット</a> &nbsp;&middot;&nbsp;
  <a href="#-コントロールパネル">コントロールパネル</a> &nbsp;&middot;&nbsp;
  <a href="#-プロバイダー">プロバイダー</a> &nbsp;&middot;&nbsp;
  <a href="#-エージェントモード">エージェントモード</a> &nbsp;&middot;&nbsp;
  <a href="#-lan">LAN</a> &nbsp;&middot;&nbsp;
  <a href="#-ショートカット">ショートカット</a> &nbsp;&middot;&nbsp;
  <a href="#-構成">構成</a>
</p>

---

NEXUS は自分で動かすチャットコンソールです。複数チャット、複数プロバイダー、永続履歴、ストリーミング、
ファイルと画像の添付、*artifacts* 風のコードプレビューペイン、実際の使用量とコストが見えるダッシュボードを備えています。

**OpenAI API 互換のあらゆるサービス**で動きます（OpenAI、OpenRouter、Groq、DeepSeek、Mistral、xAI、Gemini、
ローカルの Ollama や LM Studio など）。プロバイダーを選んでキーを貼り付けるだけ。設定ファイルを編集する必要はありません。

データは外に出ません。バックエンドは `127.0.0.1` で待ち受け、外部への通信は選んだプロバイダーへのリクエストだけです。

## 🚀 クイックスタート

```bash
git clone https://github.com/euphoriabot7/nexus.git
cd nexus
python3 server.py
```

<http://127.0.0.1:8765> を開くと、初回ウィザードがプロバイダーとキーを尋ねます。**インストールが必要な依存関係はありません**
（Python 3.9+ のみ、すべて標準ライブラリ）。

独立したウィンドウ（ブラウザーの枠なし）とメニュー登録が欲しい場合：

```bash
bash run.sh              # バックエンドを起動し chromium --app でウィンドウを開く
bash install-desktop.sh  # アプリメニューとデスクトップにショートカットを作成
bash stop.sh             # バックエンドを停止
```

## ⚡ 機能

- 複数チャット：検索、ピン留め、名前変更、複製、クリア、削除、エクスポート。
- チャットごとのモデル選択、お気に入り ★、モデル一覧の検索。
- SQLite による永続履歴。閉じても消えません。
- トークン単位のストリーミング、指標（トークン、遅延）、停止と再生成。
- 自分のメッセージを**編集して再送信**。
- **添付**：ドラッグ、貼り付け、または 📎 ボタン（テキストと画像）。
- **コードプレビュー**：返答に HTML/CSS/JS が含まれると、**書き上がる途中で**右ペインに結果を描画します。
  メッセージ下の「結果を見る」カードでも開けます。エージェントが書いたファイルも同じ。オフにもできます。
- **グローバル検索**：全メッセージ横断、ハイライトと該当箇所へのジャンプ付き。
- **プロンプトテンプレート**、**コマンドパレット**（Ctrl+P）、音声入力と読み上げ。
- チャットごとの統計、完了時の通知と効果音、6 種類のアクセントカラー、JSON の入出力。
- **UI は 7 言語対応**（英語・スペイン語・中国語・日本語・韓国語・アラビア語・インドネシア語）。上部バーから切り替えでき、アラビア語では右から左になります。

## 🖼 スクリーンショット

<p align="center">
  <img src="assets/shots/01-chat.png" width="820" alt="チャットと右側のライブプレビューペイン">
  <br><sub>チャットと右側のライブプレビューペイン</sub>
</p>
<p align="center">
  <img src="assets/shots/02-asistente.png" width="820" alt="初回ウィザード：プロバイダー選択、キー入力、接続テスト">
  <br><sub>初回ウィザード：プロバイダー選択、キー入力、接続テスト</sub>
</p>
<p align="center">
  <img src="assets/shots/03-panel.png" width="820" alt="コントロールパネル：使用量、コスト、日次アクティビティ、モデル別集計">
  <br><sub>コントロールパネル：使用量、コスト、日次アクティビティ、モデル別集計</sub>
</p>
<p align="center">
  <img src="assets/shots/04-movil.png" width="820" alt="モバイル表示。同じアプリを LAN 経由で">
  <br><sub>モバイル表示。同じアプリを LAN 経由で</sub>
</p>

## 📊 コントロールパネル

左下の **Panel** ボタン、または **Ctrl+D**。5 つのタブがあります：

**概要** — 入力/出力トークン、呼び出し回数、推定コスト、ツール使用、日次アクティビティグラフ、モデル別テーブル、
  時間帯×曜日のヒートマップ。7 / 30 / 90 日 / 1 年の範囲切替と **CSV 出力**。
**タスク** — エージェントにバックグラウンドで仕事を依頼（タイトル、指示、フォルダー、ツール、モデル）し、
  状態・出力・トークンをライブで確認。エージェントモードが必要です。
**プロジェクト** — ファイルブラウザーと**プレビュー**：`.html` は相対 CSS/JS ごとライブ描画、画像はそのまま、
  コードはテキストとして表示。
**ログ** — アクティビティ履歴（チャット作成、チャット/エージェントのターン、タスク、アプリ起動）。種類で絞り込み可能。
**LAN** — スマホや別の PC から開くためのアドレスとトークン。

## 🔑 プロバイダーとキー

初回起動時、または **設定 → プロバイダーとキー** から、プロバイダーを選びキーを貼り付けて **接続テスト** を押します。
アプリは実際のモデル一覧を取得し、最小のリクエストで動作を確認します。

設定はあなたのマシンに、あなただけが読める形で保存されます：

```
~/.config/nexus/config.json      (0600)
```

```json
{ "default": { "provider": "openai", "model": "gpt-4o-mini" },
  "providers": { "openai": { "base_url": "https://api.openai.com/v1", "api_key": "sk-..." } } }
```

一般的な環境変数も使えます（`OPENAI_API_KEY`、`OPENROUTER_API_KEY`、`GROQ_API_KEY`、`DEEPSEEK_API_KEY` など）。
サンプルカタログは `providers.json`。アプリから任意のサービスを base URL 付きで追加できます
（LiteLLM、vLLM、自前のゲートウェイ、Ollama の `http://127.0.0.1:11434/v1` など）。

## 🤖 エージェントモード（任意）

**エージェントモード**では NEXUS が [Hermes](https://hermes-agent.nousresearch.com) を実行し、実際のツールを使います：
ファイルの読み書き、コマンド実行、ブラウジング。未インストールの場合はウィザードのボタンから導入できます
（`設定 → プロバイダーとキー → エージェントモード`）。Hermes がなくても NEXUS は同じように使え、エージェントボタンが隠れるだけです。

上部の **Chat / Agent** ピルで切り替えます。チャットモードはモデルが直接答えるモードで、添付（テキストと画像）はモデルに渡されます。
画像には視覚対応モデルが必要です。

## 📱 LAN アクセス（スマホ、タブレット、別の PC）

サーバーはネットワーク全体（`0.0.0.0`）で待ち受けます。このマシン以外からは Panel → LAN に表示される**トークン**が必要です：

```
http://あなたのIP:8765/login?token=トークン
```

一度アクセスすると Cookie が保存され、以降は尋ねられません。トークンがない外部リクエストは **401** を返します。
ネットワーク公開をやめるには `NEXUS_LAN=0 python3 server.py`。Linux の ufw では `sudo bash lan-allow.sh` がサブネット向けにポートを開けます。

スマホでは自動的にモバイル表示になります：ドロワー履歴、大きめの操作部、ボトムシート、セーフエリア対応。
ヒント：Chrome の *⋮ → ホーム画面に追加* で全画面アプリのように使えます。

## ⌨ ショートカット

```text
    Ctrl+N     新規チャット         Ctrl+P    コマンドパレット
    Ctrl+K     モデル変更           Ctrl+F    チャットとメッセージを検索
    Ctrl+D     コントロールパネル   Ctrl+B    履歴の表示/非表示
    Alt+↑ / ↓  前 / 次のチャット
    Alt+1…9    n 番目のチャットへ
    Enter      送信（Shift+Enter で改行）
    ?          ヘルプ               Esc       ウィンドウを閉じる / 読み上げ停止
```

## 🗂 構成

```text
    nexus/
      server.py            バックエンド（Python 標準ライブラリのみ）
      providers.json       プロバイダーのサンプルカタログ
      prompts.json         サンプルプロンプト集（25 件）
      app/                 フロントエンド（HTML + CSS + JS、依存なし）
      assets/shots/        この README の画像
      run.sh / stop.sh     起動と停止
      install-desktop.sh   メニューとデスクトップのショートカット
      lan-allow.sh         ufw でポートを開放（任意）

    ~/.config/nexus/config.json        プロバイダー、キー、既定モデル
    ~/.config/nexus/models_cache.json  取得したモデル一覧
    ~/.local/share/nexus/nexus.db      チャット、メッセージ、テンプレート（SQLite）
    ~/.local/share/nexus/server.log    バックエンドのログ

環境変数：`NEXUS_PORT`（8765）、`NEXUS_DATA`、`NEXUS_CONFIG_DIR`、`NEXUS_LAN=0`。
```

## 📝 注意

- キーは**リポジトリに含まれません**：あなたのマシン（`~/.config/nexus/config.json`、権限 0600）か環境変数にあります。
- エージェントモードはチャットの作業フォルダーでコマンドを実行します。自分のマシンなので慎重に扱ってください。
- Python 3.9+ とブラウザーが必要です。Linux（Mint/Ubuntu）で動作確認済み。macOS と Windows/WSL でも同じです
    （その場合は `python3 server.py` を実行し、ブラウザーを手動で開いてください）。
- UI は **7 言語**対応（英語・スペイン語・中国語・日本語・韓国語・アラビア語・インドネシア語）。上部バーまたは設定で切り替えられ、アラビア語では右から左のレイアウトになります。

## 📄 ライセンス

MIT — [LICENSE](LICENSE) を参照。
