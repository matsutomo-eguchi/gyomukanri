# 放課後等デイサービス 業務管理フォーム（日報）

放課後等デイサービスのスタッフが、日々の業務内容、担当した児童の様子、送迎実績を効率的に記録・報告するためのStreamlitアプリケーションです。

## 機能概要

### 🔐 ログイン機能
- スタッフアカウントの作成・ログイン
- ログイン情報に基づく自動スタッフ名設定
- セキュアなパスワード管理

### 📋 日報入力
- **担当児童記録**: 複数名の児童の記録を同時に入力可能
  - バイタル（体温、その他）
  - 気分・顔色
  - 学習内容（タグ選択＋自由記述）
  - 自由遊び（タグ選択＋自由記述）
  - 集団遊び（タグ選択＋自由記述）
  - 食事・おやつ、水分補給、排泄記録
  - 特記事項（AI文章生成アシスト機能付き）

- **送迎業務記録**: 最大6名までの送迎記録
  - 送迎区分（迎え/送り/両方）
  - 使用車両
  - 送迎した児童名

- **業務報告・共有事項**
  - ヒヤリハット・事故報告（AI生成アシスト機能付き）
  - 申し送り事項
  - 備品購入・要望

### 📚 保存済み日報閲覧
- 過去の日報データの検索・閲覧
- 日付やスタッフ名での絞り込み
- 日報データの詳細表示

### 📝 朝礼議事録
- 朝礼の議事録作成・管理
- **音声から自動生成**: Gemini 3.0 Proを使用した音声認識機能
  - 音声ファイル（MP3, WAV, M4A, OGG, FLAC, WEBM）をアップロード
  - 自動的に議題・内容、決定事項、共有事項、メモを抽出
- 議事録の閲覧・検索機能

### 👥 利用者マスタ管理
- 利用者の追加・削除（無効化）・復元
- 利用者一覧の表示
- 日報入力画面への即座反映

### 🤖 AI文章生成アシスト
- **Grok API**: Grok-4-1-fast-reasoningモデルを使用した文章生成
  - キーワードや箇条書きから自然な日報文章を自動生成
  - 既存文章の改善・推敲機能
  - 事故報告・ヒヤリハット報告の文章生成
- **Gemini API**: Gemini 3.0 Proを使用した音声認識と議事録生成
  - 音声ファイルから朝礼議事録を自動生成

### ⚙️ 設定
- APIキー管理（Grok API、Gemini API）
- データエクスポート（CSV形式）
- 日報データの確認

## セットアップ

### 1. 必要な環境
- Python 3.8以上
- pip（Pythonパッケージマネージャー）

### 2. M3 MacBook Pro (Apple Silicon) 向けセットアップ 🍎

M3 MacBook Pro向けに最適化されたセットアップ手順です。

#### 2-1. Homebrewのインストール（未インストールの場合）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2-2. Python3のインストール

```bash
# HomebrewでPython3をインストール（ARM64最適化版）
brew install python3

# インストール確認
python3 --version
```

#### 2-3. プロジェクトのセットアップ

```bash
# プロジェクトディレクトリに移動
cd business-management

# 仮想環境の作成（ARM64最適化）
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip

# 依存パッケージのインストール（ARM64対応）
pip install -r requirements.txt
```

### 3. その他のOS向けインストール

#### Windows

```bash
# リポジトリをクローンまたはダウンロード
cd business-management

# 仮想環境の作成（推奨）
python -m venv venv

# 仮想環境の有効化
venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

#### Linux / その他のmacOS

```bash
# リポジトリをクローンまたはダウンロード
cd business-management

# 仮想環境の作成（推奨）
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定（オプション）

AI文章生成機能を使用する場合、APIキーを設定してください。

#### 方法1: 環境変数として設定
```bash
# Windows (PowerShell)
$env:GROK_API_KEY="your_api_key_here"
$env:GEMINI_API_KEY="your_gemini_api_key_here"

# Windows (CMD)
set GROK_API_KEY=your_api_key_here
set GEMINI_API_KEY=your_gemini_api_key_here

# macOS/Linux
export GROK_API_KEY="your_api_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"
```

#### 方法2: Streamlit Secrets（Streamlit Cloud使用時）
`.streamlit/secrets.toml` ファイルを作成:
```toml
GROK_API_KEY = "your_api_key_here"
GEMINI_API_KEY = "your_gemini_api_key_here"
```

#### 方法3: アプリ内設定画面
アプリ起動後、「設定」ページからAPIキーを入力できます。

**APIキーの用途**:
- **Grok API**: 日報文章生成、事故報告・ヒヤリハット報告の文章生成に使用
- **Gemini API**: 音声から朝礼議事録を自動生成する機能に使用（オプション）

