# Google Cloud デプロイガイド

このガイドでは、業務管理システムをGoogle Cloud Runにデプロイし、SupabaseとGitHubと連携する方法を説明します。

## 📋 目次

1. [前提条件](#前提条件)
2. [Supabaseのセットアップ](#supabaseのセットアップ)
3. [Google Cloudのセットアップ](#google-cloudのセットアップ)
4. [GitHub連携の設定](#github連携の設定)
5. [デプロイ手順](#デプロイ手順)
6. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

以下のアカウントとツールが必要です：

- ✅ Google Cloud Platform (GCP) アカウント
- ✅ Supabase アカウント
- ✅ GitHub アカウント
- ✅ Google Cloud SDK (gcloud) がインストール済み
- ✅ Docker がインストール済み（ローカルテスト用）

---

## Supabaseのセットアップ

### 1. Supabaseプロジェクトの作成

1. [Supabase](https://supabase.com) にアクセスしてアカウントを作成
2. 「New Project」をクリック
3. プロジェクト名、データベースパスワード、リージョンを設定
4. プロジェクトを作成（数分かかります）

### 2. データベーステーブルの作成

SupabaseのSQL Editorで以下のSQLを実行してテーブルを作成します：

```sql
-- 利用者マスタテーブル
CREATE TABLE users_master (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    classification TEXT NOT NULL DEFAULT '放課後等デイサービス',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 日報データテーブル
CREATE TABLE daily_reports (
    id SERIAL PRIMARY KEY,
    業務日 DATE,
    記入スタッフ名 TEXT,
    担当利用者名 TEXT,
    利用者区分 TEXT,
    体温 TEXT,
    バイタルその他 TEXT,
    気分顔色 TEXT,
    学習内容タグ TEXT,
    学習内容詳細 TEXT,
    自由遊びタグ TEXT,
    自由遊び詳細 TEXT,
    集団遊びタグ TEXT,
    集団遊び詳細 TEXT,
    食事状態 TEXT,
    食事詳細 TEXT,
    水分補給量 INTEGER,
    排泄記録 TEXT,
    特記事項 TEXT,
    送迎区分 TEXT,
    使用車両 TEXT,
    送迎児童名 TEXT,
    送迎人数 INTEGER,
    到着時刻 TEXT,
    退所時間 TEXT,
    ヒヤリハット事故 TEXT,
    ヒヤリハット詳細 TEXT,
    発生場所 TEXT,
    対象者 TEXT,
    事故発生の状況 TEXT,
    経過 TEXT,
    事故原因 TEXT,
    対策 TEXT,
    その他 TEXT,
    申し送り事項 TEXT,
    備品購入要望 TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- スタッフアカウントテーブル
CREATE TABLE staff_accounts (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE
);

-- 朝礼議事録テーブル
CREATE TABLE morning_meetings (
    id SERIAL PRIMARY KEY,
    日付 DATE NOT NULL,
    記入スタッフ名 TEXT,
    議題・内容 TEXT,
    決定事項 TEXT,
    共有事項 TEXT,
    その他メモ TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- タグマスタテーブル
CREATE TABLE tags_master (
    id SERIAL PRIMARY KEY,
    tag_type TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tag_type, tag_name)
);

-- インデックスの作成（パフォーマンス向上）
CREATE INDEX idx_daily_reports_業務日 ON daily_reports(業務日);
CREATE INDEX idx_morning_meetings_日付 ON morning_meetings(日付);
CREATE INDEX idx_users_master_active ON users_master(active);
CREATE INDEX idx_staff_accounts_user_id ON staff_accounts(user_id);
```

### 3. Supabase認証情報の取得

1. Supabaseプロジェクトの「Settings」→「API」に移動
2. 以下の情報をメモ：
   - **Project URL** (例: `https://xxxxx.supabase.co`)
   - **anon public key** (API Key)

---

## Google Cloudのセットアップ

### 1. Google Cloudプロジェクトの作成

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトを作成（または既存のプロジェクトを使用）
gcloud projects create YOUR_PROJECT_ID --name="Business Management"

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# 請求先アカウントをリンク（初回のみ）
# Google Cloud Consoleで請求先アカウントを設定してください
```

### 2. 必要なAPIの有効化

```bash
# Cloud Run APIを有効化
gcloud services enable run.googleapis.com

# Cloud Build APIを有効化
gcloud services enable cloudbuild.googleapis.com

# Artifact Registry APIを有効化
gcloud services enable artifactregistry.googleapis.com

# Container Registry APIを有効化（必要に応じて）
gcloud services enable containerregistry.googleapis.com
```

### 3. Artifact Registryリポジトリの作成

```bash
# Artifact Registryリポジトリを作成
gcloud artifacts repositories create business-management \
    --repository-format=docker \
    --location=asia-northeast1 \
    --description="Business Management Application Docker Images"
```

### 4. サービスアカウントの作成と権限設定

```bash
# サービスアカウントを作成
gcloud iam service-accounts create github-actions-sa \
    --display-name="GitHub Actions Service Account"

# 必要な権限を付与
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"

# サービスアカウントキーを生成
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**重要**: `github-actions-key.json` ファイルは機密情報です。GitHub Secretsに追加する前に安全に保管してください。

---

## GitHub連携の設定

### 1. GitHubリポジトリの準備

```bash
# リポジトリを初期化（まだの場合）
git init

# ファイルを追加
git add .

# 初回コミット
git commit -m "Initial commit: Google Cloud deployment setup"

# GitHubリポジトリを作成し、リモートを追加
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# プッシュ
git branch -M main
git push -u origin main
```

### 2. GitHub Secretsの設定

GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」で以下のSecretsを追加：

| Secret名 | 説明 | 取得方法 |
|---------|------|---------|
| `GCP_PROJECT_ID` | Google CloudプロジェクトID | `gcloud config get-value project` |
| `GCP_SA_KEY` | サービスアカウントキー（JSON） | `github-actions-key.json`の内容全体 |
| `SUPABASE_URL` | SupabaseプロジェクトURL | Supabase Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase API Key | Supabase Settings → API → anon public key |
| `GROK_API_KEY` | Grok APIキー（オプション） | Grok API設定から取得 |
| `GEMINI_API_KEY` | Gemini APIキー（オプション） | Google AI Studioから取得 |

**GCP_SA_KEYの設定方法**:
1. `github-actions-key.json`ファイルを開く
2. ファイルの内容全体をコピー
3. GitHub Secretsの`GCP_SA_KEY`に貼り付け

---

## デプロイ手順

### 方法1: GitHub Actionsを使用した自動デプロイ（推奨）

1. **コードをプッシュ**
   ```bash
   git add .
   git commit -m "Deploy to Google Cloud Run"
   git push origin main
   ```

2. **GitHub Actionsでデプロイを確認**
   - GitHubリポジトリの「Actions」タブを開く
   - ワークフローが実行されていることを確認
   - デプロイが完了すると、Cloud RunのURLが表示されます

3. **デプロイURLの確認**
   ```bash
   gcloud run services describe business-management \
       --region=asia-northeast1 \
       --format='value(status.url)'
   ```

### 方法2: Google Cloud Buildを使用したデプロイ

1. **Cloud Buildトリガーの作成**
   ```bash
   gcloud builds triggers create github \
       --repo-name=YOUR_REPO_NAME \
       --repo-owner=YOUR_USERNAME \
       --branch-pattern="^main$" \
       --build-config=cloudbuild.yaml \
       --substitutions=_SUPABASE_URL="YOUR_SUPABASE_URL",_SUPABASE_KEY="YOUR_SUPABASE_KEY",_GROK_API_KEY="YOUR_GROK_API_KEY",_GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
   ```

2. **手動でビルドを実行**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

### 方法3: ローカルから直接デプロイ

```bash
# Dockerイメージをビルド
docker build -t asia-northeast1-docker.pkg.dev/YOUR_PROJECT_ID/business-management/app:latest .

# Artifact Registryにプッシュ
docker push asia-northeast1-docker.pkg.dev/YOUR_PROJECT_ID/business-management/app:latest

# Cloud Runにデプロイ
gcloud run deploy business-management \
    --image asia-northeast1-docker.pkg.dev/YOUR_PROJECT_ID/business-management/app:latest \
    --region asia-northeast1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars SUPABASE_URL="YOUR_SUPABASE_URL",SUPABASE_KEY="YOUR_SUPABASE_KEY",GROK_API_KEY="YOUR_GROK_API_KEY",GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

---

## 環境変数の設定

Cloud Runサービスの環境変数は、以下の方法で設定できます：

### 方法1: gcloudコマンドで設定

```bash
gcloud run services update business-management \
    --region=asia-northeast1 \
    --update-env-vars SUPABASE_URL="YOUR_SUPABASE_URL",SUPABASE_KEY="YOUR_SUPABASE_KEY"
```

### 方法2: Google Cloud Consoleで設定

1. Cloud Runサービスのページを開く
2. 「EDIT & DEPLOY NEW REVISION」をクリック
3. 「Variables & Secrets」タブを開く
4. 環境変数を追加

### 方法3: GitHub Actionsワークフローで設定

`.github/workflows/deploy-gcp.yml`ファイルの`--set-env-vars`オプションを編集

---

## トラブルシューティング

### デプロイが失敗する

1. **ログを確認**
   ```bash
   gcloud builds list --limit=5
   gcloud builds log BUILD_ID
   ```

2. **よくある原因**
   - Dockerイメージのビルドエラー
   - 環境変数が正しく設定されていない
   - サービスアカウントの権限不足

### Supabase接続エラー

1. **環境変数を確認**
   ```bash
   gcloud run services describe business-management \
       --region=asia-northeast1 \
       --format='value(spec.template.spec.containers[0].env)'
   ```

2. **Supabaseのテーブルが正しく作成されているか確認**
   - Supabase Dashboard → Table Editorで確認

3. **Row Level Security (RLS) の設定**
   - Supabaseでは、デフォルトでRLSが有効になっている場合があります
   - 必要に応じてRLSポリシーを設定するか、無効化してください

### GitHub Actionsが失敗する

1. **Secretsが正しく設定されているか確認**
   - GitHubリポジトリのSettings → Secrets and variables → Actions

2. **サービスアカウントキーの形式を確認**
   - JSONファイルの内容全体をコピーしているか確認

3. **ワークフローログを確認**
   - GitHub Actionsのログでエラー詳細を確認

### アプリケーションが起動しない

1. **Cloud Runのログを確認**
   ```bash
   gcloud run services logs read business-management \
       --region=asia-northeast1 \
       --limit=50
   ```

2. **ポート番号を確認**
   - Cloud Runは`PORT`環境変数を自動的に設定します
   - Dockerfileで`${PORT:-8080}`を使用していることを確認

### データが保存されない

1. **Supabase接続を確認**
   - アプリケーションのログで「Supabase連携が有効です」というメッセージを確認

2. **Supabaseのテーブル構造を確認**
   - テーブルが正しく作成されているか確認
   - カラム名が正しいか確認（日本語カラム名を使用している場合）

---

## コスト見積もり

### Google Cloud Run

- **無料枠**: 月200万リクエスト、360,000 GB秒、180,000 vCPU秒
- **超過分**: 
  - CPU: $0.00002400/vCPU秒
  - メモリ: $0.00000250/GiB秒
  - リクエスト: $0.40/100万リクエスト

### Supabase

- **無料プラン**: 
  - 500MBデータベース
  - 2GBファイルストレージ
  - 50,000月間アクティブユーザー
- **Proプラン**: $25/月（より多くのリソース）

**推奨**: 小規模な運用であれば無料プランで十分です。

---

## セキュリティのベストプラクティス

1. **環境変数の管理**
   - 機密情報はGitHub SecretsまたはGoogle Secret Managerを使用
   - コードに直接書かない

2. **SupabaseのRow Level Security (RLS)**
   - 必要に応じてRLSポリシーを設定してデータアクセスを制限

3. **Cloud Runの認証**
   - 必要に応じて`--no-allow-unauthenticated`を使用して認証を有効化

4. **定期的なバックアップ**
   - Supabaseのバックアップ機能を使用
   - または、定期的にデータをエクスポート

---

## 次のステップ

- [ ] カスタムドメインの設定
- [ ] SSL証明書の設定
- [ ] モニタリングとアラートの設定
- [ ] 自動スケーリングの設定
- [ ] ログ分析の設定

---

## 参考リンク

- [Google Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Supabase ドキュメント](https://supabase.com/docs)
- [GitHub Actions ドキュメント](https://docs.github.com/en/actions)
- [Streamlit デプロイガイド](https://docs.streamlit.io/deploy)

---

## サポート

問題が発生した場合：

1. ログを確認
2. このガイドのトラブルシューティングセクションを参照
3. GitHub Issuesで質問（リポジトリが公開されている場合）

