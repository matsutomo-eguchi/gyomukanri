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
    
    # ========== 日報データ管理 ==========
    
    def save_daily_report(self, report_data: Dict) -> bool:
        """日報データを保存"""
        if not self.is_enabled():
            return False
        
        try:
            report_data["created_at"] = datetime.now().isoformat()
            self.client.table("daily_reports").insert(report_data).execute()
            return True
        except Exception as e:
            print(f"日報保存エラー: {e}")
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
    
    def verify_login(self, user_id: str, password: str) -> Optional[Dict]:
        """ログイン認証"""
        if not self.is_enabled():
            print("Supabaseが有効になっていません。ログイン認証をスキップします。")
            return None
        
        try:
            import hashlib
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            
            # ユーザーIDで検索
            response = self.client.table("staff_accounts").select("*").eq("user_id", user_id).eq("active", True).execute()
            
            if not response.data:
                print(f"ユーザーID '{user_id}' が見つかりません。")
                return None
            
            account = response.data[0]
            
            # パスワードハッシュを比較
            if account["password_hash"] == password_hash:
                return {
                    "user_id": account["user_id"],
                    "name": account["name"],
                    "created_at": account.get("created_at", "")
                }
            else:
                print(f"ユーザーID '{user_id}' のパスワードが一致しません。")
                return None
        except Exception as e:
            print(f"ログイン認証エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
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

