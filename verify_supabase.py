#!/usr/bin/env python3
"""
Supabase設定検証スクリプト
デプロイ前にSupabaseの設定が正しいか確認します
"""
import os
import sys
from pathlib import Path

def check_environment_variables():
    """環境変数の確認"""
    print("🔍 環境変数の確認...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URLが設定されていません")
        return False
    
    if not supabase_key:
        print("❌ SUPABASE_KEYが設定されていません")
        return False
    
    print(f"✓ SUPABASE_URL: {supabase_url[:50]}...")
    print(f"✓ SUPABASE_KEY: {supabase_key[:20]}...")
    
    return True

def check_supabase_package():
    """Supabaseパッケージの確認"""
    print("\n🔍 Supabaseパッケージの確認...")
    
    try:
        import supabase
        print(f"✓ supabaseパッケージがインストールされています (バージョン: {supabase.__version__ if hasattr(supabase, '__version__') else '不明'})")
        return True
    except ImportError:
        print("❌ supabaseパッケージがインストールされていません")
        print("   インストール方法: pip install supabase>=2.0.0")
        return False

def test_supabase_connection():
    """Supabase接続テスト"""
    print("\n🔍 Supabase接続テスト...")
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        client = create_client(supabase_url, supabase_key)
        print("✓ Supabaseクライアントを作成しました")
        
        return client
    except Exception as e:
        print(f"❌ Supabase接続エラー: {e}")
        return None

def test_table_access(client):
    """テーブルアクセステスト"""
    print("\n🔍 テーブルアクセステスト...")
    
    required_tables = [
        "users_master",
        "daily_reports",
        "staff_accounts",
        "morning_meetings",
        "tags_master",
        "daily_users"
    ]
    
    failed_tables = []
    
    for table_name in required_tables:
        try:
            response = client.table(table_name).select("id").limit(1).execute()
            print(f"✓ {table_name}: アクセス可能")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {table_name}: アクセスエラー")
            print(f"   エラー詳細: {error_msg[:200]}")
            failed_tables.append((table_name, error_msg))
    
    return failed_tables

def check_schema_file():
    """スキーマファイルの確認"""
    print("\n🔍 スキーマファイルの確認...")
    
    schema_file = Path("supabase_schema.sql")
    if not schema_file.exists():
        print("⚠️  supabase_schema.sqlが見つかりません")
        return False
    
    print(f"✓ supabase_schema.sqlが見つかりました ({schema_file.stat().st_size} bytes)")
    return True

def main():
    """メイン処理"""
    print("=" * 60)
    print("Supabase設定検証スクリプト")
    print("=" * 60)
    
    # 環境変数の確認
    if not check_environment_variables():
        print("\n❌ 環境変数が設定されていません")
        print("\n設定方法:")
        print("  export SUPABASE_URL='your-supabase-url'")
        print("  export SUPABASE_KEY='your-supabase-key'")
        sys.exit(1)
    
    # Supabaseパッケージの確認
    if not check_supabase_package():
        sys.exit(1)
    
    # スキーマファイルの確認
    check_schema_file()
    
    # Supabase接続テスト
    client = test_supabase_connection()
    if not client:
        sys.exit(1)
    
    # テーブルアクセステスト
    failed_tables = test_table_access(client)
    
    if failed_tables:
        print("\n" + "=" * 60)
        print("❌ 検証失敗")
        print("=" * 60)
        print("\n以下のテーブルにアクセスできません:")
        for table_name, error_msg in failed_tables:
            print(f"  - {table_name}")
        
        print("\n💡 解決方法:")
        print("1. Supabase Dashboard → SQL Editor を開く")
        print("2. supabase_schema.sql の内容をコピーして実行してください")
        print("3. 特に、以下のコマンドが実行されているか確認してください:")
        print("   ALTER TABLE <table_name> DISABLE ROW LEVEL SECURITY;")
        print("\n4. エラーメッセージを確認:")
        for table_name, error_msg in failed_tables:
            if "Row Level Security" in error_msg or "permission denied" in error_msg.lower():
                print(f"   - {table_name}: RLSが有効になっている可能性があります")
        
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ すべての検証が成功しました！")
    print("=" * 60)
    print("\nSupabase設定は正しく構成されています。")
    print("デプロイを続行できます。")

if __name__ == "__main__":
    main()

