# Google Cloud デプロイ実行手順

このドキュメントは `GOOGLE_CLOUD_DEPLOY.md` の実行手順を簡潔にまとめたものです。

## 📋 実行前の確認事項

- [ ] Google Cloud Platform (GCP) アカウントを持っている
- [ ] Supabase アカウントを持っている（または作成する）
- [ ] GitHub アカウントを持っている
- [ ] Google Cloud SDK (gcloud) がインストールされている
- [ ] Docker がインストールされている（ローカルテスト用）

---

## 🚀 実行手順

### ステップ1: Google Cloud認証

```bash
gcloud auth login
```

ブラウザが開くので、Googleアカウントでログインしてください。

---

### ステップ2: 自動セットアップスクリプトの実行

```bash
# プロジェクトIDを設定（YOUR_PROJECT_IDを実際のプロジェクトIDに変更）
export GCP_PROJECT_ID=your-project-id

# セットアップスクリプトを実行
./deploy_setup.sh
```

**注意**: プロジェクトが存在しない場合は、作成するか確認されます。作成後は、Google Cloud Consoleで請求先アカウントをリンクしてください。

---

### ステップ3: Supabaseのセットアップ（手動）

1. **Supabaseプロジェクトの作成**
   - [Supabase](https://supabase.com) にアクセス
   - 「New Project」をクリック
   - プロジェクト名、データベースパスワード、リージョンを設定
   - プロジェクトを作成（数分かかります）

2. **データベーステーブルの作成**
   - Supabase Dashboard → SQL Editor を開く
   - `supabase_schema.sql` の内容をコピー＆ペースト
   - 「Run」をクリックして実行

3. **認証情報の取得**
   - Supabase Dashboard → Settings → API
   - 以下の情報をメモ：
     - **Project URL** (例: `https://xxxxx.supabase.co`)
     - **anon public key** (API Key)

---

### ステップ4: GitHub Secretsの設定（手動）

GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」で以下のSecretsを追加：

| Secret名 | 説明 | 取得方法 |
|---------|------|---------|
| `GCP_PROJECT_ID` | Google CloudプロジェクトID | `gcloud config get-value project` または `deploy_setup.sh` で設定した値 |
| `GCP_SA_KEY` | サービスアカウントキー（JSON） | `github-actions-key.json` の内容全体をコピー |
| `SUPABASE_URL` | SupabaseプロジェクトURL | Supabase Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase API Key | Supabase Settings → API → anon public key |
| `GROK_API_KEY` | Grok APIキー（オプション） | Grok API設定から取得 |
| `GEMINI_API_KEY` | Gemini APIキー（オプション） | Google AI Studioから取得 |

**GCP_SA_KEYの設定方法**:
1. `github-actions-key.json` ファイルを開く
2. ファイルの内容全体をコピー（`{` から `}` まで）
3. GitHub Secretsの `GCP_SA_KEY` に貼り付け

---

### ステップ5: デプロイ

#### 方法A: GitHub Actionsを使用した自動デプロイ（推奨）

```bash
# コードをコミット＆プッシュ
git add .
git commit -m "Deploy to Google Cloud Run"
git push origin main
```

GitHub Actionsが自動的にデプロイを実行します。
- GitHubリポジトリの「Actions」タブで進行状況を確認できます
- デプロイが完了すると、Cloud RunのURLが表示されます

#### 方法B: Google Cloud Buildを使用したデプロイ

```bash
# 環境変数を設定
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
export GROK_API_KEY="your_grok_api_key"  # オプション
export GEMINI_API_KEY="your_gemini_api_key"  # オプション

# デプロイ
gcloud builds submit --config cloudbuild.yaml \
    --substitutions=_SUPABASE_URL="$SUPABASE_URL",_SUPABASE_KEY="$SUPABASE_KEY",_GROK_API_KEY="$GROK_API_KEY",_GEMINI_API_KEY="$GEMINI_API_KEY"
```

#### 方法C: ローカルから直接デプロイ

```bash
# 環境変数を設定
export PROJECT_ID="your-project-id"
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
export GROK_API_KEY="your_grok_api_key"  # オプション
export GEMINI_API_KEY="your_gemini_api_key"  # オプション

# Dockerイメージをビルド
docker build -t asia-northeast1-docker.pkg.dev/$PROJECT_ID/business-management/app:latest .

# Artifact Registryにプッシュ
docker push asia-northeast1-docker.pkg.dev/$PROJECT_ID/business-management/app:latest

# Cloud Runにデプロイ
gcloud run deploy business-management \
    --image asia-northeast1-docker.pkg.dev/$PROJECT_ID/business-management/app:latest \
    --region asia-northeast1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars SUPABASE_URL="$SUPABASE_URL",SUPABASE_KEY="$SUPABASE_KEY",GROK_API_KEY="$GROK_API_KEY",GEMINI_API_KEY="$GEMINI_API_KEY"
```

---

### ステップ6: デプロイURLの確認

```bash
gcloud run services describe business-management \
    --region=asia-northeast1 \
    --format='value(status.url)'
```

または、Google Cloud Consoleの Cloud Run ページで確認できます。

---

## 🔍 トラブルシューティング

### gcloudコマンドが動作しない場合

```bash
# Python環境を確認
which python3

# gcloudのPython環境を設定（必要に応じて）
export CLOUDSDK_PYTHON=$(which python3)
```

### デプロイが失敗する場合

1. **ログを確認**
   ```bash
   gcloud builds list --limit=5
   gcloud builds log BUILD_ID
   ```

2. **Cloud Runのログを確認**
   ```bash
   gcloud run services logs read business-management \
       --region=asia-northeast1 \
       --limit=50
   ```

3. **環境変数を確認**
   ```bash
   gcloud run services describe business-management \
       --region=asia-northeast1 \
       --format='value(spec.template.spec.containers[0].env)'
   ```

### Supabase接続エラー

1. Supabaseのテーブルが正しく作成されているか確認
2. Row Level Security (RLS) が有効になっている場合は、ポリシーを設定するか無効化
3. 環境変数が正しく設定されているか確認

---

## 📝 次のステップ

デプロイが完了したら：

- [ ] カスタムドメインの設定（オプション）
- [ ] SSL証明書の設定（オプション）
- [ ] モニタリングとアラートの設定（オプション）
- [ ] 自動スケーリングの設定（オプション）

---

## 📚 参考資料

詳細な情報は `GOOGLE_CLOUD_DEPLOY.md` を参照してください。

