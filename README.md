# 放課後等デイサービス 業務管理フォーム（日報）

放課後等デイサービスのスタッフが、日々の業務内容、担当した児童の様子、送迎実績を効率的に記録・報告するためのStreamlitアプリケーションです。

**✨ 最新版の特徴**:
- 🔗 **Supabaseデータベース連携**（クラウドデプロイ対応）
- 🤖 **AI文章生成**（Grok API + Gemini API）
- 🎤 **音声から議事録自動生成**
- 🚀 **GitHub Actions自動デプロイ**（Google Cloud Run）
- 📱 **クロスプラットフォーム対応**（macOS ARM64、Windows、Linux）
- 🔒 **データ保護機能強化**（自動バックアップ・整合性チェック）
- ⚡ **Python 3.13完全対応**（最新環境最適化）
- 🛠️ **デプロイ自動化スクリプト**（GitHub Secrets設定支援）

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
- **音声から自動生成**: Gemini 3 Flash Previewを使用した音声認識機能
  - 音声ファイル（MP3, WAV, M4A, OGG, FLAC, WEBM）をアップロード
  - 自動的に議題・内容、決定事項、共有事項、メモを抽出
- 議事録の閲覧・検索機能

### 👥 利用者マスタ管理
- 利用者の追加・削除（無効化）・復元
- 利用者一覧の表示
- 日報入力画面への即座反映

### 🤖 AI文章生成アシスト
- **Grok API**: xAIの最新Grokモデルを使用した文章生成
  - キーワードや箇条書きから自然な日報文章を自動生成
  - 既存文章の改善・推敲機能
  - 事故報告・ヒヤリハット報告の文章生成
  - 状況に応じた最適なモデル自動選択
- **Gemini API**: Google Geminiを使用した音声認識と議事録生成
  - 音声ファイルから朝礼議事録を自動生成
  - 複数形式の音声ファイル対応（MP3, WAV, M4A, OGG, FLAC, WEBM）

### 💾 データベース連携
- **Supabase連携**（オプション）
  - Supabase URL/Keyを設定すると、データがSupabaseデータベースに保存されます
  - ローカルファイル（`data/`ディレクトリ）とSupabaseの両方に対応
  - クラウドデプロイ時はSupabaseを使用することでデータの永続化が可能
  - 詳細は [`GOOGLE_CLOUD_DEPLOY.md`](GOOGLE_CLOUD_DEPLOY.md) を参照

### ⚙️ 設定
- APIキー管理（Grok API、Gemini API）
- Supabase連携設定（URL/Key）
- データエクスポート（CSV形式）
- 日報データの確認

## セットアップ

### 1. 必要な環境
- Python 3.9以上（推奨: Python 3.11以上、最新対応: Python 3.13）
- pip（Pythonパッケージマネージャー）
- Git（バージョン管理用、オプション）

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
$env:SUPABASE_URL="your_supabase_url"  # Supabase連携用（オプション）
$env:SUPABASE_KEY="your_supabase_key"  # Supabase連携用（オプション）

# Windows (CMD)
set GROK_API_KEY=your_api_key_here
set GEMINI_API_KEY=your_gemini_api_key_here
set SUPABASE_URL=your_supabase_url
set SUPABASE_KEY=your_supabase_key

# macOS/Linux
export GROK_API_KEY="your_api_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
```

#### 方法2: Streamlit Secrets（Streamlit Cloud使用時）
`.streamlit/secrets.toml` ファイルを作成:
```toml
GROK_API_KEY = "your_api_key_here"
GEMINI_API_KEY = "your_gemini_api_key_here"
SUPABASE_URL = "your_supabase_url"  # Supabase連携用（オプション）
SUPABASE_KEY = "your_supabase_key"  # Supabase連携用（オプション）
```

#### 方法3: アプリ内設定画面
アプリ起動後、「設定」ページからAPIキーを入力できます。

**環境変数の用途**:
- **Grok API**: 日報文章生成、事故報告・ヒヤリハット報告の文章生成に使用
- **Gemini API**: 音声から朝礼議事録を自動生成する機能に使用（オプション）
- **Supabase URL**: SupabaseプロジェクトのURL（例: `https://xxxxx.supabase.co`）
- **Supabase Key**: Supabaseプロジェクトの匿名キー（anon/public key）
  - Supabase URL/Keyを設定すると、データがSupabaseデータベースに保存されます
  - クラウドデプロイ時はSupabaseを使用することでデータの永続化が可能
  - 詳細は [`GOOGLE_CLOUD_DEPLOY.md`](GOOGLE_CLOUD_DEPLOY.md) を参照

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