### 4. アプリケーションの起動

```bash
# 仮想環境が有効化されていることを確認
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate      # Windows

# Streamlitアプリを起動
streamlit run app.py
```

ブラウザが自動的に開き、`http://localhost:8501` でアプリケーションが表示されます。

**M3 MacBook Pro向けの最適化機能**:
- ✅ Apple Silicon (ARM64) ネイティブサポート
- ✅ 高速なパフォーマンス設定（`.streamlit/config.toml`が存在する場合）

## 使い方

### 初回起動時

1. **ログイン**: 初回起動時はログインページが表示されます。新規アカウントを作成するか、既存のアカウントでログインしてください。
2. **利用者マスタ管理**で、利用する児童名を追加してください。
3. **日報入力**ページで、業務日とスタッフ名をサイドバーで設定します（ログイン済みの場合は自動設定されます）。
4. 各タブで担当児童を選択し、必要な情報を入力します。
5. 「保存」ボタンをクリックして日報を保存します。

### AI文章生成機能の使い方

#### 日報文章生成（Grok API）
1. 特記事項入力欄の上にある「AI文章作成アシスト」セクションで、キーワードや箇条書きを入力します。
2. 「✨ 文章生成」ボタンをクリックします。
3. 生成された文章を確認し、「✅ この文章を使用」ボタンで適用します。
4. 既に入力した文章を改善したい場合は、「📝 文章改善」ボタンを使用します。

#### 事故報告・ヒヤリハット報告生成（Grok API）
1. 業務報告・共有事項セクションで、事故報告またはヒヤリハット報告の入力欄を開きます。
2. 「AI文章作成アシスト」セクションで、キーワードや箇条書きを入力します。
3. 「✨ 文章生成」ボタンをクリックして、報告書形式の文章を自動生成します。

#### 朝礼議事録の音声から自動生成（Gemini API）
1. **朝礼議事録**ページの「📝 議事録入力」タブを開きます。
2. 「🎤 音声から議事録を生成」セクションで、音声ファイル（MP3, WAV, M4A, OGG, FLAC, WEBM）をアップロードします。
3. 「🎤 音声から議事録を生成」ボタンをクリックします。
4. 数分待つと、自動的に議題・内容、決定事項、共有事項、メモが抽出されます。
5. 生成された内容を確認・編集して保存します。

### データの保存場所

- 利用者マスタ: `data/users_master.json`
- 日報データ: `data/daily_reports.csv`
- タグマスタ: `data/tags_master.json`
- スタッフアカウント: `data/staff_accounts.json`
- 朝礼議事録: `data/morning_meetings.json`
- 設定ファイル: `data/config.json`
- 日報Markdownファイル: `data/reports/`
- バックアップ: `data/backups/`

### データ保護について

**重要**: このアプリケーションは、過去のデータを保護するように設計されています。

#### データ保護の仕組み

1. **既存データの保護**
   - 初期化処理は、ファイルが存在しない場合のみ実行されます
   - 既存のデータファイルは絶対に上書きされません
   - アプリ更新時も過去のデータは保持されます

2. **Git管理からの除外**
   - `data/`ディレクトリは`.gitignore`で除外されています
   - データファイルはGitリポジトリにコミットされません
   - アプリ更新時（`git pull`など）でもデータは影響を受けません

3. **バックアップ機能**
   - データ保護のため、定期的にバックアップを作成することを推奨します
   - バックアップは`data/backups/`ディレクトリに保存されます
   - 必要に応じて、バックアップからデータを復元できます

#### アプリ更新時の注意事項

- ✅ **安全**: `git pull`やアプリ更新を行っても、`data/`ディレクトリ内のデータは保持されます
- ✅ **安全**: 新しいバージョンのアプリをインストールしても、既存データは影響を受けません
- ⚠️ **注意**: `data/`ディレクトリを手動で削除した場合、データは失われます
- ⚠️ **注意**: データファイルを直接編集する場合は、事前にバックアップを取ることを推奨します

## ファイル構成

