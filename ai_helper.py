"""
AI文章生成アシストモジュール
grok-4-1-fast-reasoningを使用した文章生成機能
"""
import os
from typing import Optional
import requests


class AIHelper:
    """AI文章生成ヘルパークラス"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Grok APIキー（環境変数から取得する場合はNone）
        """
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.model = "grok-4-1-fast-reasoning"
    
    def is_available(self) -> bool:
        """APIキーが設定されているかチェック"""
        return self.api_key is not None and self.api_key.strip() != ""
    
    def generate_report_text(self, keywords: str, child_name: Optional[str] = None) -> tuple:
        """
        キーワードから日報形式の文章を生成
        
        Args:
            keywords: 箇条書きやキーワード
            child_name: 児童名（オプション）
            
        Returns:
            (成功フラグ, 生成された文章)
        """
        if not self.is_available():
            return False, "APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not keywords or not keywords.strip():
            return False, "キーワードを入力してください。"
        
        # 児童名の設定（デフォルトは「〇〇さん」）
        display_name = f"{child_name}さん" if child_name else "〇〇さん"
        
        # プロンプトの構築
        prompt = f"""#命令書 : 
あなたは、世界でトップで優秀な、プロの放課後等デイサービス、児童発達支援の児童指導員であり、世界でトップで優秀な認知科学者であり、世界でトップで優秀なプロの療育の専門家であり、世界でトップで優秀なプロの情報分析官です。放課後デイサービス、児童発達支援の最高の支援記録を作成してください。以下の要件に基づいて、入力したキーワードから気づいたことを抽出し、療育的、認知科学的側面からそれに関する今後の支援策を作成する。遠慮せずに、全力を尽くしてください。秀逸にultrahardに取り組んでください。

##要件:
・文字数は 300字程度 
・利用者の名前:{display_name}
・文章形式で簡潔に書く
・キーワードから課題を抽出して、解決策を導く
・療育的、認知科学的側面を加える
・常体で書く

キーワード:
{keywords}
"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたは、世界でトップで優秀な、プロの放課後等デイサービス、児童発達支援の児童指導員であり、世界でトップで優秀な認知科学者であり、世界でトップで優秀なプロの療育の専門家であり、世界でトップで優秀なプロの情報分析官です。放課後デイサービス、児童発達支援の最高の支援記録を作成するのが得意です。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result["choices"][0]["message"]["content"]
                return True, generated_text.strip()
            else:
                error_msg = f"APIエラー: {response.status_code} - {response.text}"
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, "APIへの接続がタイムアウトしました。しばらく待ってから再試行してください。"
        except requests.exceptions.RequestException as e:
            return False, f"API接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラーが発生しました: {str(e)}"
    
    def improve_text(self, text: str) -> tuple:
        """
        既存の文章を改善・推敲
        
        Args:
            text: 改善したい文章
            
        Returns:
            (成功フラグ, 改善された文章)
        """
        if not self.is_available():
            return False, "APIキーが設定されていません。"
        
        if not text or not text.strip():
            return False, "文章を入力してください。"
        
        prompt = f"""以下の日報の文章を、より自然で読みやすく、保護者に伝わりやすい表現に改善してください。

元の文章:
{text}

改善された文章のみを返してください。"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたは文章の推敲が得意な編集者です。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                improved_text = result["choices"][0]["message"]["content"]
                return True, improved_text.strip()
            else:
                error_msg = f"APIエラー: {response.status_code} - {response.text}"
                return False, error_msg
                
        except Exception as e:
            return False, f"エラーが発生しました: {str(e)}"
    
    def generate_accident_report(self, keywords: str, report_type: str = "situation") -> tuple:
        """
        事故報告書の各項目の文章を生成
        
        Args:
            keywords: 箇条書きやキーワード
            report_type: 生成する項目タイプ
                - "situation": 事故発生の状況
                - "process": 経過
                - "cause": 事故原因
                - "countermeasure": 対策
            
        Returns:
            (成功フラグ, 生成された文章)
        """
        if not self.is_available():
            return False, "APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not keywords or not keywords.strip():
            return False, "キーワードを入力してください。"
        
        type_descriptions = {
            "situation": "事故発生の状況",
            "process": "事故発生後の対応や経過",
            "cause": "事故の原因",
            "countermeasure": "今後の対策や防止策"
        }
        
        type_name = type_descriptions.get(report_type, "事故報告")
        
        prompt = f"""あなたは放課後等デイサービスのベテラン職員です。以下のキーワードや箇条書きを基に、{type_name}に関する文章を作成してください。

キーワード:
{keywords}

以下の点に注意してください:
- 客観的で正確な記述にする
- 具体的で分かりやすい表現を使う
- 専門用語は必要最小限にする
- 簡潔で読みやすい文章にする
- 常体で書く
- 300字程度で記述する

{type_name}に関する文章のみを返してください。"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたは放課後等デイサービスのベテラン職員で、事故報告書の作成が得意です。客観的で正確な記述を心がけます。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result["choices"][0]["message"]["content"]
                return True, generated_text.strip()
            else:
                error_msg = f"APIエラー: {response.status_code} - {response.text}"
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, "APIへの接続がタイムアウトしました。しばらく待ってから再試行してください。"
        except requests.exceptions.RequestException as e:
            return False, f"API接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラーが発生しました: {str(e)}"
    
    def generate_hiyari_hatto_report(self, keywords: str, report_type: str = "details") -> tuple:
        """
        ヒヤリハット報告書の各項目の文章を生成
        
        Args:
            keywords: 箇条書きやキーワード
            report_type: 生成する項目タイプ
                - "context": どうしていた時
                - "details": ヒヤリとした時のあらまし
                - "countermeasure": 教訓・対策
            
        Returns:
            (成功フラグ, 生成された文章)
        """
        if not self.is_available():
            return False, "APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not keywords or not keywords.strip():
            return False, "キーワードを入力してください。"
        
        type_descriptions = {
            "context": "どうしていた時（状況の説明）",
            "details": "ヒヤリとした時のあらまし（客観的な記述）",
            "countermeasure": "教訓・対策（具体的かつ実行可能なアクションプラン）"
        }
        
        type_name = type_descriptions.get(report_type, "ヒヤリハット報告")
        
        prompt = f"""あなたは放課後等デイサービスのベテラン職員です。以下のキーワードや箇条書きを基に、{type_name}に関する文章を作成してください。

キーワード:
{keywords}

以下の点に注意してください:
- 客観的で正確な記述にする
- 具体的で分かりやすい表現を使う
- 専門用語は必要最小限にする
- 簡潔で読みやすい文章にする
- 常体で書く
- 300字程度で記述する

{type_name}に関する文章のみを返してください。"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたは放課後等デイサービスのベテラン職員で、ヒヤリハット報告書の作成が得意です。客観的で正確な記述を心がけます。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result["choices"][0]["message"]["content"]
                return True, generated_text.strip()
            else:
                error_msg = f"APIエラー: {response.status_code} - {response.text}"
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, "APIへの接続がタイムアウトしました。しばらく待ってから再試行してください。"
        except requests.exceptions.RequestException as e:
            return False, f"API接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラーが発生しました: {str(e)}"

