# デプロイガイド - 素人でも簡単にデプロイできる方法

このガイドでは、この業務管理システムをインターネット上に公開する方法を、初心者でも理解できるように説明します。

## 📋 デプロイ方法の比較

| 方法 | 難易度 | 費用 | 推奨度 | 特徴 |
|------|--------|------|--------|------|
| **Streamlit Cloud** | ⭐ 非常に簡単 | 無料 | ⭐⭐⭐⭐⭐ | GitHubと連携するだけで自動デプロイ |
| **Railway** | ⭐⭐ 簡単 | 無料枠あり | ⭐⭐⭐⭐ | シンプルで高速、データ永続化可能 |
| **Render** | ⭐⭐ 簡単 | 無料枠あり | ⭐⭐⭐ | 無料枠あり、設定が簡単 |

---

## 🚀 方法1: Streamlit Cloud（最も簡単・推奨）

### メリット
- ✅ **完全無料**
- ✅ **GitHubと連携するだけで自動デプロイ**
- ✅ **コードを更新すると自動的に再デプロイ**
- ✅ **設定が非常に簡単**

### デメリット
- ⚠️ データは一時的なストレージに保存（再起動で消える可能性あり）
- ⚠️ 無料プランは制限あり

### 手順

#### ステップ1: GitHubアカウントの作成とリポジトリの準備

1. **GitHubアカウントを作成**（まだの場合）
   - https://github.com にアクセス
   - 「Sign up」をクリックしてアカウント作成

2. **GitHub Desktopをインストール**（推奨）
   - https://desktop.github.com からダウンロード
   - または、コマンドラインでGitを使用

3. **リポジトリを作成**
   - GitHubにログイン
   - 右上の「+」→「New repository」をクリック
   - リポジトリ名を入力（例：`gyomu-kanri`）
   - 「Public」または「Private」を選択
   - 「Create repository」をクリック

#### ステップ2: コードをGitHubにアップロード

**方法A: GitHub Desktopを使用（推奨）**

1. GitHub Desktopを起動
2. 「File」→「Add Local Repository」をクリック
3. プロジェクトフォルダ（`業務管理2`）を選択
4. 左下の「Commit to main」をクリック
5. コミットメッセージを入力（例：「初回コミット」）
6. 「Commit to main」をクリック
7. 「Publish repository」をクリック

**方法B: コマンドラインを使用**

```bash
# プロジェクトディレクトリに移動
cd 業務管理2

# Gitリポジトリを初期化
git init

# すべてのファイルを追加
git add .

# コミット
git commit -m "初回コミット"

# GitHubリポジトリを追加（YOUR_USERNAMEとYOUR_REPO_NAMEを置き換え）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# プッシュ
git branch -M main
git push -u origin main
```

#### ステップ3: Streamlit Cloudでデプロイ

1. **Streamlit Cloudにアクセス**
   - https://share.streamlit.io にアクセス
   - 「Sign in with GitHub」をクリック
   - GitHubアカウントでログイン

2. **アプリをデプロイ**
   - 「New app」をクリック
   - 「Repository」で先ほど作成したリポジトリを選択
   - 「Branch」は「main」を選択
   - 「Main file path」は「app.py」と入力
   - 「Deploy!」をクリック

3. **APIキーの設定（オプション）**
   - デプロイ後、アプリの設定画面を開く
   - 「Secrets」タブをクリック
   - 以下の形式で入力：
   ```toml
   GROK_API_KEY = "your_api_key_here"
   ```
   - 「Save」をクリック

4. **完了！**
   - 数分待つと、アプリが公開されます
   - URLは `https://YOUR_APP_NAME.streamlit.app` の形式になります

---

## 🚂 方法2: Railway（データ永続化が必要な場合）

### メリット
- ✅ **無料枠あり**（$5分のクレジット/月）
- ✅ **データが永続化される**
- ✅ **GitHubと連携して自動デプロイ**
- ✅ **設定が比較的簡単**

### デメリット
- ⚠️ 無料枠は制限あり

### 手順

#### ステップ1: Railwayアカウントの作成

