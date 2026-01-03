"""
Supabase連携モジュール
データベースへの永続化を担当

Supabaseを使用してデータを保存・取得するためのモジュールです。
環境変数またはStreamlit SecretsからSupabaseの認証情報を取得します。
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("警告: supabaseパッケージがインストールされていません。pip install supabase を実行してください。")


class SupabaseManager:
    """Supabaseデータベース管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.client: Optional[Client] = None
        self.enabled = False
        
        # Supabase認証情報を取得（優先順位: 環境変数 > Streamlit Secrets）
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        # Streamlit Secretsから取得（環境変数がない場合）
        if not supabase_url or not supabase_key:
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and hasattr(st.secrets, 'get'):
                    if not supabase_url:
                        supabase_url = st.secrets.get("SUPABASE_URL", None)
                    if not supabase_key:
                        supabase_key = st.secrets.get("SUPABASE_KEY", None)
            except (FileNotFoundError, AttributeError, ImportError):
                pass
        
        if not SUPABASE_AVAILABLE:
            print("Supabaseクライアントが利用できません。ローカルファイルストレージを使用します。")
            return
        
        if supabase_url and supabase_key:
            try:
                self.client = create_client(supabase_url, supabase_key)
                self.enabled = True
                print("✅ Supabase接続が有効になりました")
            except Exception as e:
                print(f"Supabase接続エラー: {e}")
                print("ローカルファイルストレージを使用します。")
        else:
            print("Supabase認証情報が設定されていません。環境変数またはStreamlit Secretsで SUPABASE_URL と SUPABASE_KEY を設定してください。")
            print("ローカルファイルストレージを使用します。")
    
    def is_enabled(self) -> bool:
        """Supabaseが有効かどうかを返す"""
        return self.enabled and self.client is not None
    
    # ========== 利用者マスタ管理 ==========
    
    def get_active_users(self) -> List[str]:
        """アクティブな利用者名のリストを取得"""
        if not self.is_enabled():
            return []
        
        try:
            response = self.client.table("users_master").select("name").eq("active", True).execute()
            return [user["name"] for user in response.data]
        except Exception as e:
            print(f"利用者取得エラー: {e}")
            return []
    
    def get_all_users(self) -> List[Dict]:
        """全利用者情報を取得"""
        if not self.is_enabled():
            return []
        
        try:
            response = self.client.table("users_master").select("*").order("id").execute()
            return response.data
        except Exception as e:
            print(f"利用者一覧取得エラー: {e}")
            return []
    
    def add_user(self, name: str, classification: str = "放課後等デイサービス") -> bool:
        """新しい利用者を追加"""
        if not self.is_enabled():
            return False
        
        try:
            # 最大IDを取得
            max_id_response = self.client.table("users_master").select("id").order("id", desc=True).limit(1).execute()
            max_id = max_id_response.data[0]["id"] if max_id_response.data else 0
            
            data = {
                "id": max_id + 1,
                "name": name.strip(),
                "classification": classification,
                "active": True,
                "created_at": datetime.now().isoformat()
            }
            
            self.client.table("users_master").insert(data).execute()
            return True
        except Exception as e:
            print(f"利用者追加エラー: {e}")
            return False
    
    def delete_users(self, names: List[str]) -> bool:
        """利用者を削除（無効化）"""
        if not self.is_enabled():
            return False
        
        try:
            for name in names:
                self.client.table("users_master").update({
                    "active": False,
                    "deleted_at": datetime.now().isoformat()
                }).eq("name", name).execute()
            return True
        except Exception as e:
            print(f"利用者削除エラー: {e}")
            return False
    
    def restore_user(self, name: str) -> bool:
        """無効化された利用者を復元"""
        if not self.is_enabled():
            return False
        
        try:
            self.client.table("users_master").update({
                "active": True
            }).eq("name", name).execute()
            # deleted_atを削除するために、NULLを設定
            self.client.table("users_master").update({
                "deleted_at": None
            }).eq("name", name).execute()
            return True
        except Exception as e:
            print(f"利用者復元エラー: {e}")
            return False
    
    def sort_users(self, user_ids: List[int]) -> bool:
        """利用者マスタの順番を並び替える"""
        if not self.is_enabled():
            return False
        
        try:
            # すべての利用者を取得
            all_users = self.get_all_users()
            user_dict = {u["id"]: u for u in all_users}
            
            # 指定されたIDの順番で利用者を並び替え
            sorted_users = []
            for user_id in user_ids:
                if user_id in user_dict:
                    sorted_users.append(user_dict[user_id])
            
            # 指定されていない利用者を追加（アクティブな利用者を優先）
            remaining_ids = set(user_dict.keys()) - set(user_ids)
            remaining_users = [user_dict[uid] for uid in remaining_ids]
            active_remaining = [u for u in remaining_users if u.get("active", True)]
            inactive_remaining = [u for u in remaining_users if not u.get("active", True)]
            
            sorted_users.extend(active_remaining)
            sorted_users.extend(inactive_remaining)
            
            # 順番を更新するために、一時的なorderフィールドを使用
            # 注意: Supabaseでは順番の管理が難しいため、IDの順番で管理する
            # 実際の順番はクライアント側で管理する
            return True
        except Exception as e:
            print(f"利用者ソートエラー: {e}")
            return False
    
    def permanently_delete_users(self, names: List[str]) -> int:
        """利用者を完全に削除（マスタから削除）"""
        if not self.is_enabled():
            return 0
        
        try:
            deleted_count = 0
            for name in names:
                result = self.client.table("users_master").delete().eq("name", name).execute()
                if result.data:
                    deleted_count += len(result.data)
            return deleted_count
        except Exception as e:
            print(f"利用者完全削除エラー: {e}")
            return 0
    
    # ========== 日報データ管理 ==========
    
    def save_daily_report(self, report_data: Dict) -> bool:
        """日報データを保存"""
        if not self.is_enabled():
            print("❌ Supabaseが有効になっていません")
            return False

        try:
            print("Supabase日報保存開始...")
            report_data["created_at"] = datetime.now().isoformat()

            # 接続テスト
            if not self.client:
                print("❌ Supabaseクライアントが初期化されていません")
                return False

            print(f"データ挿入開始: table=daily_reports, スタッフ={report_data.get('記入スタッフ名', '不明')}")
            response = self.client.table("daily_reports").insert(report_data).execute()
            print(f"✅ Supabase保存成功: 挿入された行数={len(response.data) if response.data else 0}")
            return True

        except Exception as e:
            print(f"❌ Supabase日報保存エラー: {e}")
            print(f"エラー種別: {type(e).__name__}")

            # より詳細なエラー診断
            error_str = str(e).lower()
            if "unauthorized" in error_str or "permission denied" in error_str:
                print("💡 権限エラー: APIキーの権限を確認してください")
            elif "relation" in error_str and "does not exist" in error_str:
                print("💡 テーブルエラー: daily_reportsテーブルが存在するか確認してください")
            elif "row level security" in error_str:
                print("💡 RLSエラー: Row Level Securityが有効になっている可能性があります")
            elif "connection" in error_str or "timeout" in error_str:
                print("💡 接続エラー: インターネット接続またはSupabaseサービスの状態を確認してください")
            elif "invalid" in error_str and "key" in error_str:
                print("💡 認証エラー: SUPABASE_KEYが正しいか確認してください")

            import traceback
            print("エラーの詳細:")
            print(traceback.format_exc())
            return False
    
    def get_reports(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """日報データを取得"""
        if not self.is_enabled():
            return pd.DataFrame()
        
        try:
            query = self.client.table("daily_reports").select("*")
            
            if start_date:
                query = query.gte("業務日", start_date)
            if end_date:
                query = query.lte("業務日", end_date)
            
            response = query.order("created_at", desc=True).execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            print(f"日報取得エラー: {e}")
            return pd.DataFrame()
    
    # ========== スタッフアカウント管理 ==========
    
    def create_staff_account(self, user_id: str, password: str, name: str) -> bool:
        """新しいスタッフアカウントを作成"""
        if not self.is_enabled():
            return False
        
        try:
            import hashlib
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            
            data = {
                "user_id": user_id,
                "password_hash": password_hash,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            
            self.client.table("staff_accounts").insert(data).execute()
            return True
        except Exception as e:
            print(f"スタッフアカウント作成エラー: {e}")
            return False
    
    def get_all_staff_accounts(self) -> List[Dict]:
        """全スタッフアカウント情報を取得（パスワードハッシュは除外）"""
        if not self.is_enabled():
            return []
        
        try:
            response = self.client.table("staff_accounts").select("user_id, name, created_at, active").execute()
            return [
                {
                    "user_id": acc["user_id"],
                    "name": acc["name"],
                    "created_at": acc.get("created_at", ""),
                    "active": acc.get("active", True)
                }
                for acc in response.data
            ]
        except Exception as e:
            print(f"スタッフアカウント一覧取得エラー: {e}")
            return []
    
    def delete_staff_account(self, user_id: str) -> bool:
        """スタッフアカウントを削除（無効化）"""
        if not self.is_enabled():
            return False
        
        try:
            self.client.table("staff_accounts").update({
                "active": False,
                "deleted_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            print(f"スタッフアカウント削除エラー: {e}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """パスワードを変更"""
        if not self.is_enabled():
            return False
        
        try:
            import hashlib
            old_password_hash = hashlib.sha256(old_password.encode('utf-8')).hexdigest()
            new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            
            # 現在のパスワードを確認
            response = self.client.table("staff_accounts").select("password_hash").eq("user_id", user_id).execute()
            if not response.data or response.data[0]["password_hash"] != old_password_hash:
                return False
            
            # パスワードを更新
            self.client.table("staff_accounts").update({
                "password_hash": new_password_hash,
                "password_changed_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            print(f"パスワード変更エラー: {e}")
            return False
    
    def verify_login(self, user_id: str, password: str) -> Optional[Dict]:
        """ログイン認証"""
        if not self.is_enabled():
            print("Supabaseが有効になっていません。ログイン認証をスキップします。")
            return None
        
        try:
            import hashlib
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            
            # まず、テーブルにアクセスできるかテスト
            try:
                test_response = self.client.table("staff_accounts").select("id").limit(1).execute()
                print(f"テーブルアクセステスト成功: {len(test_response.data) if test_response.data else 0}件のレコード")
            except Exception as test_error:
                print(f"⚠️ テーブルアクセステスト失敗: {test_error}")
                print("💡 ヒント: Row Level Security (RLS) が有効になっている可能性があります。")
                print("   supabase_schema.sql のRLS無効化コマンドを実行してください。")
                raise
            
            # ユーザーIDで検索
            response = self.client.table("staff_accounts").select("*").eq("user_id", user_id).eq("active", True).execute()
            
            if not response.data:
                print(f"ユーザーID '{user_id}' が見つかりません。")
                # 全アカウント数を確認（デバッグ用）
                try:
                    all_accounts = self.client.table("staff_accounts").select("user_id").execute()
                    print(f"データベース内のアカウント数: {len(all_accounts.data) if all_accounts.data else 0}")
                    if all_accounts.data:
                        print(f"登録されているユーザーID: {[acc.get('user_id') for acc in all_accounts.data]}")
                except Exception as e:
                    print(f"アカウント一覧取得エラー: {e}")
                return None
            
            account = response.data[0]
            
            # パスワードハッシュを比較
            if account["password_hash"] == password_hash:
                print(f"✅ ログイン成功: {account['name']} ({user_id})")
                return {
                    "user_id": account["user_id"],
                    "name": account["name"],
                    "created_at": account.get("created_at", "")
                }
            else:
                print(f"ユーザーID '{user_id}' のパスワードが一致しません。")
                return None
        except Exception as e:
            error_msg = str(e)
            print(f"❌ ログイン認証エラー: {error_msg}")
            if "Row Level Security" in error_msg or "permission denied" in error_msg.lower():
                print("💡 解決方法: SupabaseのSQL Editorで以下のコマンドを実行してください:")
                print("   ALTER TABLE staff_accounts DISABLE ROW LEVEL SECURITY;")
            import traceback
            traceback.print_exc()
            return None
    
    def test_connection(self) -> Dict[str, any]:
        """接続テストを実行"""
        result = {
            "enabled": self.is_enabled(),
            "connected": False,
            "error": None,
            "table_accessible": False,
            "account_count": 0
        }
        
        if not self.is_enabled():
            result["error"] = "Supabaseが有効になっていません"
            return result
        
        try:
            # テーブルにアクセスできるかテスト
            response = self.client.table("staff_accounts").select("id").limit(1).execute()
            result["connected"] = True
            result["table_accessible"] = True
            
            # アカウント数を取得
            count_response = self.client.table("staff_accounts").select("id", count="exact").execute()
            result["account_count"] = count_response.count if hasattr(count_response, 'count') else len(count_response.data) if count_response.data else 0
            
        except Exception as e:
            result["error"] = str(e)
            result["connected"] = False
        
        return result
    
    # ========== 朝礼議事録管理 ==========
    
    def save_morning_meeting(self, meeting_data: Dict) -> bool:
        """朝礼議事録を保存"""
        if not self.is_enabled():
            return False
        
        try:
            meeting_data["created_at"] = datetime.now().isoformat()
            self.client.table("morning_meetings").insert(meeting_data).execute()
            return True
        except Exception as e:
            print(f"朝礼議事録保存エラー: {e}")
            return False
    
    def get_morning_meetings(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """朝礼議事録を取得"""
        if not self.is_enabled():
            return []
        
        try:
            query = self.client.table("morning_meetings").select("*")
            
            if start_date:
                query = query.gte("日付", start_date)
            if end_date:
                query = query.lte("日付", end_date)
            
            response = query.order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"朝礼議事録取得エラー: {e}")
            return []
    
    # ========== タグマスタ管理 ==========
    
    def get_tags(self, tag_type: str) -> List[str]:
        """タグリストを取得"""
        if not self.is_enabled():
            return []
        
        try:
            response = self.client.table("tags_master").select("tag_name").eq("tag_type", tag_type).execute()
            return [tag["tag_name"] for tag in response.data]
        except Exception as e:
            print(f"タグ取得エラー: {e}")
            return []
    
    def add_tag(self, tag_type: str, tag_name: str) -> bool:
        """新しいタグを追加"""
        if not self.is_enabled():
            return False
        
        try:
            data = {
                "tag_type": tag_type,
                "tag_name": tag_name.strip(),
                "created_at": datetime.now().isoformat()
            }
            self.client.table("tags_master").insert(data).execute()
            return True
        except Exception as e:
            print(f"タグ追加エラー: {e}")
            return False
    
    def delete_tag(self, tag_type: str, tag_name: str) -> bool:
        """タグを削除"""
        if not self.is_enabled():
            return False
        
        try:
            self.client.table("tags_master").delete().eq("tag_type", tag_type).eq("tag_name", tag_name).execute()
            return True
        except Exception as e:
            print(f"タグ削除エラー: {e}")
            return False
    
    # ========== 日別利用者記録管理 ==========
    
    def save_daily_users(self, target_date: str, user_names: List[str]) -> bool:
        """その日の利用者を保存"""
        if not self.is_enabled():
            return False
        
        try:
            # JSONB形式で保存
            data = {
                "target_date": target_date,
                "user_names": user_names,
                "updated_at": datetime.now().isoformat()
            }
            
            # UPSERT操作（存在する場合は更新、存在しない場合は挿入）
            self.client.table("daily_users").upsert(data, on_conflict="target_date").execute()
            return True
        except Exception as e:
            print(f"日別利用者記録保存エラー: {e}")
            return False
    
    def get_daily_users(self, target_date: str) -> List[str]:
        """その日の利用者一覧を取得"""
        if not self.is_enabled():
            return []
        
        try:
            response = self.client.table("daily_users").select("user_names").eq("target_date", target_date).execute()
            if response.data and response.data[0].get("user_names"):
                return response.data[0]["user_names"]
            return []
        except Exception as e:
            print(f"日別利用者記録取得エラー: {e}")
            return []
    
    def get_all_daily_users(self) -> Dict[str, List[str]]:
        """全期間の利用者記録を取得"""
        if not self.is_enabled():
            return {}
        
        try:
            response = self.client.table("daily_users").select("target_date, user_names").execute()
            return {
                record["target_date"]: record.get("user_names", [])
                for record in response.data
            }
        except Exception as e:
            print(f"全期間利用者記録取得エラー: {e}")
            return {}
    
    def delete_daily_users(self, target_date: str) -> bool:
        """指定日の利用者記録を削除"""
        if not self.is_enabled():
            return False
        
        try:
            self.client.table("daily_users").delete().eq("target_date", target_date).execute()
            return True
        except Exception as e:
            print(f"日別利用者記録削除エラー: {e}")
            return False
    
    # ========== スキーマ初期化 ==========
    
    def initialize_schema(self) -> Dict[str, any]:
        """データベーススキーマを初期化（テーブル存在確認）"""
        if not self.is_enabled():
            return {"success": False, "error": "Supabaseが有効になっていません"}
        
        result = {
            "success": True,
            "tables": {},
            "errors": []
        }
        
        required_tables = [
            "users_master",
            "daily_reports",
            "staff_accounts",
            "morning_meetings",
            "tags_master",
            "daily_users"
        ]
        
        for table_name in required_tables:
            try:
                # テーブルにアクセスできるかテスト
                response = self.client.table(table_name).select("id").limit(1).execute()
                result["tables"][table_name] = {
                    "exists": True,
                    "accessible": True
                }
            except Exception as e:
                error_msg = str(e)
                result["tables"][table_name] = {
                    "exists": False,
                    "accessible": False,
                    "error": error_msg
                }
                result["errors"].append(f"{table_name}: {error_msg}")
                result["success"] = False
        
        return result

