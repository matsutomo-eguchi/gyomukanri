# Supabase設定クイックガイド

## ⚠️ 重要な注意事項

**SQL Editorには、SQLコマンドのみを実行してください。**
- ❌ `export SUPABASE_URL=...` のような環境変数設定コマンドは実行しないでください
- ✅ `supabase_schema.sql` のSQLコマンドのみを実行してください

## 正しい手順

### ステップ1: SQL Editorでスキーマを実行

1. Supabase Dashboard → **SQL Editor** を開く
2. 「New query」をクリック
3. **`supabase_schema.sql`** ファイルを開く
4. ファイルの内容を**すべてコピー**
5. SQL Editorに**貼り付け**
6. 「Run」ボタンをクリック（または `Ctrl+Enter` / `Cmd+Enter`）

### ステップ2: 環境変数の設定（ローカル環境のみ）

環境変数は**ターミナル（コマンドライン）**で設定します。SQL Editorでは設定しません。

```bash
# ターミナルで実行
export SUPABASE_URL='https://xfjzdzpidfdndjjekshz.supabase.co'
export SUPABASE_KEY='your-anon-public-key-here'
```

### ステップ3: 検証

```bash
# ターミナルで実行
python3 verify_supabase.py
```

## よくある間違い

### ❌ 間違い1: SQL Editorに環境変数コマンドを貼り付け
```
export SUPABASE_URL=https://...
```
→ これはSQLコマンドではないためエラーになります

### ✅ 正しい: SQL EditorにSQLコマンドを貼り付け
```sql
CREATE TABLE IF NOT EXISTS users_master (
    id SERIAL PRIMARY KEY,
    ...
);
```

## 確認方法

SQL Editorでスキーマを実行した後、以下で確認できます:

1. **Table Editor** を開く
2. 以下のテーブルが表示されることを確認:
   - `users_master`
   - `daily_reports`
   - `staff_accounts`
   - `morning_meetings`
   - `tags_master`
   - `daily_users`

## トラブルシューティング

### エラー: "syntax error at or near 'export'"
- **原因**: 環境変数設定コマンドをSQL Editorで実行した
- **解決**: SQL Editorには`supabase_schema.sql`の内容のみを実行してください

### エラー: "relation does not exist"
- **原因**: テーブルが作成されていない
- **解決**: `supabase_schema.sql`を実行してください

### エラー: "permission denied" または "Row Level Security"
- **原因**: RLSが有効になっている
- **解決**: `supabase_schema.sql`のRLS無効化コマンドが実行されているか確認してください