1. https://railway.app にアクセス
2. 「Start a New Project」をクリック
3. 「Login with GitHub」をクリックしてGitHubアカウントでログイン

#### ステップ2: プロジェクトの作成

1. 「New Project」をクリック
2. 「Deploy from GitHub repo」を選択
3. リポジトリを選択
4. 「Deploy Now」をクリック

#### ステップ3: 環境変数の設定

1. プロジェクトの設定画面を開く
2. 「Variables」タブをクリック
3. 以下の環境変数を追加：
   ```
   GROK_API_KEY = your_api_key_here
   ```
4. 「Add」をクリック

#### ステップ4: 起動コマンドの設定

1. 「Settings」タブをクリック
2. 「Start Command」に以下を入力：
   ```
   streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```
3. 「Save」をクリック

#### ステップ5: カスタムドメインの設定（オプション）

1. 「Settings」タブの「Domains」セクション
2. 「Generate Domain」をクリック
3. カスタムドメインが生成されます

---

## 🎨 方法3: Render（無料枠あり）

### メリット
- ✅ **無料枠あり**
- ✅ **設定が簡単**
- ✅ **自動デプロイ**

### デメリット
- ⚠️ 無料プランはスリープする（15分間アクセスがないと停止）

### 手順

#### ステップ1: Renderアカウントの作成

1. https://render.com にアクセス
2. 「Get Started for Free」をクリック
3. GitHubアカウントでログイン

#### ステップ2: 新しいWebサービスの作成

1. 「New +」→「Web Service」をクリック
2. GitHubリポジトリを選択
3. 以下の設定を入力：
   - **Name**: アプリ名（例：gyomu-kanri）
   - **Region**: 最寄りの地域を選択
   - **Branch**: main
   - **Root Directory**: （空白のまま）
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
4. 「Create Web Service」をクリック

#### ステップ3: 環境変数の設定

1. 「Environment」タブをクリック
2. 「Add Environment Variable」をクリック
3. 以下を追加：
   - Key: `GROK_API_KEY`
   - Value: `your_api_key_here`
4. 「Save Changes」をクリック

---

## 📝 デプロイ前のチェックリスト

デプロイ前に、以下を確認してください：

- [ ] `requirements.txt` が最新である
- [ ] `.gitignore` に `data/` と `.streamlit/secrets.toml` が含まれている
- [ ] 機密情報（APIキーなど）がコードに含まれていない
- [ ] すべての依存パッケージが `requirements.txt` に記載されている

---

## 🔧 トラブルシューティング

### デプロイが失敗する

1. **ログを確認**
   - Streamlit Cloud: デプロイ画面の「Logs」タブ
   - Railway: 「Deployments」タブのログ
   - Render: 「Logs」タブ

2. **よくある原因**
   - `requirements.txt` にパッケージが不足している
   - Pythonのバージョンが合わない
   - ポート番号の設定が間違っている

### データが保存されない

- **Streamlit Cloud**: データは一時的なストレージに保存されます。永続化が必要な場合は、外部データベース（Supabase、Firebase等）の使用を検討してください。
- **Railway/Render**: データは永続化されますが、定期的なバックアップを推奨します。

### APIキーが認識されない

1. 環境変数が正しく設定されているか確認
2. アプリを再起動
3. Streamlit Secretsの形式が正しいか確認（`.toml`形式）

---

## 💡 推奨事項

### 初めてデプロイする場合
→ **Streamlit Cloud** を推奨（最も簡単）

### データの永続化が必要な場合
→ **Railway** を推奨（無料枠あり、設定が簡単）

### 予算に余裕がある場合
→ **Railway** の有料プラン（$5/月）でより安定した運用が可能

---

## 📚 参考リンク

- Streamlit Cloud: https://share.streamlit.io
- Railway: https://railway.app
- Render: https://render.com
- Streamlit公式ドキュメント: https://docs.streamlit.io

---

## 🆘 サポートが必要な場合

デプロイで問題が発生した場合：
1. エラーメッセージを確認
2. ログを確認
3. 上記のトラブルシューティングを参照
4. GitHubのIssuesで質問（リポジトリが公開されている場合）