#### ローカルファイルモード（デフォルト）
Supabase URL/Keyが設定されていない場合、データはローカルファイルに保存されます：

- 利用者マスタ: `data/users_master.json`
- 日報データ: `data/daily_reports.csv`
- タグマスタ: `data/tags_master.json`
- スタッフアカウント: `data/staff_accounts.json`
- 朝礼議事録: `data/morning_meetings.json`
- 設定ファイル: `data/config.json`
- 日報Markdownファイル: `data/reports/`
- バックアップ: `data/backups/`

#### Supabaseモード（推奨・Cloud Runデプロイ時は必須）
Supabase URL/Keyが設定されている場合、データはSupabaseデータベースに保存されます：

- 利用者マスタ: `users_master`テーブル
- 日報データ: `daily_reports`テーブル
- スタッフアカウント: `staff_accounts`テーブル
- 朝礼議事録: `morning_meetings`テーブル
- タグマスタ: `tags_master`テーブル
- 日別利用者記録: `daily_users`テーブル

**重要**: 
- Supabaseモードでは、ローカルの`data/`ディレクトリは使用されません。データはすべてSupabaseに保存されます。
- **Cloud Runにデプロイする場合は、Supabaseの使用を強く推奨します。** ローカルファイルストレージではデータが永続化されません。
- Supabase設定方法は `SUPABASE_SETUP.md` を参照してください。

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
├── app.py                        # メインアプリケーション（Streamlit）
├── data_manager.py               # データ管理モジュール（Supabase/ローカル両対応）
├── supabase_manager.py           # Supabase連携モジュール
├── ai_helper.py                  # AI文章生成モジュール（Grok/Gemini API）
├── accident_report_generator.py  # 事故報告書生成モジュール
├── hiyari_hatto_generator.py     # ヒヤリハット報告書生成モジュール
├── requirements.txt              # 依存パッケージ（Python 3.13対応）
├── env_example.txt               # 環境変数サンプル
├── Dockerfile                    # Google Cloud Run用Dockerfile
├── cloudbuild.yaml              # Google Cloud Build設定
├── supabase_schema.sql          # Supabaseデータベーススキーマ
├── verify_supabase.py           # Supabase接続検証スクリプト
├── .gitignore                    # Git除外設定
├── .dockerignore                 # Docker除外設定
├── README.md                     # このファイル（最新版）
├── 仕様書.md                     # アプリケーション仕様書
├── ヒヤリハット.html             # ヒヤリハット報告書テンプレート
├── 事故報告書.html               # 事故報告書テンプレート
├── DEPLOY.md                     # デプロイ詳細ガイド
├── DEPLOY_QUICKSTART.md          # デプロイクイックスタートガイド
├── DEPLOY_CHECKLIST.md           # デプロイチェックリスト
├── DEPLOY_STEPS.md               # デプロイ手順詳細
├── GOOGLE_CLOUD_DEPLOY.md        # Google Cloudデプロイガイド
├── DATA_PROTECTION.md            # データ保護ガイド
├── SUPABASE_SETUP.md             # Supabase設定詳細ガイド
├── SUPABASE_SETUP_QUICK.md       # Supabaseクイックスタートガイド
├── SETUP_SUPABASE.sh             # Supabase自動セットアップスクリプト
├── GITHUB_SECRETS_SETUP.md       # GitHub Secrets設定ガイド
├── GITHUB_SECRETS_VALUES.md      # GitHub Secrets値の説明
├── deploy_setup.sh               # デプロイセットアップスクリプト
├── setup_github_secrets.sh       # GitHub Secrets設定スクリプト
├── setup_github_secrets_cli.sh   # GitHub Secrets設定CLIスクリプト
├── run_github_secrets_setup.sh   # GitHub Secrets設定実行スクリプト
├── SETUP_SUPABASE.sh             # Supabase自動セットアップスクリプト
├── github-actions-key.json       # GitHub Actions設定用キー
├── .github/                      # GitHub Actions設定
│   └── workflows/
│       └── deploy-gcp.yml        # Google Cloud Run自動デプロイワークフロー
├── .streamlit/                   # Streamlit設定ディレクトリ（存在する場合）
│   └── config.toml               # Streamlitパフォーマンス設定
├── venv/                         # Python仮想環境（自動生成）
├── __pycache__/                  # Pythonキャッシュ（自動生成）
├── streamlit.log                 # Streamlitログファイル
├── streamlit_output.log          # Streamlit出力ログ
└── data/                         # データ保存ディレクトリ（自動生成、Supabase使用時は未使用）
    ├── users_master.json         # 利用者マスタ
    ├── daily_reports.csv         # 日報データ
    ├── daily_users.json          # 日別利用者記録
    ├── tags_master.json          # タグマスタ
    ├── staff_accounts.json       # スタッフアカウント
    ├── morning_meetings.json     # 朝礼議事録
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