```
business-management/
├── app.py                        # メインアプリケーション
├── data_manager.py               # データ管理モジュール
├── ai_helper.py                  # AI文章生成モジュール（Grok API / Gemini API）
├── accident_report_generator.py  # 事故報告書生成モジュール
├── hiyari_hatto_generator.py     # ヒヤリハット報告書生成モジュール
├── requirements.txt              # 依存パッケージ
├── env_example.txt               # 環境変数サンプル
├── .gitignore                    # Git除外設定
├── README.md                     # このファイル
├── 仕様書.md                     # アプリケーション仕様書
├── DEPLOY.md                     # デプロイ詳細ガイド
├── DEPLOY_QUICKSTART.md          # デプロイクイックスタートガイド
├── DEPLOY_CHECKLIST.md           # デプロイチェックリスト
├── .streamlit/                   # Streamlit設定ディレクトリ（存在する場合）
│   └── config.toml               # Streamlitパフォーマンス設定
└── data/                         # データ保存ディレクトリ（自動生成）
    ├── users_master.json         # 利用者マスタ
    ├── daily_reports.csv         # 日報データ
    ├── tags_master.json          # タグマスタ
    ├── staff_accounts.json       # スタッフアカウント
    ├── morning_meetings.json      # 朝礼議事録
    ├── config.json               # 設定ファイル
    ├── reports/                  # 日報Markdownファイル
    └── backups/                  # バックアップファイル
```

## 🌐 デプロイ（インターネット上に公開）

このアプリケーションをインターネット上に公開して、チーム全体で使用できるようにする方法です。

### クイックスタート（5分でデプロイ）

**最も簡単な方法**については、[`DEPLOY_QUICKSTART.md`](DEPLOY_QUICKSTART.md) を参照してください。

### 詳細なデプロイ方法

以下のデプロイ方法が利用可能です：

- **Streamlit Cloud**（推奨・完全無料・最も簡単）
- **Railway**（無料枠あり・データ永続化可能）
- **Render**（無料枠あり・簡単）

詳細な手順は [`DEPLOY.md`](DEPLOY.md) を参照してください。

### デプロイ前の確認事項

- [ ] `requirements.txt` が最新である
- [ ] `.gitignore` に機密情報が含まれていない
- [ ] APIキーがコードに直接書かれていない

## 注意事項

- **データ保護**: アプリ更新時も過去のデータは自動的に保護されます。`data/`ディレクトリは`.gitignore`で除外されているため、Git操作でデータが失われることはありません。
- **バックアップ**: データファイル（`data/`ディレクトリ）は定期的にバックアップしてください。重要なデータの場合は、外部ストレージにもバックアップを保存することを推奨します。
- **APIキー**: APIキーは機密情報です。`.gitignore`に含まれているため、Gitリポジトリにコミットされませんが、取り扱いには注意してください。
- **セキュリティ**: 本アプリケーションはローカル環境での使用を想定しています。本番環境で使用する場合は、適切なセキュリティ対策を実施してください。
- **クラウドデプロイ時**: Streamlit Cloudではデータは一時的なストレージに保存されます。永続化が必要な場合は、RailwayやRenderの使用を検討してください。

## トラブルシューティング

### APIキーが認識されない
- 環境変数が正しく設定されているか確認してください（Grok API、Gemini APIそれぞれ）。
- アプリを再起動してください。
- 設定画面から直接APIキーを入力してみてください。
- Gemini APIを使用する場合は、`google-generativeai`パッケージがインストールされているか確認してください。

### データが保存されない
- `data/`ディレクトリへの書き込み権限があるか確認してください。
- エラーメッセージを確認してください。

### 利用者が表示されない
- 「利用者マスタ管理」で利用者が追加されているか確認してください。
- 無効化された利用者は「無効化された利用者」セクションに表示されます。

### M3 MacBook Proでのパフォーマンス問題
- `.streamlit/config.toml`が正しく配置されているか確認してください（存在する場合）。
- 仮想環境がARM64版のPythonを使用しているか確認：
  ```bash
  python3 -c "import platform; print(platform.machine())"
  # 出力が "arm64" であることを確認
  ```

### 音声から議事録が生成されない
- Gemini APIキーが正しく設定されているか確認してください。
- `google-generativeai`パッケージがインストールされているか確認してください。
- 音声ファイルの形式が対応しているか確認してください（MP3, WAV, M4A, OGG, FLAC, WEBM）。
- 音声ファイルのサイズが大きすぎる場合は、処理に時間がかかる場合があります。

## ライセンス

このプロジェクトは内部使用を目的としています。

## 更新履歴

- v2.0.0 (2025): 機能拡張版
  - ログイン機能の追加（スタッフアカウント管理）
  - 朝礼議事録機能の追加
  - 音声から議事録を自動生成する機能（Gemini 3.0 Pro）
  - 保存済み日報閲覧機能の追加
  - 事故報告書・ヒヤリハット報告書のAI生成機能
  - Gemini APIサポートの追加

- v1.1.0 (2024): M3 MacBook Pro最適化版
  - Apple Silicon (ARM64) ネイティブサポート
  - Streamlitパフォーマンス設定の追加（`.streamlit/config.toml`）

- v1.0.0 (2024): 初版リリース
  - 日報入力機能
  - 利用者マスタ管理
  - AI文章生成アシスト（Grok API）
  - 送迎業務記録

