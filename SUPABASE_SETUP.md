# Supabase設定ガイド

このガイドでは、Google Cloud Runにデプロイする際にSupabaseを使用してデータを永続化する方法を説明します。

## 📋 目次

1. [Supabaseとは](#supabaseとは)
2. [Supabaseプロジェクトの作成](#supabaseプロジェクトの作成)
3. [データベーススキーマの設定](#データベーススキーマの設定)
4. [環境変数の設定](#環境変数の設定)
5. [接続テスト](#接続テスト)
6. [トラブルシューティング](#トラブルシューティング)

## Supabaseとは

Supabaseは、オープンソースのFirebase代替として開発されたバックエンドサービスです。PostgreSQLデータベースを提供し、データの永続化が可能です。

**Cloud Runでローカルファイルストレージを使用する場合の問題:**
- コンテナ再起動時にデータが失われる
- デプロイ時にデータが失われる可能性がある
- 複数インスタンス間でデータが共有されない

**Supabaseを使用する利点:**
- ✅ データが永続化される
- ✅ 複数インスタンス間でデータが共有される
- ✅ バックアップと復元が容易
- ✅ スケーラブル

## Supabaseプロジェクトの作成

### 1. Supabaseアカウントの作成

1. [Supabase](https://supabase.com/)にアクセス
2. 「Start your project」をクリック
3. GitHubアカウントでサインアップ（推奨）

### 2. 新しいプロジェクトの作成

1. Dashboardで「New Project」をクリック
2. プロジェクト情報を入力:
   - **Name**: プロジェクト名（例: `business-management`）
   - **Database Password**: 強力なパスワードを設定（必ず保存してください）
   - **Region**: `Northeast Asia (Tokyo)` を推奨（日本に近い）
3. 「Create new project」をクリック
4. プロジェクトの作成完了を待つ（1-2分）

### 3. APIキーの取得

1. プロジェクトのDashboardで「Settings」→「API」を開く
2. 以下の情報をコピー:
   - **Project URL**: `https://xxxxx.supabase.co` 形式
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` 形式

## データベーススキーマの設定

### 1. SQL Editorを開く

1. Supabase Dashboardで「SQL Editor」を開く
2. 「New query」をクリック

### 2. スキーマを実行

1. このリポジトリの `supabase_schema.sql` ファイルを開く
2. ファイルの内容をすべてコピー
3. SQL Editorに貼り付け
4. 「Run」ボタンをクリック（または `Ctrl+Enter` / `Cmd+Enter`）

### 3. 実行結果の確認

以下のメッセージが表示されれば成功です:
```
Success. No rows returned
```

### 4. テーブルの確認

1. Dashboardで「Table Editor」を開く
2. 以下のテーブルが作成されていることを確認:
   - `users_master` - 利用者マスタ
   - `daily_reports` - 日報データ
   - `staff_accounts` - スタッフアカウント
   - `morning_meetings` - 朝礼議事録
   - `tags_master` - タグマスタ
   - `daily_users` - 日別利用者記録

## 環境変数の設定

### GitHub Secretsに設定（推奨）

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」を開く
2. 「New repository secret」をクリック
3. 以下のシークレットを追加:

| Name | Value | 説明 |
|------|-------|------|
| `SUPABASE_URL` | `https://xxxxx.supabase.co` | SupabaseプロジェクトURL |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | Supabase anon public key |

### ローカル環境での設定

```bash
export SUPABASE_URL='https://xxxxx.supabase.co'
export SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

または、`.env`ファイルを作成:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 接続テスト

### 自動テスト（推奨）

```bash
# 環境変数を設定
export SUPABASE_URL='https://xxxxx.supabase.co'
export SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

# 検証スクリプトを実行
python3 verify_supabase.py
```

### 手動テスト

```python
from supabase import create_client
import os

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

client = create_client(supabase_url, supabase_key)

# テーブルアクセステスト
response = client.table("users_master").select("id").limit(1).execute()
print("✅ 接続成功！")
```

## トラブルシューティング

### エラー: "Row Level Security (RLS) policy violation"

**原因**: Row Level Security (RLS) が有効になっている

**解決方法**:
1. Supabase Dashboard → SQL Editor を開く
2. 以下のSQLを実行:

```sql
ALTER TABLE users_master DISABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports DISABLE ROW LEVEL SECURITY;
ALTER TABLE staff_accounts DISABLE ROW LEVEL SECURITY;
ALTER TABLE morning_meetings DISABLE ROW LEVEL SECURITY;
ALTER TABLE tags_master DISABLE ROW LEVEL SECURITY;
ALTER TABLE daily_users DISABLE ROW LEVEL SECURITY;
```

または、`supabase_schema.sql` のRLS無効化コマンドを実行してください。

### エラー: "relation does not exist"

**原因**: テーブルが作成されていない

**解決方法**:
1. `supabase_schema.sql` を実行してください
2. Table Editorでテーブルが作成されているか確認してください

### エラー: "permission denied"

**原因**: APIキーの権限が不足している

**解決方法**:
1. Supabase Dashboard → Settings → API を開く
2. `anon public` キーを使用していることを確認
3. 必要に応じて、`service_role` キーを使用（本番環境では非推奨）

### エラー: "connection timeout"

**原因**: ネットワーク接続の問題

**解決方法**:
1. インターネット接続を確認
2. Supabaseプロジェクトのステータスを確認
3. ファイアウォール設定を確認

## デプロイ後の確認

デプロイ後、以下の手順で動作確認を行ってください:

1. **ログインページで接続テスト**
   - アプリケーションにアクセス
   - ログインページで「🔍 接続テスト」ボタンをクリック
   - 接続成功メッセージが表示されることを確認

2. **データの保存テスト**
   - スタッフアカウントを作成
   - ログインして日報を入力
   - Supabase Dashboard → Table Editor でデータが保存されていることを確認

3. **データの永続化確認**
   - アプリケーションを再起動
   - データが保持されていることを確認

## 参考リンク

- [Supabase公式ドキュメント](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)

## サポート

問題が解決しない場合は、以下を確認してください:

1. `verify_supabase.py` の実行結果
2. Supabase Dashboardのログ
3. アプリケーションのログ（Cloud Runのログを確認）

---

**重要**: Supabaseを使用することで、データが永続化され、Cloud Runでも安全にデータを管理できます。本番環境では必ずSupabaseを使用することを推奨します。

