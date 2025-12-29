"""
データ管理モジュール
利用者マスタと日報データの永続化を担当
"""
import json
import os
import hashlib
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
        self.staff_accounts_file = self.data_dir / "staff_accounts.json"
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.morning_meeting_file = self.data_dir / "morning_meetings.json"
        
        # 利用者マスタの初期化
        self._init_master_file()
        # タグマスタの初期化
        self._init_tags_file()
        # スタッフアカウントの初期化
        self._init_staff_accounts_file()
        # 朝礼議事録の初期化
        self._init_morning_meeting_file()
    
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
        日報データを保存（CSVとMarkdown形式の両方）
        
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
            
            # CSV形式で保存
            df.to_csv(self.report_file, index=False, encoding='utf-8')
            
            # Markdown形式でも保存（担当利用者名または送迎区分がある場合）
            if ("担当利用者名" in report_data and report_data["担当利用者名"]) or \
               ("送迎区分" in report_data and report_data["送迎区分"]):
                self._save_report_as_markdown(report_data)
            
            return True
        except Exception as e:
            print(f"日報保存エラー: {e}")
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
    
    def _init_staff_accounts_file(self):
        """スタッフアカウントファイルが存在しない場合、初期化"""
        if not self.staff_accounts_file.exists():
            default_accounts = []
            self._save_staff_accounts(default_accounts)
    
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
        accounts = self._load_staff_accounts()
        
        password_hash = self._hash_password(password)
        
        for account in accounts:
            if (account["user_id"] == user_id and 
                account["password_hash"] == password_hash and 
                account.get("active", True)):
                # パスワードハッシュを返さない
                return {
                    "user_id": account["user_id"],
                    "name": account["name"],
                    "created_at": account.get("created_at", "")
                }
        
        return None
    
    def get_all_staff_accounts(self) -> List[Dict]:
        """全スタッフアカウント情報を取得（パスワードハッシュは除外）"""
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
        """朝礼議事録ファイルが存在しない場合、初期化"""
        if not self.morning_meeting_file.exists():
            default_meetings = []
            self._save_morning_meetings(default_meetings)
    
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

