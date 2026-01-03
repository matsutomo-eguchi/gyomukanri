# GitHub Secrets設定ガイド

このガイドでは、GitHub Actionsで使用するSecretsを設定する方法を説明します。

## 📋 設定するSecrets一覧

| Secret名 | 値 | 必須/オプション |
|---------|-----|----------------|
| `GCP_PROJECT_ID` | `gemini-gijiroku-py` | 必須 |
| `GCP_SA_KEY` | `github-actions-key.json`の内容全体 | 必須 |
| `SUPABASE_URL` | Supabase Settings → API → Project URL | 必須 |
| `SUPABASE_KEY` | Supabase Settings → API → anon public key | 必須 |
| `GROK_API_KEY` | Grok APIキー | オプション |
| `GEMINI_API_KEY` | Gemini APIキー | オプション |

---

## 🚀 設定方法

### 方法1: GitHub CLIを使用（推奨）

#### 1. GitHub CLIのインストール

```bash
# macOS (Homebrew)
brew install gh

# または、公式インストーラーを使用
# https://cli.github.com/
```

#### 2. GitHub CLIにログイン

```bash
gh auth login
```

ブラウザが開くので、GitHubアカウントでログインしてください。

#### 3. Secretsを設定

```bash
# プロジェクトディレクトリに移動
cd /Users/matsutomoeguchi/Downloads/my.python/business-management

# GCP_PROJECT_IDを設定
gh secret set GCP_PROJECT_ID --body "gemini-gijiroku-py"

# GCP_SA_KEYを設定（JSONファイルから）
gh secret set GCP_SA_KEY < github-actions-key.json

# SUPABASE_URLを設定（対話的に入力）
gh secret set SUPABASE_URL

# SUPABASE_KEYを設定（対話的に入力）
gh secret set SUPABASE_KEY

# オプション: GROK_API_KEYを設定
gh secret set GROK_API_KEY

# オプション: GEMINI_API_KEYを設定
gh secret set GEMINI_API_KEY
```

#### 4. 設定の確認

```bash
gh secret list
```

---

### 方法2: Web UIを使用

#### 1. GitHubリポジトリにアクセス

https://github.com/matsutomo-eguchi/----2

#### 2. Settingsページを開く

1. リポジトリページの上部にある「Settings」タブをクリック
2. 左メニューから「Secrets and variables」→「Actions」を選択

#### 3. Secretsを追加

「New repository secret」ボタンをクリックして、以下のSecretsを追加してください：

##### GCP_PROJECT_ID

- **Name**: `GCP_PROJECT_ID`
- **Value**: `gemini-gijiroku-py`
- 「Add secret」をクリック

##### GCP_SA_KEY

- **Name**: `GCP_SA_KEY`
- **Value**: `github-actions-key.json` ファイルの内容全体をコピー＆ペースト
  ```json
  {
    "type": "service_account",
    "project_id": "gemini-gijiroku-py",
    "private_key_id": "b9daa9f6938900ca0c079e8731bd0f5de2082d31",
    "private_key": "-----BEGIN PRIVATE KEY-----\n...",
    "client_email": "github-actions-sa@gemini-gijiroku-py.iam.gserviceaccount.com",
    ...
  }
  ```
- 「Add secret」をクリック

**重要**: JSON全体をコピーしてください（`{` から `}` まで）

##### SUPABASE_URL

- **Name**: `SUPABASE_URL`
- **Value**: Supabase Dashboard → Settings → API → Project URL
  - 例: `https://xxxxx.supabase.co`
- 「Add secret」をクリック

##### SUPABASE_KEY

- **Name**: `SUPABASE_KEY`
- **Value**: Supabase Dashboard → Settings → API → anon public key
- 「Add secret」をクリック

##### GROK_API_KEY（オプション）

- **Name**: `GROK_API_KEY`
- **Value**: Grok APIキー（AI文章生成機能を使用する場合）
- 「Add secret」をクリック

##### GEMINI_API_KEY（オプション）

- **Name**: `GEMINI_API_KEY`
- **Value**: Gemini APIキー（音声認識機能を使用する場合）
- 「Add secret」をクリック

---

## ✅ 設定確認

設定が完了したら、以下の方法で確認できます：

### GitHub CLIを使用

```bash
gh secret list
```

### Web UIを使用

GitHubリポジトリの Settings → Secrets and variables → Actions で確認できます。

---

## 🔍 トラブルシューティング

### Secretsが正しく設定されていない

1. Secret名のスペルを確認（大文字・小文字を区別）
2. JSON形式が正しいか確認（GCP_SA_KEY）
3. 値に余分なスペースや改行が含まれていないか確認

### GitHub Actionsが失敗する

1. GitHub Actionsのログを確認
2. Secretsが正しく設定されているか確認
3. エラーメッセージを確認

---

## 📝 次のステップ

GitHub Secretsの設定が完了したら：

1. **Supabaseのセットアップ**
   - `GOOGLE_CLOUD_DEPLOY.md` の「Supabaseのセットアップ」セクションを参照
   - `supabase_schema.sql` を実行してテーブルを作成

2. **デプロイの実行**
   - GitHubにコードをプッシュすると自動デプロイされます
   - または、手動でデプロイする場合:
     ```bash
     gcloud builds submit --config cloudbuild.yaml
     ```

---

## 📚 参考資料

- [GitHub Secrets ドキュメント](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub CLI ドキュメント](https://cli.github.com/manual/)
- `GOOGLE_CLOUD_DEPLOY.md` - 詳細なデプロイガイド

