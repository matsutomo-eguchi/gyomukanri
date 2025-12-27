# 🚀 5分でデプロイ！超簡単ガイド

このガイドでは、**最も簡単な方法**でアプリを公開する手順を説明します。

## 📌 前提条件

- GitHubアカウント（無料で作成可能）
- このプロジェクトのコード

---

## ⚡ 超簡単3ステップ

### ステップ1: GitHubにコードをアップロード（5分）

#### 方法A: GitHub Desktopを使う（最も簡単）

1. **GitHub Desktopをインストール**
   - https://desktop.github.com からダウンロード
   - インストールして起動

2. **GitHubにログイン**
   - GitHubアカウントでログイン

3. **リポジトリを作成**
   - GitHub Desktopで「File」→「New Repository」
   - 名前を入力（例：`gyomu-kanri`）
   - ローカルパスでこのプロジェクトフォルダを選択
   - 「Create repository」をクリック

4. **コードをアップロード**
   - 左下に変更ファイルが表示されます
   - コミットメッセージを入力（例：「初回コミット」）
   - 「Commit to main」をクリック
   - 「Publish repository」をクリック

#### 方法B: ブラウザから直接アップロード（GitHub Desktopが使えない場合）

1. **GitHubでリポジトリを作成**
   - https://github.com にログイン
   - 右上の「+」→「New repository」
   - リポジトリ名を入力
   - 「Create repository」をクリック

2. **ファイルをアップロード**
   - 「uploading an existing file」をクリック
   - プロジェクトフォルダ内のファイルをドラッグ&ドロップ
   - 「Commit changes」をクリック

### ステップ2: Streamlit Cloudでデプロイ（3分）

1. **Streamlit Cloudにアクセス**
   - https://share.streamlit.io を開く
   - 「Sign in with GitHub」をクリック
   - GitHubアカウントでログイン（初回は認証が必要）

2. **アプリをデプロイ**
   - 「New app」ボタンをクリック
   - 「Repository」で先ほど作成したリポジトリを選択
   - 「Branch」は「main」を選択
   - 「Main file path」に「app.py」と入力
   - 「Deploy!」ボタンをクリック

3. **完了！**
   - 1〜2分待つと、アプリが公開されます
   - URLは `https://YOUR_APP_NAME.streamlit.app` の形式です

### ステップ3: APIキーを設定（オプション・2分）

AI機能を使う場合のみ必要です。

1. **Streamlit Cloudのダッシュボードで**
   - デプロイしたアプリの「⋮」メニューをクリック
   - 「Settings」を選択

2. **Secretsを設定**
   - 「Secrets」タブをクリック
   - 以下の形式で入力：
   ```toml
   GROK_API_KEY = "your_api_key_here"
   ```
   - 「Save」をクリック
   - アプリが自動的に再起動されます

---

## ✅ 完了！

これで、インターネット上でアプリにアクセスできるようになりました！

### 次のステップ

- **コードを更新したら**：GitHubにプッシュすると、自動的に再デプロイされます
- **URLを共有**：チームメンバーにURLを共有すれば、誰でもアクセスできます
- **カスタムドメイン**：Streamlit Cloudではカスタムドメインは使用できませんが、無料で使えます

---

## 🆘 うまくいかない場合

### エラーが出る

1. **ログを確認**
   - Streamlit Cloudのダッシュボードで「Logs」タブを確認
   - エラーメッセージを確認

2. **よくある問題**
   - `requirements.txt` が正しくアップロードされているか確認
   - `app.py` のパスが正しいか確認（「Main file path」が「app.py」になっているか）

### データが保存されない

- Streamlit Cloudでは、データは一時的なストレージに保存されます
- 永続化が必要な場合は、RailwayやRenderの使用を検討してください（詳細は `DEPLOY.md` を参照）

---

## 📚 もっと詳しく知りたい場合

詳細なデプロイ方法や他の選択肢については、`DEPLOY.md` を参照してください。
