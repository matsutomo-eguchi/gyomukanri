"""
データ管理モジュール
利用者マスタと日報データの永続化を担当
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd


class DataManager:
    """データ管理クラス"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初期化
        
        Args:
            data_dir: データファイルを保存するディレクトリ
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.master_file = self.data_dir / "users_master.json"
        self.report_file = self.data_dir / "daily_reports.csv"
        self.tags_file = self.data_dir / "tags_master.json"
        self.config_file = self.data_dir / "config.json"
        
        # 利用者マスタの初期化
        self._init_master_file()
        # タグマスタの初期化
        self._init_tags_file()
    
    def _init_master_file(self):
        """利用者マスタファイルが存在しない場合、初期化"""
        if not self.master_file.exists():
            default_users = [
                {"id": 1, "name": "サンプル児童1", "active": True},
                {"id": 2, "name": "サンプル児童2", "active": True},
            ]
            self._save_master(default_users)
    
    def _load_master(self) -> List[Dict]:
        """利用者マスタを読み込む"""
        try:
            with open(self.master_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _save_master(self, users: List[Dict]):
        """利用者マスタを保存する"""
        with open(self.master_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    
    def get_active_users(self) -> List[str]:
        """アクティブな利用者名のリストを取得"""
        users = self._load_master()
        return [u["name"] for u in users if u.get("active", True)]
    
    def get_all_users(self) -> List[Dict]:
        """全利用者情報を取得"""
        return self._load_master()
    
    def add_user(self, name: str) -> bool:
        """
        新しい利用者を追加
        
        Args:
            name: 利用者名
            
        Returns:
            成功した場合True
        """
        if not name or not name.strip():
            return False
        
        users = self._load_master()
        # 重複チェック
        if any(u["name"] == name.strip() for u in users):
            return False
        
        # 新しいIDを生成
        max_id = max([u.get("id", 0) for u in users], default=0)
        new_user = {
            "id": max_id + 1,
            "name": name.strip(),
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        users.append(new_user)
        self._save_master(users)
        return True
    
    def delete_users(self, names: List[str]) -> int:
        """
        利用者を削除（無効化）
        
        Args:
            names: 削除する利用者名のリスト
            
        Returns:
            削除した件数
        """
        users = self._load_master()
        deleted_count = 0
        
        for user in users:
            if user["name"] in names:
                user["active"] = False
                user["deleted_at"] = datetime.now().isoformat()
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_master(users)
        
        return deleted_count
    
    def restore_user(self, name: str) -> bool:
        """
        無効化された利用者を復元
        
        Args:
            name: 復元する利用者名
            
        Returns:
            成功した場合True
        """
        users = self._load_master()
        for user in users:
            if user["name"] == name:
                user["active"] = True
                if "deleted_at" in user:
                    del user["deleted_at"]
                self._save_master(users)
                return True
        return False
    
    def save_daily_report(self, report_data: Dict) -> bool:
        """
        日報データを保存
        
        Args:
            report_data: 日報データの辞書
            
        Returns:
            成功した場合True
        """
        try:
            # CSVファイルが存在する場合は読み込み、存在しない場合は新規作成
            if self.report_file.exists():
                df = pd.read_csv(self.report_file, encoding='utf-8')
            else:
                df = pd.DataFrame()
            
            # タイムスタンプを追加
            report_data["created_at"] = datetime.now().isoformat()
            
            # 新しい行を追加
            new_row = pd.DataFrame([report_data])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # 保存
            df.to_csv(self.report_file, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"日報保存エラー: {e}")
            return False
    
    def get_reports(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        日報データを取得
        
        Args:
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式）
            
        Returns:
            日報データのDataFrame
        """
        if not self.report_file.exists():
            return pd.DataFrame()
        
        df = pd.read_csv(self.report_file, encoding='utf-8')
        
        if "業務日" in df.columns:
            df["業務日"] = pd.to_datetime(df["業務日"])
            if start_date:
                df = df[df["業務日"] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df["業務日"] <= pd.to_datetime(end_date)]
        
        return df
    
    def _init_tags_file(self):
        """タグマスタファイルが存在しない場合、初期化"""
        if not self.tags_file.exists():
            default_tags = {
                "learning": [
                    "プリント学習", "宿題", "SST（ソーシャルスキルトレーニング）", 
                    "読み書き練習", "計算練習", "工作", "絵本の読み聞かせ"
                ],
                "free_play": [
                    "ブロック遊び", "お絵描き", "読書", "パズル", "カードゲーム",
                    "ままごと", "積み木", "折り紙", "ぬりえ", "音楽鑑賞"
                ],
                "group_play": [
                    "リトミック", "体操", "公園遊び", "ボール遊び", "鬼ごっこ",
                    "ダンス", "集団ゲーム", "散歩", "運動遊び", "歌"
                ]
            }
            self._save_tags(default_tags)
    
    def _load_tags(self) -> Dict[str, List[str]]:
        """タグマスタを読み込む"""
        try:
            with open(self.tags_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "learning": [],
                "free_play": [],
                "group_play": []
            }
    
    def _save_tags(self, tags: Dict[str, List[str]]):
        """タグマスタを保存する"""
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            json.dump(tags, f, ensure_ascii=False, indent=2)
    
    def get_tags(self, tag_type: str) -> List[str]:
        """
        タグリストを取得
        
        Args:
            tag_type: タグタイプ ("learning", "free_play", "group_play")
            
        Returns:
            タグのリスト
        """
        tags = self._load_tags()
        return tags.get(tag_type, [])
    
    def add_tag(self, tag_type: str, tag_name: str) -> bool:
        """
        新しいタグを追加
        
        Args:
            tag_type: タグタイプ ("learning", "free_play", "group_play")
            tag_name: タグ名
            
        Returns:
            成功した場合True
        """
        if not tag_name or not tag_name.strip():
            return False
        
        tags = self._load_tags()
        if tag_type not in tags:
            tags[tag_type] = []
        
        # 重複チェック
        if tag_name.strip() in tags[tag_type]:
            return False
        
        tags[tag_type].append(tag_name.strip())
        self._save_tags(tags)
        return True
    
    def delete_tag(self, tag_type: str, tag_name: str) -> bool:
        """
        タグを削除
        
        Args:
            tag_type: タグタイプ ("learning", "free_play", "group_play")
            tag_name: 削除するタグ名
            
        Returns:
            成功した場合True
        """
        tags = self._load_tags()
        if tag_type not in tags:
            return False
        
        if tag_name in tags[tag_type]:
            tags[tag_type].remove(tag_name)
            self._save_tags(tags)
            return True
        return False
    
    def _load_config(self) -> Dict:
        """設定ファイルを読み込む"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_config(self, config: Dict):
        """設定ファイルを保存する"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def save_api_key(self, api_key: str) -> bool:
        """
        APIキーを保存
        
        Args:
            api_key: Grok APIキー
            
        Returns:
            成功した場合True
        """
        try:
            config = self._load_config()
            config["grok_api_key"] = api_key
            self._save_config(config)
            return True
        except Exception as e:
            print(f"APIキー保存エラー: {e}")
            return False
    
    def get_api_key(self) -> Optional[str]:
        """
        APIキーを取得
        
        Returns:
            APIキー（存在しない場合はNone）
        """
        config = self._load_config()
        return config.get("grok_api_key")
    
    def delete_api_key(self) -> bool:
        """
        APIキーを削除
        
        Returns:
            成功した場合True
        """
        try:
            config = self._load_config()
            if "grok_api_key" in config:
                del config["grok_api_key"]
                self._save_config(config)
            return True
        except Exception as e:
            print(f"APIキー削除エラー: {e}")
            return False

