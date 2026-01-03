#!/bin/bash
# Supabase設定セットアップスクリプト

echo "============================================================"
echo "Supabase設定セットアップ"
echo "============================================================"
echo ""

# 環境変数の確認
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "⚠️  Supabase環境変数が設定されていません"
    echo ""
    echo "以下の手順で設定してください:"
    echo ""
    echo "1. Supabaseプロジェクトを作成:"
    echo "   https://supabase.com/ にアクセス"
    echo ""
    echo "2. APIキーを取得:"
    echo "   - Dashboard → Settings → API"
    echo "   - Project URL と anon public key をコピー"
    echo ""
    echo "3. 環境変数を設定:"
    echo "   export SUPABASE_URL='https://xxxxx.supabase.co'"
    echo "   export SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'"
    echo ""
    echo "4. スキーマを設定:"
    echo "   - Supabase Dashboard → SQL Editor"
    echo "   - supabase_schema.sql の内容を実行"
    echo ""
    echo "5. 検証を実行:"
    echo "   python3 verify_supabase.py"
    echo ""
    echo "詳細は SUPABASE_SETUP.md を参照してください"
    exit 1
fi

echo "✓ 環境変数が設定されています"
echo ""

# supabaseパッケージの確認
echo "🔍 supabaseパッケージの確認..."
if python3 -c "import supabase" 2>/dev/null; then
    echo "✓ supabaseパッケージがインストールされています"
else
    echo "⚠️  supabaseパッケージがインストールされていません"
    echo "インストールしますか？ (y/n)"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        echo "インストール中..."
        pip install supabase>=2.0.0
        if [ $? -eq 0 ]; then
            echo "✓ インストール完了"
        else
            echo "❌ インストールに失敗しました"
            exit 1
        fi
    else
        echo "スキップしました"
        exit 1
    fi
fi

echo ""
echo "🔍 Supabase接続テストを実行します..."
python3 verify_supabase.py

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ Supabase設定が完了しました！"
    echo "============================================================"
    echo ""
    echo "次のステップ:"
    echo "1. GitHub Secretsに環境変数を設定（デプロイ時）"
    echo "2. アプリケーションを起動して動作確認"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "❌ Supabase設定に問題があります"
    echo "============================================================"
    echo ""
    echo "トラブルシューティング:"
    echo "- SUPABASE_SETUP.md のトラブルシューティングセクションを参照"
    echo "- Supabase Dashboardでテーブルが作成されているか確認"
    echo "- RLS (Row Level Security) が無効化されているか確認"
    echo ""
    exit 1
fi