- **Google Cloud Run**（推奨・Supabase連携・GitHub Actions CI/CD）⭐ **推奨**
  - 本番環境向けの堅牢なデプロイ
  - Supabaseによるデータベース永続化
  - GitHub Actionsによる自動デプロイ（mainブランチへのpushで自動デプロイ）
  - デプロイ前にSupabase接続テストを自動実行
  - スケーラブルで高可用性
  - 詳細は [`GOOGLE_CLOUD_DEPLOY.md`](GOOGLE_CLOUD_DEPLOY.md) を参照
  - GitHub Secrets設定方法は [`GITHUB_SECRETS_SETUP.md`](GITHUB_SECRETS_SETUP.md) を参照
- **Streamlit Cloud**（完全無料・最も簡単）
  - GitHubと連携するだけで自動デプロイ
  - データは一時的なストレージに保存（再起動で消える可能性あり）
- **Railway**（無料枠あり・データ永続化可能）
  - シンプルで高速
  - データ永続化可能
- **Render**（無料枠あり・簡単）
  - 無料枠あり、設定が簡単

詳細な手順は [`DEPLOY.md`](DEPLOY.md) を参照してください。

### Supabase連携について

クラウドデプロイ時は、データの永続化のためにSupabaseの使用を強く推奨します：

1. **Supabaseプロジェクトの作成**: [Supabase](https://supabase.com) でプロジェクトを作成
2. **データベーススキーマの設定**: `supabase_schema.sql` をSupabaseのSQL Editorで実行
3. **環境変数の設定**: 
   - ローカル実行時: 環境変数またはアプリ内設定画面で設定
   - Cloud Runデプロイ時: GitHub Secretsに設定（`SUPABASE_URL`、`SUPABASE_KEY`）
4. **データの自動保存**: 設定後、すべてのデータがSupabaseに自動保存されます
5. **接続テスト**: `verify_supabase.py` を実行して設定を確認できます

詳細は [`GOOGLE_CLOUD_DEPLOY.md`](GOOGLE_CLOUD_DEPLOY.md) の「Supabaseのセットアップ」セクションを参照してください。

### GitHub Actionsによる自動デプロイ（Google Cloud Run）⭐ **推奨**

mainブランチにpushすると、GitHub Actionsが自動的にデプロイを実行します。

#### 必要なGitHub Secrets

以下のSecretsをGitHubリポジトリに設定する必要があります：

- **GCP_PROJECT_ID**: Google CloudプロジェクトID
- **GCP_SA_KEY**: Google Cloudサービスアカウントキー（JSON形式）
- **SUPABASE_URL**: SupabaseプロジェクトURL（**推奨・必須**）
- **SUPABASE_KEY**: Supabase匿名キー（**推奨・必須**）
- **GROK_API_KEY**: Grok APIキー（オプション）
- **GEMINI_API_KEY**: Gemini APIキー（オプション）

詳細な設定方法は [`GITHUB_SECRETS_SETUP.md`](GITHUB_SECRETS_SETUP.md) を参照してください。

#### 自動デプロイの流れ

1. mainブランチにコードをpush
2. GitHub Actionsが自動的に以下を実行：
   - **Supabase接続テスト**（YAML構文修正済み、設定されている場合）
   - 必要なテーブルアクセス確認（users_master, daily_reports, staff_accounts, morning_meetings, tags_master, daily_users）
   - Dockerイメージのビルド（asia-northeast1リージョン）
   - Google Cloud Runへのデプロイ（環境変数自動設定）
3. デプロイ完了後、Cloud RunのURLが表示されます

#### 最近の改善点（2025年1月）

- ✅ **YAML構文エラー修正**: GitHub Actionsワークフローで発生していたヒアドキュメントの構文エラーを修正
- ✅ **Supabase接続テスト強化**: デプロイ前に全テーブルへのアクセスを自動検証
- ✅ **RLS設定確認**: Row Level Securityが適切に無効化されているか自動チェック

### デプロイ前の確認事項

- [ ] `requirements.txt` が最新である
- [ ] `.gitignore` に機密情報が含まれていない
- [ ] APIキーがコードに直接書かれていない
- [ ] GitHub Secretsが正しく設定されている（Cloud Runデプロイの場合）
- [ ] Supabaseスキーマが適用されている（Supabase使用の場合）

## 注意事項

### ⚠️ 重要なお知らせ（2026年1月）

- **Supabase推奨**: クラウドデプロイ時は**必ずSupabaseを使用してください**。ローカルファイルストレージではデータが永続化されません。
- **GitHub Actions修正**: ワークフローで発生していたYAML構文エラーは修正済みです。最新版の`.github/workflows/deploy-gcp.yml`を使用してください。
- **Python 3.13対応**: 最新版のPython 3.13で完全動作確認済みです。ARM64 Macや最新環境での使用を推奨します。

### データ管理

- **データ保護**: アプリ更新時も過去のデータは自動的に保護されます。`data/`ディレクトリは`.gitignore`で除外されているため、Git操作でデータが失われることはありません。
- **自動バックアップ**: アプリケーション起動時に、既存データがある場合は自動的にバックアップを作成します（24時間以内にバックアップが作成されていない場合のみ）。※ローカルファイルモードのみ
- **データマイグレーション**: スキーマバージョン管理により、データ形式が変更されても既存データを保持します。
- **データ整合性チェック**: 起動時にデータファイルの整合性を確認し、破損が検出された場合は最新のバックアップから自動的に復元を試みます。※ローカルファイルモードのみ

### Supabase連携（推奨）

- **クラウドデプロイ必須**: Supabase URL/Keyを設定すると、データはSupabaseデータベースに保存されます。**Google Cloud Runデプロイ時はSupabaseの使用が必須です。**
- **設定方法**: `SUPABASE_SETUP_QUICK.md`（クイックスタート）または `SUPABASE_SETUP.md`（詳細）を参照してください。
- **接続テスト**: `verify_supabase.py` を使用してSupabase設定を確認できます。
- **RLS設定**: SupabaseのテーブルでRow Level Securityが無効化されていることを確認してください。

### セキュリティ・運用

- **APIキー**: APIキーは機密情報です。`.gitignore`に含まれているため、Gitリポジトリにコミットされませんが、取り扱いには注意してください。
- **セキュリティ**: 本アプリケーションはローカル環境での使用を想定しています。本番環境で使用する場合は、適切なセキュリティ対策を実施してください。
- **バックアップ**: 重要なデータの場合は、外部ストレージにもバックアップを保存することを推奨します。詳細は`DATA_PROTECTION.md`を参照してください。
- **環境変数**: APIキーなどの機密情報は環境変数またはStreamlit Secretsで管理してください。

## Supabase設定（Cloud Runデプロイ時推奨）

Cloud Runにデプロイする場合、データの永続化のためにSupabaseの使用を強く推奨します。

詳細な設定方法は **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)** を参照してください。

