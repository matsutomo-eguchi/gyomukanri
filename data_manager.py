"""
データ管理モジュール
利用者マスタと日報データの永続化を担当

データ保護について:
- 既存データは絶対に上書きされません
- 初期化処理はファイルが存在しない場合のみ実行されます
- アプリ更新時も過去のデータは保持されます
- データファイルは .gitignore で除外されているため、Gitにコミットされません
- コード更新（デプロイ）時もデータは自動的に保護されます

Supabase連携:
- 環境変数 SUPABASE_URL と SUPABASE_KEY が設定されている場合、Supabaseを使用
- 設定されていない場合はローカルファイルストレージを使用
"""
import json
import os
import hashlib
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

# Supabase連携（オプション）
try:
    from supabase_manager import SupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    SupabaseManager = None


class DataManager:
    """データ管理クラス"""
    
    # データスキーマバージョン（スキーマ変更時に更新）
    SCHEMA_VERSION = 1
    
    def __init__(self, data_dir: str = "data"):
        """
        初期化
        
        Args:
            data_dir: データファイルを保存するディレクトリ
        """
        self.data_dir = Path(data_dir)
        
        # Supabase連携の初期化（環境変数が設定されている場合）
        self.supabase_manager = None
        if SUPABASE_AVAILABLE and SupabaseManager:
            try:
                self.supabase_manager = SupabaseManager()
                if self.supabase_manager.is_enabled():
                    print("✅ Supabase連携が有効です。データはSupabaseに保存されます。")
            except Exception as e:
                print(f"Supabase初期化エラー: {e}")
                print("ローカルファイルストレージを使用します。")
        
        # データディレクトリの保護（既存データを保持）
        self._ensure_data_directory_protected()
        
        self.master_file = self.data_dir / "users_master.json"
        self.report_file = self.data_dir / "daily_reports.csv"
        self.tags_file = self.data_dir / "tags_master.json"
        self.config_file = self.data_dir / "config.json"
        self.staff_accounts_file = self.data_dir / "staff_accounts.json"
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.morning_meeting_file = self.data_dir / "morning_meetings.json"
        self.daily_users_file = self.data_dir / "daily_users.json"
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.version_file = self.data_dir / ".schema_version"
        
        # Supabaseが無効な場合のみローカルファイル処理を実行
        if not self._is_supabase_enabled():
            # データマイグレーション（スキーマ変更時にもデータを保持）
            self._migrate_data_if_needed()
            
            # デプロイ前の自動バックアップ（既存データがある場合）
            self._auto_backup_on_startup()
            
            # データ整合性チェック
            self._verify_data_integrity()
            
            # 利用者マスタの初期化（既存データは保護）
            self._init_master_file()
            # タグマスタの初期化（既存データは保護）
            self._init_tags_file()
            # スタッフアカウントの初期化（既存データは保護）
            self._init_staff_accounts_file()
            # 朝礼議事録の初期化（既存データは保護）
            self._init_morning_meeting_file()
            # 日別利用者記録の初期化（既存データは保護）
            self._init_daily_users_file()
    
    def _is_supabase_enabled(self) -> bool:
        """Supabaseが有効かどうかを返す"""
        return self.supabase_manager is not None and self.supabase_manager.is_enabled()
    
    def _ensure_data_directory_protected(self):
        """
        データディレクトリの保護を確保
        コード更新時にもデータが消えないようにする
        """
        # データディレクトリが存在する場合は、そのまま保持
        if self.data_dir.exists():
            # 既存のデータファイルを確認
            existing_files = list(self.data_dir.glob("*"))
            if existing_files:
                # データが存在する場合は保護マーカーを作成
                protection_marker = self.data_dir / ".data_protected"
                if not protection_marker.exists():
                    try:
                        protection_marker.touch()
                        with open(protection_marker, 'w', encoding='utf-8') as f:
                            f.write(f"Data protection enabled: {datetime.now().isoformat()}\n")
                    except Exception:
                        pass  # マーカーの作成に失敗しても続行
        else:
            # データディレクトリが存在しない場合は作成
            self.data_dir.mkdir(exist_ok=True)
    
    def _migrate_data_if_needed(self):
        """
        データマイグレーション
        スキーマバージョンが変更された場合に、既存データを新しい形式に変換
        """
        current_version = self._get_schema_version()
        
        if current_version < self.SCHEMA_VERSION:
            # マイグレーションが必要な場合
            try:
                # マイグレーション前にバックアップを作成
                self.create_backup()
                
                # バージョン1へのマイグレーション（将来の拡張用）
                if current_version == 0 and self.SCHEMA_VERSION >= 1:
                    # 既存データの互換性を確保
                    self._migrate_to_version_1()
                
                # スキーマバージョンを更新
                self._save_schema_version(self.SCHEMA_VERSION)
            except Exception as e:
                print(f"データマイグレーションエラー: {e}")
                # エラーが発生しても続行（既存データを保護）
    
    def _get_schema_version(self) -> int:
        """現在のスキーマバージョンを取得"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version_str = f.read().strip()
                    return int(version_str) if version_str.isdigit() else 0
            except Exception:
                return 0
        return 0
    
    def _save_schema_version(self, version: int):
        """スキーマバージョンを保存"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                f.write(str(version))
        except Exception:
            pass
    
    def _migrate_to_version_1(self):
        """
        バージョン1へのマイグレーション
        既存データの互換性を確保
        """
        # 既存データファイルの整合性を確認
        # 必要に応じてデータ形式を更新
        
        # 利用者マスタのマイグレーション
        if self.master_file.exists():
            try:
                users = self._load_master()
                # バージョン1の必須フィールドを追加（既存データを保護）
                updated = False
                for user in users:
                    if "created_at" not in user:
                        user["created_at"] = datetime.now().isoformat()
                        updated = True
                    # 区分フィールドが存在しない場合はデフォルト値を設定
                    if "classification" not in user:
                        user["classification"] = "放課後等デイサービス"
                        updated = True
                if updated:
                    self._save_master(users)
            except Exception:
                pass  # エラーが発生しても既存データを保護
        
        # その他のデータファイルも同様にマイグレーション可能
    
    def _auto_backup_on_startup(self):
        """
        起動時の自動バックアップ
        既存データがある場合のみ実行
        """
        # 既存データが存在するか確認
        has_data = (
            self.master_file.exists() or
            self.report_file.exists() or
            self.tags_file.exists() or
            self.staff_accounts_file.exists() or
            self.morning_meeting_file.exists() or
            self.daily_users_file.exists() or
            (self.reports_dir.exists() and list(self.reports_dir.glob("*.md")))
        )
        
        if has_data:
            # 最後のバックアップ時刻を確認
            last_backup_time = self._get_last_backup_time()
            now = datetime.now()
            
            # 24時間以内にバックアップが作成されていない場合のみ実行
            if not last_backup_time or (now - last_backup_time).total_seconds() > 86400:
                try:
                    backup_path = self.create_backup()
                    if backup_path:
                        print(f"起動時の自動バックアップを作成しました: {backup_path}")
                except Exception as e:
                    print(f"自動バックアップエラー: {e}")
                    # エラーが発生しても続行
    
    def _get_last_backup_time(self) -> Optional[datetime]:
        """最後のバックアップ作成時刻を取得"""
        backups = self.get_backup_list()
        if backups:
            try:
                return datetime.fromisoformat(backups[0]["created_at"])
            except Exception:
                return None
        return None
    
    def _verify_data_integrity(self):
        """
        データ整合性チェック
        破損したデータファイルを検出して修復を試みる
        """
        # 各データファイルの整合性を確認
        data_files = [
            self.master_file,
            self.tags_file,
            self.staff_accounts_file,
            self.morning_meeting_file,
            self.daily_users_file,
            self.config_file
        ]
        
        for file_path in data_files:
            if file_path.exists():
                try:
                    # JSONファイルの読み込みテスト
                    if file_path.suffix == '.json':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                except json.JSONDecodeError:
                    # JSONが破損している場合、バックアップから復元を試みる
                    print(f"警告: {file_path.name} が破損している可能性があります")
                    self._attempt_restore_from_backup(file_path)
                except Exception as e:
                    print(f"データ整合性チェックエラー ({file_path.name}): {e}")
        
        # CSVファイルの整合性チェック
        if self.report_file.exists():
            try:
                pd.read_csv(self.report_file, encoding='utf-8')
            except Exception as e:
                print(f"警告: daily_reports.csv の読み込みエラー: {e}")
                # バックアップから復元を試みる
                self._attempt_restore_from_backup(self.report_file)
    
    def _attempt_restore_from_backup(self, file_path: Path):
        """
        バックアップからファイルを復元しようとする
        """
        backups = self.get_backup_list()
        if backups:
            # 最新のバックアップから復元を試みる
            latest_backup = backups[0]
            backup_path = Path(latest_backup["path"])
            backup_file = backup_path / file_path.name
            
            if backup_file.exists():
                try:
                    # 現在のファイルをバックアップ
                    if file_path.exists():
                        corrupted_backup = file_path.with_suffix(file_path.suffix + '.corrupted')
                        shutil.copy2(file_path, corrupted_backup)
                    
                    # バックアップから復元
                    shutil.copy2(backup_file, file_path)
                    print(f"バックアップから {file_path.name} を復元しました")
                except Exception as e:
                    print(f"バックアップからの復元に失敗しました: {e}")
    
    def _init_master_file(self):
        """利用者マスタファイルが存在しない場合、初期化（既存データは保護）"""
        # 既存データを絶対に上書きしない
        if not self.master_file.exists():
            default_users = [
                {"id": 1, "name": "サンプル児童1", "classification": "放課後等デイサービス", "active": True},
                {"id": 2, "name": "サンプル児童2", "classification": "児童発達支援", "active": True},
            ]
            self._save_master(default_users)
        else:
            # 既存データが存在する場合は、そのまま保持（上書きしない）
            # ただし、区分フィールドがない場合は追加する
            try:
                users = self._load_master()
                updated = False
                for user in users:
                    if "classification" not in user:
                        user["classification"] = "放課後等デイサービス"
                        updated = True
                if updated:
                    self._save_master(users)
            except Exception:
                pass  # エラーが発生しても既存データを保護
    
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
        if self._is_supabase_enabled():
            return self.supabase_manager.get_active_users()
        users = self._load_master()
        return [u["name"] for u in users if u.get("active", True)]
    
    def get_all_users(self) -> List[Dict]:
        """全利用者情報を取得"""
        if self._is_supabase_enabled():
            return self.supabase_manager.get_all_users()
        return self._load_master()
    
    def get_user_by_name(self, name: str) -> Optional[Dict]:
        """
        利用者名から利用者情報を取得
        
        Args:
            name: 利用者名
            
        Returns:
            利用者情報の辞書、見つからない場合はNone
        """
        users = self._load_master()
        for user in users:
            if user["name"] == name and user.get("active", True):
                return user
        return None
    
    def add_user(self, name: str, classification: str = "放課後等デイサービス") -> bool:
        """
        新しい利用者を追加
        
        Args:
            name: 利用者名
            classification: 利用者区分（"放課後等デイサービス"または"児童発達支援"）
            
        Returns:
            成功した場合True
        """
        if not name or not name.strip():
            return False
        
        # 区分のバリデーション
        valid_classifications = ["放課後等デイサービス", "児童発達支援"]
        if classification not in valid_classifications:
            classification = "放課後等デイサービス"  # デフォルト値
        
        if self._is_supabase_enabled():
            return self.supabase_manager.add_user(name, classification)
        
        users = self._load_master()
        # 重複チェック
        if any(u["name"] == name.strip() for u in users):
            return False
        
        # 新しいIDを生成
        max_id = max([u.get("id", 0) for u in users], default=0)
        new_user = {
            "id": max_id + 1,
            "name": name.strip(),
            "classification": classification,
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
        if self._is_supabase_enabled():
            success = self.supabase_manager.delete_users(names)
            return len(names) if success else 0
        
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
        if self._is_supabase_enabled():
            return self.supabase_manager.restore_user(name)
        
        users = self._load_master()
        for user in users:
            if user["name"] == name:
                user["active"] = True
                if "deleted_at" in user:
                    del user["deleted_at"]
                self._save_master(users)
                return True
        return False
    
    def sort_users(self, user_ids: List[int]) -> bool:
        """
        利用者マスタの順番を並び替える
        
        Args:
            user_ids: 新しい順番の利用者IDのリスト
            
        Returns:
            成功した場合True
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.sort_users(user_ids)
        
        try:
            users = self._load_master()
            
            # IDから利用者へのマッピングを作成
            user_dict = {u["id"]: u for u in users}
            
            # 指定されたIDの順番で利用者を並び替え
            sorted_users = []
            for user_id in user_ids:
                if user_id in user_dict:
                    sorted_users.append(user_dict[user_id])
            
            # 指定されていない利用者を追加（アクティブな利用者を優先）
            remaining_ids = set(user_dict.keys()) - set(user_ids)
            remaining_users = [user_dict[uid] for uid in remaining_ids]
            
            # アクティブな利用者を先に、無効化された利用者を後に
            active_remaining = [u for u in remaining_users if u.get("active", True)]
            inactive_remaining = [u for u in remaining_users if not u.get("active", True)]
            
            sorted_users.extend(active_remaining)
            sorted_users.extend(inactive_remaining)
            
            self._save_master(sorted_users)
            return True
        except Exception as e:
            print(f"利用者ソートエラー: {e}")
            return False
    
    def permanently_delete_users(self, names: List[str]) -> int:
        """
        利用者を完全に削除（マスタから削除）
        
        Args:
            names: 完全に削除する利用者名のリスト
            
        Returns:
            削除した件数
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.permanently_delete_users(names)
        
        try:
            users = self._load_master()
            original_count = len(users)
            
            # 指定された名前の利用者を除外
            users = [u for u in users if u["name"] not in names]
            
            deleted_count = original_count - len(users)
            
            if deleted_count > 0:
                self._save_master(users)
            
            return deleted_count
        except Exception as e:
            print(f"利用者完全削除エラー: {e}")
            return 0
    
    def save_daily_report(self, report_data: Dict) -> bool:
        """
        日報データを保存（CSVとMarkdown形式の両方）
        既存データは保護され、新しいデータのみ追加される

        Args:
            report_data: 日報データの辞書

        Returns:
            成功した場合True
        """
        try:
            print(f"業務報告保存開始: スタッフ={report_data.get('記入スタッフ名', '不明')}, 日付={report_data.get('業務日', '不明')}")

            # Supabaseが有効な場合はSupabaseに保存
            if self._is_supabase_enabled():
                print("Supabase保存モードを使用")
                success = self.supabase_manager.save_daily_report(report_data)
                if success:
                    print("✅ Supabaseへの保存に成功")
                    # Markdown形式でも保存（担当利用者名または送迎区分がある場合）
                    if (("担当利用者名" in report_data and report_data["担当利用者名"]) or \
                       ("送迎区分" in report_data and report_data["送迎区分"])):
                        try:
                            self._save_report_as_markdown(report_data)
                            print("✅ Markdownファイルの保存にも成功")
                        except Exception as md_error:
                            print(f"⚠️ Markdown保存エラー（Supabase保存は成功）: {md_error}")
                    return True
                else:
                    print("❌ Supabase保存に失敗 - ローカル保存にフォールバック")
                    # Supabase保存に失敗した場合、ローカル保存にフォールバック
                    return self._save_to_local_csv(report_data)

            # ローカルファイルストレージを使用
            print("ローカルCSV保存モードを使用")
            return self._save_to_local_csv(report_data)

        except Exception as e:
            print(f"❌ 日報保存エラー: {e}")
            import traceback
            print("エラーの詳細:")
            print(traceback.format_exc())
            return False

    def _save_to_local_csv(self, report_data: Dict) -> bool:
        """
        ローカルCSVファイルに日報データを保存

        Args:
            report_data: 日報データの辞書

        Returns:
            成功した場合True
        """
        try:
            print(f"ローカルCSV保存開始: {self.report_file}")

            # CSVファイルが存在する場合は読み込み、存在しない場合は新規作成
            # 既存データは必ず保持される
            if self.report_file.exists():
                print(f"既存CSVファイル読み込み: {self.report_file}")
                df = pd.read_csv(self.report_file, encoding='utf-8')
                print(f"既存データ行数: {len(df)}")
            else:
                print(f"新規CSVファイル作成: {self.report_file}")
                df = pd.DataFrame()

            # タイムスタンプを追加
            report_data["created_at"] = datetime.now().isoformat()

            # 新しい行を追加（既存データは保持）
            new_row = pd.DataFrame([report_data])
            df = pd.concat([df, new_row], ignore_index=True)
            print(f"データ追加後行数: {len(df)}")

            # CSV形式で保存（既存データを含む）
            df.to_csv(self.report_file, index=False, encoding='utf-8')
            print(f"✅ CSV保存成功: {self.report_file}")

            # Markdown形式でも保存（担当利用者名または送迎区分がある場合）
            if ("担当利用者名" in report_data and report_data["担当利用者名"]) or \
               ("送迎区分" in report_data and report_data["送迎区分"]):
                try:
                    self._save_report_as_markdown(report_data)
                    print("✅ Markdownファイル保存成功")
                except Exception as md_error:
                    print(f"⚠️ Markdown保存エラー（CSV保存は成功）: {md_error}")

            return True

        except PermissionError as e:
            print(f"❌ ファイル権限エラー: {e}")
            print(f"ファイルパス: {self.report_file}")
            print("dataディレクトリの書き込み権限を確認してください")
            return False
        except OSError as e:
            print(f"❌ OSエラー: {e}")
            print("ディスク容量やファイルシステムの問題を確認してください")
            return False
        except Exception as e:
            print(f"❌ ローカル保存エラー: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def _save_report_as_markdown(self, report_data: Dict) -> bool:
        """
        日報データをMarkdown形式で保存
        
        Args:
            report_data: 日報データの辞書
            
        Returns:
            成功した場合True
        """
        try:
            # ファイル名を生成（業務日_担当利用者名または送迎区分.md）
            work_date = report_data.get("業務日", datetime.now().date().isoformat())
            if "担当利用者名" in report_data and report_data["担当利用者名"]:
                name_part = report_data["担当利用者名"]
            elif "送迎区分" in report_data and report_data["送迎区分"]:
                name_part = report_data["送迎区分"]
            else:
                name_part = "不明"
            # ファイル名に使用できない文字を置換
            safe_name = name_part.replace("/", "_").replace("\\", "_").replace(":", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{work_date}_{safe_name}_{timestamp}.md"
            filepath = self.reports_dir / filename
            
            # Markdown形式で内容を生成
            md_content = self._format_report_as_markdown(report_data)
            
            # ファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return True
        except Exception as e:
            print(f"Markdown保存エラー: {e}")
            return False
    
    def _format_report_as_markdown(self, report_data: Dict) -> str:
        """
        日報データをMarkdown形式の文字列に変換
        
        Args:
            report_data: 日報データの辞書
            
        Returns:
            Markdown形式の文字列
        """
        lines = []
        lines.append("# 日報")
        lines.append("")
        
        # 基本情報
        lines.append("## 基本情報")
        lines.append("")
        if "業務日" in report_data:
            lines.append(f"- **業務日**: {report_data['業務日']}")
        if "記入スタッフ名" in report_data:
            lines.append(f"- **記入スタッフ名**: {report_data['記入スタッフ名']}")
        if "始業時間" in report_data:
            lines.append(f"- **始業時間**: {report_data['始業時間']}")
        if "終業時間" in report_data:
            lines.append(f"- **終業時間**: {report_data['終業時間']}")
        if "担当利用者名" in report_data:
            lines.append(f"- **担当利用者名**: {report_data['担当利用者名']}")
        if "利用者区分" in report_data and report_data["利用者区分"]:
            classification_display = report_data["利用者区分"]
            # 区分の表示名を設定（放デイ/児発の略称付き）
            if classification_display == "放課後等デイサービス":
                classification_display = "放課後等デイサービス（放デイ）"
            elif classification_display == "児童発達支援":
                classification_display = "児童発達支援（児発）"
            lines.append(f"- **利用者区分**: {classification_display}")
        if "created_at" in report_data:
            created_at = report_data['created_at']
            if isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    lines.append(f"- **作成日時**: {dt.strftime('%Y年%m月%d日 %H:%M:%S')}")
                except:
                    lines.append(f"- **作成日時**: {created_at}")
        lines.append("")
        
        # バイタル情報
        if any(key in report_data for key in ["体温", "バイタルその他", "気分顔色"]):
            lines.append("## バイタル")
            lines.append("")
            if "体温" in report_data:
                lines.append(f"- **体温**: {report_data['体温']}℃")
            if "バイタルその他" in report_data and report_data["バイタルその他"]:
                lines.append(f"- **その他**: {report_data['バイタルその他']}")
            if "気分顔色" in report_data:
                lines.append(f"- **気分・顔色**: {report_data['気分顔色']}")
            lines.append("")
        
        # 食事・健康情報
        if any(key in report_data for key in ["食事状態", "食事詳細", "水分補給量", "排泄記録"]):
            lines.append("## 食事・健康")
            lines.append("")
            if "食事状態" in report_data:
                lines.append(f"- **食事・おやつ**: {report_data['食事状態']}")
            if "食事詳細" in report_data and report_data["食事詳細"]:
                lines.append(f"- **メニュー内容**: {report_data['食事詳細']}")
            if "水分補給量" in report_data and report_data.get("水分補給量", 0) > 0:
                lines.append(f"- **水分補給量**: {report_data['水分補給量']}ml")
            if "排泄記録" in report_data and report_data["排泄記録"]:
                lines.append(f"- **排泄記録**: {report_data['排泄記録']}")
            lines.append("")
        
        # 活動内容
        if any(key in report_data for key in ["学習内容タグ", "学習内容詳細", "自由遊びタグ", "自由遊び詳細", "集団遊びタグ", "集団遊び詳細"]):
            lines.append("## 活動内容")
            lines.append("")
            
            if "学習内容タグ" in report_data and report_data["学習内容タグ"]:
                lines.append(f"- **学習内容**: {report_data['学習内容タグ']}")
            if "学習内容詳細" in report_data and report_data["学習内容詳細"]:
                lines.append(f"  {report_data['学習内容詳細']}")
                lines.append("")
            
            if "自由遊びタグ" in report_data and report_data["自由遊びタグ"]:
                lines.append(f"- **自由遊び**: {report_data['自由遊びタグ']}")
            if "自由遊び詳細" in report_data and report_data["自由遊び詳細"]:
                lines.append(f"  {report_data['自由遊び詳細']}")
                lines.append("")
            
            if "集団遊びタグ" in report_data and report_data["集団遊びタグ"]:
                lines.append(f"- **集団遊び**: {report_data['集団遊びタグ']}")
            if "集団遊び詳細" in report_data and report_data["集団遊び詳細"]:
                lines.append(f"  {report_data['集団遊び詳細']}")
                lines.append("")
        
        # 特記事項
        if "特記事項" in report_data and report_data["特記事項"]:
            lines.append("## 特記事項")
            lines.append("")
            lines.append(report_data["特記事項"])
            lines.append("")
        
        # 送迎業務記録
        if "送迎区分" in report_data:
            lines.append("## 送迎業務記録")
            lines.append("")
            if "送迎区分" in report_data:
                lines.append(f"- **送迎区分**: {report_data['送迎区分']}")
            if "使用車両" in report_data and report_data["使用車両"]:
                lines.append(f"- **使用車両**: {report_data['使用車両']}")
            if "送迎児童名" in report_data and report_data["送迎児童名"]:
                lines.append(f"- **送迎児童名**: {report_data['送迎児童名']}")
            if "送迎人数" in report_data:
                lines.append(f"- **送迎人数**: {report_data['送迎人数']}名")
            if "到着時刻" in report_data and report_data["到着時刻"]:
                lines.append(f"- **到着時刻**: {report_data['到着時刻']}")
            if "退所時間" in report_data and report_data["退所時間"]:
                lines.append(f"- **退所時間**: {report_data['退所時間']}")
            lines.append("")
        
        # 業務報告・共有事項
        if any(key in report_data for key in ["ヒヤリハット事故", "ヒヤリハット詳細", "発生場所", "対象者", "事故発生の状況", "経過", "事故原因", "対策", "その他", "申し送り事項", "備品購入要望"]):
            lines.append("## 業務報告・共有事項")
            lines.append("")
            
            if "ヒヤリハット事故" in report_data:
                lines.append(f"- **ヒヤリハット・事故**: {report_data['ヒヤリハット事故']}")
            
            if "発生場所" in report_data and report_data["発生場所"]:
                lines.append(f"- **発生場所**: {report_data['発生場所']}")
            if "対象者" in report_data and report_data["対象者"]:
                lines.append(f"- **対象者**: {report_data['対象者']}")
            if "事故発生の状況" in report_data and report_data["事故発生の状況"]:
                lines.append("### 事故発生の状況")
                lines.append(report_data["事故発生の状況"])
                lines.append("")
            if "経過" in report_data and report_data["経過"]:
                lines.append("### 経過")
                lines.append(report_data["経過"])
                lines.append("")
            if "事故原因" in report_data and report_data["事故原因"]:
                lines.append("### 事故原因")
                lines.append(report_data["事故原因"])
                lines.append("")
            if "対策" in report_data and report_data["対策"]:
                lines.append("### 対策")
                lines.append(report_data["対策"])
                lines.append("")
            if "その他" in report_data and report_data["その他"]:
                lines.append("### その他")
                lines.append(report_data["その他"])
                lines.append("")
            if "ヒヤリハット詳細" in report_data and report_data["ヒヤリハット詳細"]:
                lines.append("### ヒヤリハット詳細")
                lines.append(report_data["ヒヤリハット詳細"])
                lines.append("")
            
            if "申し送り事項" in report_data and report_data["申し送り事項"]:
                lines.append("### 申し送り事項")
                lines.append(report_data["申し送り事項"])
                lines.append("")
            if "備品購入要望" in report_data and report_data["備品購入要望"]:
                lines.append("### 備品購入・要望")
                lines.append(report_data["備品購入要望"])
                lines.append("")
        
        return "\n".join(lines)
    
    def get_saved_reports(self) -> List[Dict]:
        """
        保存済みのMarkdown形式の日報ファイル一覧を取得
        
        Returns:
            日報ファイル情報のリスト（ファイル名、パス、作成日時など）
        """
        reports = []
        if not self.reports_dir.exists():
            return reports
        
        for filepath in sorted(self.reports_dir.glob("*.md"), reverse=True):
            try:
                stat = filepath.stat()
                reports.append({
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size": stat.st_size
                })
            except Exception as e:
                print(f"ファイル情報取得エラー ({filepath}): {e}")
        
        return reports
    
    def load_report_markdown(self, filename: str) -> Optional[str]:
        """
        指定されたMarkdownファイルの内容を読み込む
        
        Args:
            filename: ファイル名
            
        Returns:
            Markdownファイルの内容（存在しない場合はNone）
        """
        filepath = self.reports_dir / filename
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Markdown読み込みエラー ({filepath}): {e}")
            return None
    
    def get_reports(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        日報データを取得
        
        Args:
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式）
            
        Returns:
            日報データのDataFrame
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.get_reports(start_date, end_date)
        
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
    
    def get_daily_user_count(self, target_date: str) -> int:
        """
        指定日の利用者数合計を取得
        
        Args:
            target_date: 対象日（YYYY-MM-DD形式）
            
        Returns:
            その日のユニークな利用者数
        """
        if not self.report_file.exists():
            return 0
        
        try:
            df = pd.read_csv(self.report_file, encoding='utf-8')
            
            if df.empty or "業務日" not in df.columns:
                return 0
            
            # 業務日を文字列形式に統一して比較（YYYY-MM-DD形式）
            # まず日付型に変換してから文字列に変換
            df["業務日_str"] = pd.to_datetime(df["業務日"]).dt.strftime("%Y-%m-%d")
            
            # 指定日も文字列形式に変換
            if isinstance(target_date, str):
                target_date_str = target_date
            else:
                target_date_str = target_date.isoformat() if hasattr(target_date, 'isoformat') else str(target_date)
            
            # 指定日のデータをフィルタリング
            daily_df = df[df["業務日_str"] == target_date_str]
            
            if daily_df.empty:
                return 0
            
            # ユニークな利用者名を収集
            unique_users = set()
            
            # 担当利用者名から取得
            if "担当利用者名" in daily_df.columns:
                for user_name in daily_df["担当利用者名"].dropna():
                    if user_name and str(user_name).strip():
                        unique_users.add(str(user_name).strip())
            
            # 送迎児童名から取得（カンマ区切りで複数名が記録されている可能性がある）
            if "送迎児童名" in daily_df.columns:
                for children_names in daily_df["送迎児童名"].dropna():
                    if children_names and str(children_names).strip():
                        # カンマ区切りで分割
                        names = [name.strip() for name in str(children_names).split(",")]
                        for name in names:
                            if name:
                                unique_users.add(name)
            
            return len(unique_users)
        except Exception as e:
            print(f"利用者数カウントエラー: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _init_tags_file(self):
        """タグマスタファイルが存在しない場合、初期化（既存データは保護）"""
        # 既存データを絶対に上書きしない
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
        else:
            # 既存データが存在する場合は、そのまま保持（上書きしない）
            pass
    
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
        if self._is_supabase_enabled():
            return self.supabase_manager.get_tags(tag_type)
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
        
        if self._is_supabase_enabled():
            return self.supabase_manager.add_tag(tag_type, tag_name)
        
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
        if self._is_supabase_enabled():
            return self.supabase_manager.delete_tag(tag_type, tag_name)
        
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
    
    def save_gemini_api_key(self, api_key: str) -> bool:
        """
        Gemini APIキーを保存
        
        Args:
            api_key: Gemini APIキー
            
        Returns:
            成功した場合True
        """
        try:
            config = self._load_config()
            config["gemini_api_key"] = api_key
            self._save_config(config)
            return True
        except Exception as e:
            print(f"Gemini APIキー保存エラー: {e}")
            return False
    
    def get_gemini_api_key(self) -> Optional[str]:
        """
        Gemini APIキーを取得
        
        Returns:
            APIキー（存在しない場合はNone）
        """
        config = self._load_config()
        return config.get("gemini_api_key")
    
    def delete_gemini_api_key(self) -> bool:
        """
        Gemini APIキーを削除
        
        Returns:
            成功した場合True
        """
        try:
            config = self._load_config()
            if "gemini_api_key" in config:
                del config["gemini_api_key"]
                self._save_config(config)
            return True
        except Exception as e:
            print(f"Gemini APIキー削除エラー: {e}")
            return False
    
    def _init_staff_accounts_file(self):
        """スタッフアカウントファイルが存在しない場合、初期化（既存データは保護）"""
        # 既存データを絶対に上書きしない
        if not self.staff_accounts_file.exists():
            default_accounts = []
            self._save_staff_accounts(default_accounts)
        else:
            # 既存データが存在する場合は、そのまま保持（上書きしない）
            pass
    
    def _load_staff_accounts(self) -> List[Dict]:
        """スタッフアカウントを読み込む"""
        try:
            with open(self.staff_accounts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _save_staff_accounts(self, accounts: List[Dict]):
        """スタッフアカウントを保存する"""
        with open(self.staff_accounts_file, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """パスワードをハッシュ化"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def create_staff_account(self, user_id: str, password: str, name: str) -> bool:
        """
        新しいスタッフアカウントを作成
        
        Args:
            user_id: ユーザーID
            password: パスワード（平文）
            name: スタッフ名
            
        Returns:
            成功した場合True
        """
        if not user_id or not password or not name:
            return False
        
        if self._is_supabase_enabled():
            return self.supabase_manager.create_staff_account(user_id, password, name)
        
        accounts = self._load_staff_accounts()
        
        # 重複チェック
        if any(acc["user_id"] == user_id for acc in accounts):
            return False
        
        # 新しいアカウントを作成
        new_account = {
            "user_id": user_id,
            "password_hash": self._hash_password(password),
            "name": name,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        
        accounts.append(new_account)
        self._save_staff_accounts(accounts)
        return True
    
    def verify_login(self, user_id: str, password: str) -> Optional[Dict]:
        """
        ログイン認証
        
        Args:
            user_id: ユーザーID
            password: パスワード（平文）
            
        Returns:
            認証成功時はアカウント情報の辞書、失敗時はNone
        """
        try:
            # 入力値の検証
            if not user_id or not password:
                print("ユーザーIDまたはパスワードが空です。")
                return None
            
            # Supabaseが有効な場合
            if self._is_supabase_enabled():
                try:
                    result = self.supabase_manager.verify_login(user_id, password)
                    return result
                except Exception as supabase_error:
                    print(f"Supabaseログイン認証エラー: {supabase_error}")
                    import traceback
                    traceback.print_exc()
                    raise  # エラーを上位に伝播
            
            # ローカルファイルストレージを使用する場合
            try:
                accounts = self._load_staff_accounts()
            except Exception as load_error:
                print(f"スタッフアカウントファイルの読み込みエラー: {load_error}")
                import traceback
                traceback.print_exc()
                raise
            
            if not accounts:
                print("スタッフアカウントが登録されていません。")
                return None
            
            password_hash = self._hash_password(password)
            
            # ユーザーIDで検索
            found_user_id = False
            for account in accounts:
                if account.get("user_id") == user_id:
                    found_user_id = True
                    # activeフラグをチェック
                    if not account.get("active", True):
                        print(f"ユーザーID '{user_id}' のアカウントは無効化されています。")
                        return None
                    # パスワードをチェック
                    if account.get("password_hash") == password_hash:
                        print(f"✅ ログイン成功: {account.get('name', 'Unknown')} ({user_id})")
                        return {
                            "user_id": account["user_id"],
                            "name": account["name"],
                            "created_at": account.get("created_at", "")
                        }
                    else:
                        print(f"ユーザーID '{user_id}' のパスワードが一致しません。")
                        return None
            
            if not found_user_id:
                print(f"ユーザーID '{user_id}' が見つかりません。")
                print(f"登録されているユーザーID数: {len(accounts)}")
                if accounts:
                    registered_ids = [acc.get("user_id", "N/A") for acc in accounts]
                    print(f"登録されているユーザーID: {registered_ids}")
            
            return None
        except Exception as e:
            print(f"ログイン認証処理中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            raise  # エラーを上位に伝播して、app.pyで適切に処理できるようにする
    
    def get_all_staff_accounts(self) -> List[Dict]:
        """全スタッフアカウント情報を取得（パスワードハッシュは除外）"""
        if self._is_supabase_enabled():
            return self.supabase_manager.get_all_staff_accounts()
        
        accounts = self._load_staff_accounts()
        return [
            {
                "user_id": acc["user_id"],
                "name": acc["name"],
                "created_at": acc.get("created_at", ""),
                "active": acc.get("active", True)
            }
            for acc in accounts
        ]
    
    def delete_staff_account(self, user_id: str) -> bool:
        """
        スタッフアカウントを削除（無効化）
        
        Args:
            user_id: 削除するユーザーID
            
        Returns:
            成功した場合True
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.delete_staff_account(user_id)
        
        accounts = self._load_staff_accounts()
        
        for account in accounts:
            if account["user_id"] == user_id:
                account["active"] = False
                account["deleted_at"] = datetime.now().isoformat()
                self._save_staff_accounts(accounts)
                return True
        
        return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        パスワードを変更
        
        Args:
            user_id: ユーザーID
            old_password: 現在のパスワード（平文）
            new_password: 新しいパスワード（平文）
            
        Returns:
            成功した場合True
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.change_password(user_id, old_password, new_password)
        
        accounts = self._load_staff_accounts()
        
        old_password_hash = self._hash_password(old_password)
        
        for account in accounts:
            if (account["user_id"] == user_id and 
                account["password_hash"] == old_password_hash):
                account["password_hash"] = self._hash_password(new_password)
                account["password_changed_at"] = datetime.now().isoformat()
                self._save_staff_accounts(accounts)
                return True
        
        return False
    
    def _init_morning_meeting_file(self):
        """朝礼議事録ファイルが存在しない場合、初期化（既存データは保護）"""
        # 既存データを絶対に上書きしない
        if not self.morning_meeting_file.exists():
            default_meetings = []
            self._save_morning_meetings(default_meetings)
        else:
            # 既存データが存在する場合は、そのまま保持（上書きしない）
            pass
    
    def _load_morning_meetings(self) -> List[Dict]:
        """朝礼議事録を読み込む"""
        try:
            with open(self.morning_meeting_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _save_morning_meetings(self, meetings: List[Dict]):
        """朝礼議事録を保存する"""
        with open(self.morning_meeting_file, 'w', encoding='utf-8') as f:
            json.dump(meetings, f, ensure_ascii=False, indent=2)
    
    def save_morning_meeting(self, meeting_data: Dict) -> bool:
        """
        朝礼議事録を保存
        
        Args:
            meeting_data: 朝礼議事録データの辞書
            
        Returns:
            成功した場合True
        """
        try:
            if self._is_supabase_enabled():
                return self.supabase_manager.save_morning_meeting(meeting_data)
            
            meetings = self._load_morning_meetings()
            
            # タイムスタンプを追加
            meeting_data["created_at"] = datetime.now().isoformat()
            
            # 新しい議事録を追加
            meetings.append(meeting_data)
            
            # 日付順にソート（新しい順）
            meetings.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            self._save_morning_meetings(meetings)
            return True
        except Exception as e:
            print(f"朝礼議事録保存エラー: {e}")
            return False
    
    def get_morning_meetings(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """
        朝礼議事録を取得
        
        Args:
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式）
            
        Returns:
            朝礼議事録のリスト
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.get_morning_meetings(start_date, end_date)
        
        meetings = self._load_morning_meetings()
        
        if start_date or end_date:
            filtered_meetings = []
            for meeting in meetings:
                meeting_date = meeting.get("日付", "")
                if isinstance(meeting_date, str):
                    try:
                        meeting_date_obj = datetime.fromisoformat(meeting_date).date()
                        if start_date:
                            start_date_obj = datetime.fromisoformat(start_date).date()
                            if meeting_date_obj < start_date_obj:
                                continue
                        if end_date:
                            end_date_obj = datetime.fromisoformat(end_date).date()
                            if meeting_date_obj > end_date_obj:
                                continue
                        filtered_meetings.append(meeting)
                    except:
                        continue
            return filtered_meetings
        
        return meetings
    
    def delete_morning_meeting(self, meeting_id: str) -> bool:
        """
        朝礼議事録を削除
        
        Args:
            meeting_id: 削除する議事録のID（created_atのタイムスタンプ）
            
        Returns:
            成功した場合True
        """
        try:
            meetings = self._load_morning_meetings()
            meetings = [m for m in meetings if m.get("created_at") != meeting_id]
            self._save_morning_meetings(meetings)
            return True
        except Exception as e:
            print(f"朝礼議事録削除エラー: {e}")
            return False
    
    def format_morning_meeting_as_markdown(self, meeting_data: Dict) -> str:
        """
        朝礼議事録データをMarkdown形式の文字列に変換
        
        Args:
            meeting_data: 朝礼議事録データの辞書
            
        Returns:
            Markdown形式の文字列
        """
        lines = []
        
        # タイトル
        meeting_date_str = meeting_data.get("日付", "")
        if meeting_date_str:
            try:
                date_obj = datetime.fromisoformat(meeting_date_str).date()
                lines.append(f"# {date_obj.strftime('%Y年%m月%d日')} の朝礼議事録")
            except:
                lines.append("# 朝礼議事録")
        else:
            lines.append("# 朝礼議事録")
        
        lines.append("")
        
        # 基本情報
        lines.append("## 基本情報")
        lines.append("")
        if "日付" in meeting_data:
            try:
                date_obj = datetime.fromisoformat(meeting_data["日付"]).date()
                lines.append(f"- **日付**: {date_obj.strftime('%Y年%m月%d日')}")
            except:
                lines.append(f"- **日付**: {meeting_data['日付']}")
        if "記入スタッフ名" in meeting_data:
            lines.append(f"- **記入スタッフ名**: {meeting_data['記入スタッフ名']}")
        if "created_at" in meeting_data:
            created_at = meeting_data['created_at']
            if isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    lines.append(f"- **作成日時**: {dt.strftime('%Y年%m月%d日 %H:%M:%S')}")
                except:
                    lines.append(f"- **作成日時**: {created_at}")
        lines.append("")
        
        # 議題・内容
        if "議題・内容" in meeting_data and meeting_data["議題・内容"]:
            lines.append("## 議題・内容")
            lines.append("")
            lines.append(meeting_data["議題・内容"])
            lines.append("")
        
        # 決定事項
        if "決定事項" in meeting_data and meeting_data["決定事項"]:
            lines.append("## 決定事項")
            lines.append("")
            lines.append(meeting_data["決定事項"])
            lines.append("")
        
        # 共有事項
        if "共有事項" in meeting_data and meeting_data["共有事項"]:
            lines.append("## 共有事項")
            lines.append("")
            lines.append(meeting_data["共有事項"])
            lines.append("")
        
        # その他メモ
        if "その他メモ" in meeting_data and meeting_data["その他メモ"]:
            lines.append("## その他メモ")
            lines.append("")
            lines.append(meeting_data["その他メモ"])
            lines.append("")
        
        return "\n".join(lines)
    
    def _init_daily_users_file(self):
        """日別利用者記録ファイルが存在しない場合、初期化（既存データは保護）"""
        # 既存データを絶対に上書きしない
        if not self.daily_users_file.exists():
            default_daily_users = {}
            self._save_daily_users(default_daily_users)
        else:
            # 既存データが存在する場合は、そのまま保持（上書きしない）
            pass
    
    def _load_daily_users(self) -> Dict[str, List[str]]:
        """日別利用者記録を読み込む"""
        try:
            with open(self.daily_users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_daily_users(self, daily_users: Dict[str, List[str]]):
        """日別利用者記録を保存する"""
        with open(self.daily_users_file, 'w', encoding='utf-8') as f:
            json.dump(daily_users, f, ensure_ascii=False, indent=2)
    
    def save_daily_users(self, target_date: str, user_names: List[str]) -> bool:
        """
        その日の利用者を保存
        
        Args:
            target_date: 対象日（YYYY-MM-DD形式）
            user_names: 利用者名のリスト
            
        Returns:
            成功した場合True
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.save_daily_users(target_date, user_names)
        
        try:
            daily_users = self._load_daily_users()
            # 日付をキーとして利用者名のリストを保存
            daily_users[target_date] = user_names
            self._save_daily_users(daily_users)
            return True
        except Exception as e:
            print(f"日別利用者記録保存エラー: {e}")
            return False
    
    def get_daily_users(self, target_date: str) -> List[str]:
        """
        その日の利用者一覧を取得
        
        Args:
            target_date: 対象日（YYYY-MM-DD形式）
            
        Returns:
            利用者名のリスト
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.get_daily_users(target_date)
        
        try:
            daily_users = self._load_daily_users()
            return daily_users.get(target_date, [])
        except Exception as e:
            print(f"日別利用者記録取得エラー: {e}")
            return []
    
    def get_all_daily_users(self) -> Dict[str, List[str]]:
        """
        全期間の利用者記録を取得
        
        Returns:
            日付をキーとした利用者名のリストの辞書
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.get_all_daily_users()
        
        try:
            return self._load_daily_users()
        except Exception as e:
            print(f"全期間利用者記録取得エラー: {e}")
            return {}
    
    def delete_daily_users(self, target_date: str) -> bool:
        """
        指定日の利用者記録を削除
        
        Args:
            target_date: 対象日（YYYY-MM-DD形式）
            
        Returns:
            成功した場合True
        """
        if self._is_supabase_enabled():
            return self.supabase_manager.delete_daily_users(target_date)
        
        try:
            daily_users = self._load_daily_users()
            if target_date in daily_users:
                del daily_users[target_date]
                self._save_daily_users(daily_users)
                return True
            return False
        except Exception as e:
            print(f"日別利用者記録削除エラー: {e}")
            return False
    
    def create_backup(self) -> Optional[str]:
        """
        データファイルのバックアップを作成
        コード更新（デプロイ）前に自動的に実行される
        
        Returns:
            バックアップディレクトリのパス（失敗時はNone）
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(exist_ok=True)
            
            # すべてのデータファイルをバックアップ
            data_files = [
                self.master_file,
                self.report_file,
                self.tags_file,
                self.config_file,
                self.staff_accounts_file,
                self.morning_meeting_file,
                self.daily_users_file,
                self.version_file  # スキーマバージョンファイルも含める
            ]
            
            backed_up_files = []
            for file_path in data_files:
                if file_path.exists():
                    try:
                        shutil.copy2(file_path, backup_path / file_path.name)
                        backed_up_files.append(file_path.name)
                    except Exception as e:
                        print(f"警告: {file_path.name} のバックアップに失敗: {e}")
            
            # reportsディレクトリもバックアップ
            if self.reports_dir.exists():
                try:
                    backup_reports_dir = backup_path / "reports"
                    shutil.copytree(self.reports_dir, backup_reports_dir, dirs_exist_ok=True)
                    backed_up_files.append(f"reports/ ({len(list(self.reports_dir.glob('*.md')))} files)")
                except Exception as e:
                    print(f"警告: reportsディレクトリのバックアップに失敗: {e}")
            
            # バックアップメタデータを保存
            metadata = {
                "timestamp": timestamp,
                "backup_date": datetime.now().isoformat(),
                "schema_version": self.SCHEMA_VERSION,
                "backed_up_files": backed_up_files,
                "data_dir": str(self.data_dir)
            }
            metadata_file = backup_path / ".backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 保護マーカーもバックアップ
            protection_marker = self.data_dir / ".data_protected"
            if protection_marker.exists():
                try:
                    shutil.copy2(protection_marker, backup_path / ".data_protected")
                except Exception:
                    pass
            
            return str(backup_path)
        except Exception as e:
            print(f"バックアップ作成エラー: {e}")
            return None
    
    def get_backup_list(self) -> List[Dict]:
        """
        バックアップ一覧を取得
        
        Returns:
            バックアップ情報のリスト
        """
        backups = []
        if not self.backup_dir.exists():
            return backups
        
        for backup_path in sorted(self.backup_dir.glob("backup_*"), reverse=True):
            if backup_path.is_dir():
                try:
                    stat = backup_path.stat()
                    backups.append({
                        "path": str(backup_path),
                        "name": backup_path.name,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "size": sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                    })
                except Exception as e:
                    print(f"バックアップ情報取得エラー ({backup_path}): {e}")
        
        return backups
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        バックアップからデータを復元
        
        Args:
            backup_path: バックアップディレクトリのパス
            
        Returns:
            成功した場合True
        """
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists() or not backup_dir.is_dir():
                return False
            
            # 復元前に現在のデータをバックアップ
            self.create_backup()
            
            # データファイルを復元
            for file_name in ["users_master.json", "daily_reports.csv", "tags_master.json", 
                            "config.json", "staff_accounts.json", "morning_meetings.json", "daily_users.json"]:
                backup_file = backup_dir / file_name
                if backup_file.exists():
                    target_file = self.data_dir / file_name
                    shutil.copy2(backup_file, target_file)
            
            # reportsディレクトリを復元
            backup_reports_dir = backup_dir / "reports"
            if backup_reports_dir.exists():
                if self.reports_dir.exists():
                    shutil.rmtree(self.reports_dir)
                shutil.copytree(backup_reports_dir, self.reports_dir)
            
            return True
        except Exception as e:
            print(f"バックアップ復元エラー: {e}")
            return False
    
    def export_all_data(self, export_path: Optional[str] = None) -> Optional[str]:
        """
        すべてのデータをZIPファイルにエクスポート
        
        Args:
            export_path: エクスポート先のパス（指定しない場合は一時ファイル）
            
        Returns:
            エクスポートされたZIPファイルのパス（失敗時はNone）
        """
        try:
            # エクスポート先のパスを決定
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = str(self.data_dir / f"data_export_{timestamp}.zip")
            
            export_file = Path(export_path)
            
            # ZIPファイルを作成
            with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # すべてのデータファイルをZIPに追加
                data_files = [
                    self.master_file,
                    self.report_file,
                    self.tags_file,
                    self.config_file,
                    self.staff_accounts_file,
                    self.morning_meeting_file,
                    self.daily_users_file,
                    self.version_file
                ]
                
                for file_path in data_files:
                    if file_path.exists():
                        # ファイルをZIPに追加（data/ディレクトリ内の相対パスを保持）
                        zipf.write(file_path, file_path.name)
                
                # reportsディレクトリ内のすべてのファイルを追加
                if self.reports_dir.exists():
                    for report_file in self.reports_dir.glob("*.md"):
                        zipf.write(report_file, f"reports/{report_file.name}")
                
                # エクスポートメタデータを追加
                metadata = {
                    "export_date": datetime.now().isoformat(),
                    "schema_version": self.SCHEMA_VERSION,
                    "data_dir": str(self.data_dir),
                    "exported_files": [
                        f.name for f in data_files if f.exists()
                    ]
                }
                metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
                zipf.writestr("export_metadata.json", metadata_json)
            
            return str(export_file)
        except Exception as e:
            print(f"データエクスポートエラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def import_all_data(self, import_file_path: str, overwrite: bool = False) -> bool:
        """
        ZIPファイルからすべてのデータをインポート
        
        Args:
            import_file_path: インポートするZIPファイルのパス
            overwrite: 既存データを上書きするか（Falseの場合は既存データを保護）
            
        Returns:
            成功した場合True
        """
        try:
            import_file = Path(import_file_path)
            if not import_file.exists():
                print(f"インポートファイルが見つかりません: {import_file_path}")
                return False
            
            # インポート前に現在のデータをバックアップ
            if not overwrite:
                self.create_backup()
            
            # ZIPファイルを一時ディレクトリに展開
            temp_dir = self.data_dir / "temp_import"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # ZIPファイルを展開
                with zipfile.ZipFile(import_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # メタデータを確認
                metadata_file = temp_dir / "export_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        print(f"インポートデータのエクスポート日時: {metadata.get('export_date', '不明')}")
                        print(f"スキーマバージョン: {metadata.get('schema_version', '不明')}")
                
                # データファイルをインポート
                data_files = [
                    ("users_master.json", self.master_file),
                    ("daily_reports.csv", self.report_file),
                    ("tags_master.json", self.tags_file),
                    ("config.json", self.config_file),
                    ("staff_accounts.json", self.staff_accounts_file),
                    ("morning_meetings.json", self.morning_meeting_file),
                    ("daily_users.json", self.daily_users_file),
                    (".schema_version", self.version_file)
                ]
                
                imported_files = []
                for source_name, target_file in data_files:
                    source_file = temp_dir / source_name
                    if source_file.exists():
                        if overwrite or not target_file.exists():
                            shutil.copy2(source_file, target_file)
                            imported_files.append(source_name)
                        else:
                            print(f"既存データを保護: {source_name} はスキップされました")
                
                # reportsディレクトリをインポート
                temp_reports_dir = temp_dir / "reports"
                if temp_reports_dir.exists():
                    if overwrite and self.reports_dir.exists():
                        shutil.rmtree(self.reports_dir)
                    if not self.reports_dir.exists():
                        self.reports_dir.mkdir(exist_ok=True)
                    
                    for report_file in temp_reports_dir.glob("*.md"):
                        target_report = self.reports_dir / report_file.name
                        if overwrite or not target_report.exists():
                            shutil.copy2(report_file, target_report)
                            imported_files.append(f"reports/{report_file.name}")
                
                print(f"インポート完了: {len(imported_files)} ファイルをインポートしました")
                
                # データ整合性チェック
                self._verify_data_integrity()
                
                return True
            finally:
                # 一時ディレクトリを削除
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            
        except Exception as e:
            print(f"データインポートエラー: {e}")
            import traceback
            traceback.print_exc()
            return False