### クイックスタート

1. [Supabase](https://supabase.com/)でプロジェクトを作成
2. `supabase_schema.sql` をSupabase SQL Editorで実行
3. GitHub Secretsに以下を設定:
   - `SUPABASE_URL`: SupabaseプロジェクトURL
   - `SUPABASE_KEY`: Supabase anon public key
4. デプロイを実行

### 接続テスト

```bash
# 環境変数を設定
export SUPABASE_URL='https://xxxxx.supabase.co'
export SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

# 検証スクリプトを実行
python3 verify_supabase.py
```

## トラブルシューティング

### GitHub Actionsワークフローエラー

#### YAML構文エラー（Invalid workflow file）
- **症状**: `You have an error in your yaml syntax on line 143` などのエラー
- **原因**: ヒアドキュメント内のPythonコードのインデントが不正
- **解決**: ワークフロー内のPythonスクリプト部分がrunステップのインデントレベルに統一されているか確認
- **最新状況**: この問題は修正済み。ヒアドキュメントを適切な形式に変更

#### Supabase接続テストエラー
- **症状**: `python3 -c "` で始まるエラー
- **原因**: シェルのヒアドキュメント構文エラー
- **解決**: ワークフローが最新版に更新されているか確認
- **確認方法**: `.github/workflows/deploy-gcp.yml` の76行目付近を確認

### Supabase接続エラー

- **クイック診断**: `SUPABASE_SETUP_QUICK.md` を参照してください
- **詳細診断**: `SUPABASE_SETUP.md` のトラブルシューティングセクションを参照してください
- **自動検証スクリプト**:
  ```bash
  # 環境変数を設定
  export SUPABASE_URL='https://xxxxx.supabase.co'
  export SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

  # 検証スクリプトを実行
  python3 verify_supabase.py
  ```
- **GitHub Actionsログ確認**: デプロイ時のSupabase接続テスト結果を確認できます
- **RLS設定確認**: SupabaseダッシュボードでRLSが無効化されているか確認

### APIキーが認識されない
- 環境変数が正しく設定されているか確認してください（Grok API、Gemini APIそれぞれ）。
- アプリを再起動してください。
- 設定画面から直接APIキーを入力してみてください。
- Gemini APIを使用する場合は、`google-generativeai`パッケージがインストールされているか確認してください。

### データが保存されない
- **ローカルファイルモードの場合**:
  - `data/`ディレクトリへの書き込み権限があるか確認してください。
  - エラーメッセージを確認してください。
- **Supabaseモードの場合**:
  - Supabase URL/Keyが正しく設定されているか確認してください。
  - Supabaseプロジェクトがアクティブか確認してください。
  - SupabaseのSQL Editorでテーブルが作成されているか確認してください（`supabase_schema.sql`を実行）。
  - Supabaseのログを確認してください。

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

- v2.2.0 (2026年1月): 機能安定化・ドキュメント充実版
  - Supabase接続テストの自動化スクリプト強化
  - GitHub Secrets設定の自動化スクリプト追加
  - データ保護機能の強化
  - デプロイ関連ドキュメントの拡充
  - Python 3.13完全対応

- v2.1.1 (2025年1月): GitHub Actionsワークフロー修正版
  - GitHub Actions YAML構文エラーの修正（ヒアドキュメント形式統一）
  - Supabase接続テストの安定化
  - デプロイプロセスの信頼性向上
  - Python 3.13対応確認

- v2.1.0 (2025年1月): Supabase連携・クラウドデプロイ対応版
  - Supabaseデータベース連携機能の追加
  - Google Cloud Runデプロイ対応（Dockerfile、cloudbuild.yaml）
  - GitHub Actions CI/CD自動デプロイ機能
  - デプロイ前のSupabase接続テスト自動実行
  - データ保存方法の選択（ローカルファイル / Supabase）
  - クラウドデプロイ時のデータ永続化対応
  - Supabase接続検証スクリプト（verify_supabase.py）の追加
  - Supabaseクイックスタートガイドの追加

- v2.0.0 (2025): 機能拡張版
  - ログイン機能の追加（スタッフアカウント管理）
  - 朝礼議事録機能の追加
  - 音声から議事録を自動生成する機能（Gemini API）
  - 保存済み日報閲覧機能の追加
  - 事故報告書・ヒヤリハット報告書のAI生成機能
  - Gemini APIサポートの追加
  - 日別利用者記録機能の追加

- v1.1.0 (2024): M3 MacBook Pro最適化版
  - Apple Silicon (ARM64) ネイティブサポート
  - Streamlitパフォーマンス設定の追加（`.streamlit/config.toml`）

- v1.0.0 (2024): 初版リリース
  - 日報入力機能
  - 利用者マスタ管理
  - AI文章生成アシスト（Grok API）
  - 送迎業務記録

