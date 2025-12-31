"""
AI文章生成アシストモジュール
grok-4-1-fast-reasoningを使用した文章生成機能
Gemini 3 Flash Previewを使用した音声認識と議事録生成機能
"""
import os
from typing import Optional, Dict, Tuple
import requests

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class AIHelper:
    """AI文章生成ヘルパークラス"""
    
    def __init__(self, api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Grok APIキー（環境変数から取得する場合はNone）
            gemini_api_key: Gemini APIキー（環境変数から取得する場合はNone）
        """
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.model = "grok-4-1-fast-reasoning"
        
        # Gemini API設定
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if GEMINI_AVAILABLE and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
    
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
                # 100字以内に制限
                generated_text = generated_text.strip()
                if len(generated_text) > 100:
                    generated_text = generated_text[:100]
                return True, generated_text
            else:
                error_msg = f"APIエラー: {response.status_code} - {response.text}"
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, "APIへの接続がタイムアウトしました。しばらく待ってから再試行してください。"
        except requests.exceptions.RequestException as e:
            return False, f"API接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラーが発生しました: {str(e)}"
    
    def is_gemini_available(self) -> bool:
        """Gemini APIキーが設定されているかチェック"""
        return GEMINI_AVAILABLE and self.gemini_api_key is not None and self.gemini_api_key.strip() != ""
    
    def _ensure_gemini_configured(self):
        """Gemini APIキーが正しく設定されているか確認し、必要に応じて設定する"""
        if not GEMINI_AVAILABLE or not self.gemini_api_key:
            return False
        
        try:
            # APIキーをクリーンアップ（余分な空白や改行を削除）
            api_key = self.gemini_api_key.strip()
            # 複数のAPIキーが結合されている可能性があるため、最初の有効なキーのみを使用
            if ' ' in api_key:
                # スペースで区切られている場合、最初の部分のみを使用
                api_key = api_key.split()[0]
            
            # genai.configure()を再呼び出して、最新のAPIキーを設定
            genai.configure(api_key=api_key)
            self.gemini_api_key = api_key
            return True
        except Exception:
            return False
    
    def transcribe_audio_to_text(self, audio_file_path: str, context_info: Optional[str] = None) -> Tuple[bool, str]:
        """
        音声ファイルをテキストに変換（Gemini 3 Flash Preview使用）
        
        Args:
            audio_file_path: 音声ファイルのパス
            context_info: 補助情報（名前、固有名詞など）を記載したテキスト
            
        Returns:
            (成功フラグ, 変換されたテキストまたはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not os.path.exists(audio_file_path):
            return False, "音声ファイルが見つかりません。"
        
        # APIキーが正しく設定されているか確認
        if not self._ensure_gemini_configured():
            return False, "Gemini APIキーの設定に失敗しました。設定画面でAPIキーを確認してください。"
        
        try:
            # ファイル拡張子からMIMEタイプを判定
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            mime_types = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.m4a': 'audio/mp4',
                '.ogg': 'audio/ogg',
                '.flac': 'audio/flac',
                '.webm': 'audio/webm'
            }
            mime_type = mime_types.get(file_ext, 'audio/mpeg')
            
            # Gemini 3 Flash Previewを使用して音声をテキストに変換
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            # 音声ファイルをアップロード
            audio_file_obj = genai.upload_file(
                path=audio_file_path,
                mime_type=mime_type
            )
            
            # プロンプトを設定
            prompt = """この音声は朝礼の議事録です。音声の内容を正確にテキストに変換してください。
話し手の言葉をそのまま記録し、言いよどみや繰り返しも含めて正確に書き起こしてください。
不要な編集は行わず、話された内容を忠実に記録してください。"""
            
            # 補助情報がある場合はプロンプトに追加
            if context_info and context_info.strip():
                prompt += f"""

以下の情報を参考にして、音声内の名前や固有名詞の認識精度を向上させてください：
{context_info}

これらの情報を参考にしながら、音声の内容を正確にテキストに変換してください。"""
            
            # 音声認識を実行
            response = model.generate_content([prompt, audio_file_obj])
            
            # テキストを取得
            transcribed_text = response.text.strip()
            
            # アップロードしたファイルを削除
            genai.delete_file(audio_file_obj.name)
            
            return True, transcribed_text
            
        except Exception as e:
            return False, f"音声認識エラー: {str(e)}"
    
    def generate_meeting_minutes_from_audio(self, audio_file_path: str, context_info: Optional[str] = None) -> Tuple[bool, Dict[str, str]]:
        """
        音声ファイルから朝礼議事録を生成（Gemini 3 Flash Preview使用）
        
        Args:
            audio_file_path: 音声ファイルのパス
            context_info: 補助情報（名前、固有名詞など）を記載したテキスト
            
        Returns:
            (成功フラグ, 議事録データの辞書またはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not os.path.exists(audio_file_path):
            return False, "音声ファイルが見つかりません。"
        
        try:
            # まず音声をテキストに変換（補助情報を含める）
            success, transcribed_text = self.transcribe_audio_to_text(audio_file_path, context_info)
            if not success:
                return False, transcribed_text
            
            # テキストから議事録を構造化
            return self.generate_meeting_minutes_from_text(transcribed_text)
            
        except Exception as e:
            return False, f"議事録生成エラー: {str(e)}"
    
    def generate_meeting_minutes_from_text(self, text: str) -> Tuple[bool, Dict[str, str]]:
        """
        テキストから朝礼議事録を構造化して生成（Gemini 3 Flash Preview使用）
        
        Args:
            text: 議事録の元となるテキスト
            
        Returns:
            (成功フラグ, 議事録データの辞書またはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not text or not text.strip():
            return False, "テキストが空です。"
        
        # APIキーが正しく設定されているか確認
        if not self._ensure_gemini_configured():
            return False, "Gemini APIキーの設定に失敗しました。設定画面でAPIキーを確認してください。"
        
        try:
            # Gemini 3 Flash Previewを使用して議事録を構造化
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            prompt = f"""以下の朝礼の音声を書き起こしたテキストから、朝礼議事録を作成してください。

音声テキスト:
{text}

以下の形式でJSON形式で出力してください。各項目は適切に整理し、必要に応じて要約してください。

{{
    "議題・内容": "朝礼で話し合った主な議題や内容をまとめて記述してください",
    "決定事項": "決定した事項があれば箇条書きで記述してください。なければ空文字列にしてください",
    "共有事項": "スタッフ間で共有すべき事項を箇条書きで記述してください。なければ空文字列にしてください",
    "その他メモ": "その他の重要なメモがあれば記述してください。なければ空文字列にしてください"
}}

注意事項:
- 音声の内容を正確に反映してください
- 重要な情報を見落とさないようにしてください
- 各項目は適切に整理し、読みやすくしてください
- JSON形式のみを返してください（説明文は不要）
- 日本語で記述してください
"""
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            # JSONをパース
            import json
            import re
            
            response_text = response.text.strip()
            
            # JSON部分を抽出（コードブロックがあれば除去）
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
            
            # JSONをパース
            meeting_data = json.loads(json_str)
            
            # 必須フィールドの確認
            if "議題・内容" not in meeting_data:
                meeting_data["議題・内容"] = text[:500]  # フォールバック
            
            # 空のフィールドを空文字列に設定
            for key in ["決定事項", "共有事項", "その他メモ"]:
                if key not in meeting_data:
                    meeting_data[key] = ""
            
            # 議題・内容から短いタイトルを生成（必ず「の件」形式）
            if "議題・内容" in meeting_data and meeting_data["議題・内容"]:
                title_success, title = self.generate_title_from_text(meeting_data["議題・内容"])
                if title_success and title:
                    # 強制的に「の件」形式に変換（最終的な保証）
                    meeting_data["タイトル"] = self.ensure_title_format(title, meeting_data["議題・内容"])
                else:
                    # フォールバック: 簡易的にタイトルを生成（必ず「の件」形式）
                    meeting_data["タイトル"] = self.ensure_title_format("", meeting_data["議題・内容"])
            
            return True, meeting_data
            
        except json.JSONDecodeError as e:
            # JSONパースエラーの場合、テキストをそのまま議題・内容として使用
            meeting_data = {
                "議題・内容": text[:1000] if len(text) > 1000 else text,
                "決定事項": "",
                "共有事項": "",
                "その他メモ": ""
            }
            # 議題・内容から短いタイトルを生成（必ず「の件」形式）
            if meeting_data["議題・内容"]:
                title_success, title = self.generate_title_from_text(meeting_data["議題・内容"])
                if title_success and title:
                    # 強制的に「の件」形式に変換（最終的な保証）
                    meeting_data["タイトル"] = self.ensure_title_format(title, meeting_data["議題・内容"])
                else:
                    # フォールバック: 簡易的にタイトルを生成（必ず「の件」形式）
                    meeting_data["タイトル"] = self.ensure_title_format("", meeting_data["議題・内容"])
            return True, meeting_data
        except Exception as e:
            return False, f"議事録生成エラー: {str(e)}"
    
    def ensure_title_format(self, title: str, source_text: str = "") -> str:
        """
        タイトルが必ず「の件」形式になることを保証する（最終的な強制処理）
        
        Args:
            title: 処理前のタイトル
            source_text: 元のテキスト（フォールバック用）
            
        Returns:
            「の件」形式で終わるタイトル
        """
        if not title or not title.strip():
            # タイトルが空の場合は、元のテキストから生成
            if source_text:
                title = source_text.strip()[:18]
                for delimiter in ['。', '、', '\n', '.', ',', '：', ':', '・', 'について', 'に関して']:
                    if delimiter in title:
                        title = title.split(delimiter)[0]
                        break
            else:
                title = "議事録の件"
        
        # 余分な文字を削除
        title = title.strip()
        title = title.replace('"', '').replace("'", '').replace('「', '').replace('」', '').replace('【', '').replace('】', '').replace('（', '').replace('）', '').replace('(', '').replace(')', '')
        title = ' '.join(title.split())
        title = title.replace('\n', '').replace('\r', '').replace('\t', '')
        
        # 説明文や補足を削除
        for marker in ['例:', '注意:', '出力:', 'タイトル:', '件名:', '件:', '：', ':', '出力例', '例文']:
            if marker in title:
                title = title.split(marker)[-1].strip()
        
        # 「の件」が途中にある場合は、その前の部分を取得
        if "の件" in title and not title.endswith("の件"):
            parts = title.split("の件")
            if parts[0]:
                title = parts[0] + "の件"
            else:
                title = "の件"
        
        # 20文字以内に制限（「の件」を含む）
        if len(title) > 20:
            if title.endswith("の件"):
                main_part = title[:-2]
                if len(main_part) > 18:
                    main_part = main_part[:18]
                title = main_part + "の件"
            else:
                title = title[:18] + "の件"
        
        # 最終確認: 必ず「の件」で終わることを強制
        if not title.endswith("の件"):
            # 「の件」を除いた部分を取得
            if "の件" in title:
                title = title.split("の件")[0] + "の件"
            else:
                title = title + "の件"
        
        # 空文字列や「の件」だけの場合はフォールバック
        if not title or title == "の件" or len(title) < 3:
            if source_text:
                fallback = source_text.strip()[:18]
                for delimiter in ['。', '、', '\n', '.', ',', '：', ':', '・', 'について', 'に関して']:
                    if delimiter in fallback:
                        fallback = fallback.split(delimiter)[0]
                        break
                title = fallback + "の件" if fallback else "議事録の件"
            else:
                title = "議事録の件"
        
        return title
    
    def generate_title_from_text(self, text: str) -> tuple:
        """
        テキストから短いタイトルを生成（「○○の件」形式）
        
        Args:
            text: 元となるテキスト（議題・内容など）
            
        Returns:
            (成功フラグ, 生成されたタイトル)
        """
        if not self.is_available():
            # APIキーがない場合は、テキストから簡易的にタイトルを生成（必ず「の件」形式）
            if not text or not text.strip():
                return False, ""
            
            # テキストの最初の18文字程度を取得
            title = text.strip()[:18]
            # 句読点や改行で区切る
            for delimiter in ['。', '、', '\n', '.', ',', '：', ':', '・', 'について', 'に関して']:
                if delimiter in title:
                    title = title.split(delimiter)[0]
                    break
            
            # 強制的に「の件」形式に変換（最終的な保証）
            title = self.ensure_title_format(title, text.strip())
            
            return True, title
        
        if not text or not text.strip():
            return False, ""
        
        # テキストを前処理（最初の100文字程度を取得）
        text_preview = text.strip()[:100]
        for delimiter in ['。', '、', '\n', '.', ',', '：', ':', '・', 'について', 'に関して']:
            if delimiter in text_preview:
                text_preview = text_preview.split(delimiter)[0]
                break
        
        prompt = f"""#命令書（絶対遵守・違反不可）
あなたは、世界でトップで優秀な、プロのタイトル生成の専門家です。遠慮せずに、全力を尽くしてください。秀逸にultrahardに取り組んでください。

##最重要ルール（絶対遵守・違反不可）:
1. 出力は必ず「○○の件」という形式で終わること（「の件」で終わらない場合は無効・絶対禁止）
2. 「の件」以外の文字列は一切返さないこと（説明文、補足、例、注意書きは一切不要）
3. タイトルのみを返すこと（引用符、括弧、改行、空白行は一切不要）
4. 20文字以内（「の件」を含む）にまとめること

##入力議題・内容:
{text}

##正しい出力例（この形式のみ有効・必ずこの形式で返すこと）:
利用者送迎に関する件
スタッフ会議の件
設備点検の件
安全確認の件
利用者対応の件
送迎業務の件

##間違った出力例（絶対に返さないこと）:
利用者送迎について
スタッフ会議
設備点検に関する報告
安全確認についての件名
「利用者送迎の件」
【スタッフ会議の件】

##禁止事項（絶対に守ること・違反不可）:
- 「の件」で終わらないタイトルは返さない（絶対禁止）
- 説明文や補足を付けない（絶対禁止）
- 引用符や括弧で囲まない（絶対禁止）
- 改行を入れない（絶対禁止）
- 「について」「に関して」などの語尾は使わない（「の件」のみ使用）

##出力指示:
上記の正しい出力例の形式で、タイトルのみを「○○の件」形式で返してください。
議題・内容から重要なキーワードを抽出し、「○○の件」という形式で返してください。"""
        
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
                        "content": "あなたは、世界でトップで優秀な、プロのタイトル生成の専門家です。議題・内容から必ず「○○の件」という形式のタイトルを生成します。遠慮せずに、全力を尽くしてください。秀逸にultrahardに取り組んでください。\n\n最重要ルール（絶対遵守）: タイトルは必ず「の件」で終わる形式で返してください。「の件」で終わらないタイトルは絶対に返さないでください。説明文や補足は一切不要です。タイトルのみを返してください。引用符、括弧、改行は一切使用しないでください。"
                    },
                    {
                        "role": "user",
                        "content": "議題: 利用者送迎について話し合った\nタイトルを生成してください。"
                    },
                    {
                        "role": "assistant",
                        "content": "利用者送迎に関する件"
                    },
                    {
                        "role": "user",
                        "content": "議題: スタッフ会議で今後の方針を決定した\nタイトルを生成してください。"
                    },
                    {
                        "role": "assistant",
                        "content": "スタッフ会議の件"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.05,
                "max_tokens": 25
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_title = result["choices"][0]["message"]["content"].strip()
                
                # 強制的に「の件」形式に変換（最終的な保証）
                title = self.ensure_title_format(raw_title, text_preview)
                
                # 最終確認: 必ず「の件」で終わることを確認（二重チェック）
                if not title.endswith("の件"):
                    title = self.ensure_title_format("", text.strip())
                
                return True, title
            else:
                # APIエラーの場合は簡易的にタイトルを生成（必ず「の件」で終わる）
                title = self.ensure_title_format("", text.strip())
                return True, title
                
        except Exception as e:
            # エラーの場合は簡易的にタイトルを生成（必ず「の件」で終わる）
            title = self.ensure_title_format("", text.strip())
            return True, title
    
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
- 100字以内で記述する（厳守）

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
                # 100字以内に制限
                generated_text = generated_text.strip()
                if len(generated_text) > 100:
                    generated_text = generated_text[:100]
                return True, generated_text
            else:
                error_msg = f"APIエラー: {response.status_code} - {response.text}"
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, "APIへの接続がタイムアウトしました。しばらく待ってから再試行してください。"
        except requests.exceptions.RequestException as e:
            return False, f"API接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラーが発生しました: {str(e)}"
    
    def generate_report_content(self, keywords: str) -> tuple:
        """
        報告内容の短い文章を生成
        
        Args:
            keywords: 箇条書きやキーワード
            
        Returns:
            (成功フラグ, 生成された文章)
        """
        if not self.is_available():
            return False, "APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not keywords or not keywords.strip():
            return False, "キーワードを入力してください。"
        
        prompt = f"""あなたは放課後等デイサービスのベテラン職員です。以下のキーワードや箇条書きを基に、報告内容の短い要約文を作成してください。

キーワード:
{keywords}

以下の点に注意してください:
- 簡潔で分かりやすい表現を使う
- 専門用語は必要最小限にする
- 50字以内で記述する（厳守）
- 常体で書く

報告内容の要約文のみを返してください。"""
        
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
                        "content": "あなたは放課後等デイサービスのベテラン職員で、報告内容の要約が得意です。簡潔で分かりやすい文章を作成します。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result["choices"][0]["message"]["content"].strip()
                # 50字以内に制限
                if len(generated_text) > 50:
                    generated_text = generated_text[:50]
                return True, generated_text
            else:
                error_msg = f"APIエラー: {response.status_code}"
                try:
                    error_detail = response.json()
                    if "error" in error_detail:
                        error_msg = error_detail["error"].get("message", error_msg)
                except:
                    pass
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, "APIへの接続がタイムアウトしました。しばらく待ってから再試行してください。"
        except requests.exceptions.RequestException as e:
            return False, f"API接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラーが発生しました: {str(e)}"


    def is_gemini_available(self) -> bool:
        """Gemini APIキーが設定されているかチェック"""
        return GEMINI_AVAILABLE and self.gemini_api_key is not None and self.gemini_api_key.strip() != ""
    
    def _ensure_gemini_configured(self):
        """Gemini APIキーが正しく設定されているか確認し、必要に応じて設定する"""
        if not GEMINI_AVAILABLE or not self.gemini_api_key:
            return False
        
        try:
            # APIキーをクリーンアップ（余分な空白や改行を削除）
            api_key = self.gemini_api_key.strip()
            # 複数のAPIキーが結合されている可能性があるため、最初の有効なキーのみを使用
            if ' ' in api_key:
                # スペースで区切られている場合、最初の部分のみを使用
                api_key = api_key.split()[0]
            
            # genai.configure()を再呼び出して、最新のAPIキーを設定
            genai.configure(api_key=api_key)
            self.gemini_api_key = api_key
            return True
        except Exception:
            return False
    
    def transcribe_audio_to_text(self, audio_file_path: str, context_info: Optional[str] = None) -> Tuple[bool, str]:
        """
        音声ファイルをテキストに変換（Gemini 3 Flash Preview使用）
        
        Args:
            audio_file_path: 音声ファイルのパス
            context_info: 補助情報（名前、固有名詞など）を記載したテキスト
            
        Returns:
            (成功フラグ, 変換されたテキストまたはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not os.path.exists(audio_file_path):
            return False, "音声ファイルが見つかりません。"
        
        # APIキーが正しく設定されているか確認
        if not self._ensure_gemini_configured():
            return False, "Gemini APIキーの設定に失敗しました。設定画面でAPIキーを確認してください。"
        
        try:
            # ファイル拡張子からMIMEタイプを判定
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            mime_types = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.m4a': 'audio/mp4',
                '.ogg': 'audio/ogg',
                '.flac': 'audio/flac',
                '.webm': 'audio/webm'
            }
            mime_type = mime_types.get(file_ext, 'audio/mpeg')
            
            # Gemini 3 Flash Previewを使用して音声をテキストに変換
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            # 音声ファイルをアップロード
            audio_file_obj = genai.upload_file(
                path=audio_file_path,
                mime_type=mime_type
            )
            
            # プロンプトを設定
            prompt = """この音声は朝礼の議事録です。音声の内容を正確にテキストに変換してください。
話し手の言葉をそのまま記録し、言いよどみや繰り返しも含めて正確に書き起こしてください。
不要な編集は行わず、話された内容を忠実に記録してください。"""
            
            # 補助情報がある場合はプロンプトに追加
            if context_info and context_info.strip():
                prompt += f"""

以下の情報を参考にして、音声内の名前や固有名詞の認識精度を向上させてください：
{context_info}

これらの情報を参考にしながら、音声の内容を正確にテキストに変換してください。"""
            
            # 音声認識を実行
            response = model.generate_content([prompt, audio_file_obj])
            
            # テキストを取得
            transcribed_text = response.text.strip()
            
            # アップロードしたファイルを削除
            genai.delete_file(audio_file_obj.name)
            
            return True, transcribed_text
            
        except Exception as e:
            return False, f"音声認識エラー: {str(e)}"
    
    def generate_meeting_minutes_from_audio(self, audio_file_path: str, context_info: Optional[str] = None) -> Tuple[bool, Dict[str, str]]:
        """
        音声ファイルから朝礼議事録を生成（Gemini 3 Flash Preview使用）
        
        Args:
            audio_file_path: 音声ファイルのパス
            context_info: 補助情報（名前、固有名詞など）を記載したテキスト
            
        Returns:
            (成功フラグ, 議事録データの辞書またはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not os.path.exists(audio_file_path):
            return False, "音声ファイルが見つかりません。"
        
        try:
            # まず音声をテキストに変換（補助情報を含める）
            success, transcribed_text = self.transcribe_audio_to_text(audio_file_path, context_info)
            if not success:
                return False, transcribed_text
            
            # テキストから議事録を構造化
            return self.generate_meeting_minutes_from_text(transcribed_text)
            
        except Exception as e:
            return False, f"議事録生成エラー: {str(e)}"
    
    def generate_meeting_minutes_from_text(self, text: str) -> Tuple[bool, Dict[str, str]]:
        """
        テキストから朝礼議事録を構造化して生成（Gemini 3 Flash Preview使用）
        
        Args:
            text: 議事録の元となるテキスト
            
        Returns:
            (成功フラグ, 議事録データの辞書またはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not text or not text.strip():
            return False, "テキストが空です。"
        
        # APIキーが正しく設定されているか確認
        if not self._ensure_gemini_configured():
            return False, "Gemini APIキーの設定に失敗しました。設定画面でAPIキーを確認してください。"
        
        try:
            # Gemini 3 Flash Previewを使用して議事録を構造化
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            prompt = f"""以下の朝礼の音声を書き起こしたテキストから、朝礼議事録を作成してください。

音声テキスト:
{text}

以下の形式でJSON形式で出力してください。各項目は適切に整理し、必要に応じて要約してください。

{{
    "議題・内容": "朝礼で話し合った主な議題や内容をまとめて記述してください",
    "決定事項": "決定した事項があれば箇条書きで記述してください。なければ空文字列にしてください",
    "共有事項": "スタッフ間で共有すべき事項を箇条書きで記述してください。なければ空文字列にしてください",
    "その他メモ": "その他の重要なメモがあれば記述してください。なければ空文字列にしてください"
}}

注意事項:
- 音声の内容を正確に反映してください
- 重要な情報を見落とさないようにしてください
- 各項目は適切に整理し、読みやすくしてください
- JSON形式のみを返してください（説明文は不要）
- 日本語で記述してください
"""
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            # JSONをパース
            import json
            import re
            
            response_text = response.text.strip()
            
            # JSON部分を抽出（コードブロックがあれば除去）
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
            
            # JSONをパース
            meeting_data = json.loads(json_str)
            
            # 必須フィールドの確認
            if "議題・内容" not in meeting_data:
                meeting_data["議題・内容"] = text[:500]  # フォールバック
            
            # 空のフィールドを空文字列に設定
            for key in ["決定事項", "共有事項", "その他メモ"]:
                if key not in meeting_data:
                    meeting_data[key] = ""
            
            return True, meeting_data
            
        except json.JSONDecodeError as e:
            # JSONパースエラーの場合、テキストをそのまま議題・内容として使用
            return True, {
                "議題・内容": text[:1000] if len(text) > 1000 else text,
                "決定事項": "",
                "共有事項": "",
                "その他メモ": ""
            }
        except Exception as e:
            return False, f"議事録生成エラー: {str(e)}"
    
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
- 100字以内で記述する（厳守）

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
                # 100字以内に制限
                generated_text = generated_text.strip()
                if len(generated_text) > 100:
                    generated_text = generated_text[:100]
                return True, generated_text
            else:
                error_msg = f"APIエラー: {response.status_code} - {response.text}"
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, "APIへの接続がタイムアウトしました。しばらく待ってから再試行してください。"
        except requests.exceptions.RequestException as e:
            return False, f"API接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラーが発生しました: {str(e)}"
    
    def is_gemini_available(self) -> bool:
        """Gemini APIキーが設定されているかチェック"""
        return GEMINI_AVAILABLE and self.gemini_api_key is not None and self.gemini_api_key.strip() != ""
    
    def _ensure_gemini_configured(self):
        """Gemini APIキーが正しく設定されているか確認し、必要に応じて設定する"""
        if not GEMINI_AVAILABLE or not self.gemini_api_key:
            return False
        
        try:
            # APIキーをクリーンアップ（余分な空白や改行を削除）
            api_key = self.gemini_api_key.strip()
            # 複数のAPIキーが結合されている可能性があるため、最初の有効なキーのみを使用
            if ' ' in api_key:
                # スペースで区切られている場合、最初の部分のみを使用
                api_key = api_key.split()[0]
            
            # genai.configure()を再呼び出して、最新のAPIキーを設定
            genai.configure(api_key=api_key)
            self.gemini_api_key = api_key
            return True
        except Exception:
            return False
    
    def transcribe_audio_to_text(self, audio_file_path: str, context_info: Optional[str] = None) -> Tuple[bool, str]:
        """
        音声ファイルをテキストに変換（Gemini 3 Flash Preview使用）
        
        Args:
            audio_file_path: 音声ファイルのパス
            context_info: 補助情報（名前、固有名詞など）を記載したテキスト
            
        Returns:
            (成功フラグ, 変換されたテキストまたはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not os.path.exists(audio_file_path):
            return False, "音声ファイルが見つかりません。"
        
        # APIキーが正しく設定されているか確認
        if not self._ensure_gemini_configured():
            return False, "Gemini APIキーの設定に失敗しました。設定画面でAPIキーを確認してください。"
        
        try:
            # ファイル拡張子からMIMEタイプを判定
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            mime_types = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.m4a': 'audio/mp4',
                '.ogg': 'audio/ogg',
                '.flac': 'audio/flac',
                '.webm': 'audio/webm'
            }
            mime_type = mime_types.get(file_ext, 'audio/mpeg')
            
            # Gemini 3 Flash Previewを使用して音声をテキストに変換
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            # 音声ファイルをアップロード
            audio_file_obj = genai.upload_file(
                path=audio_file_path,
                mime_type=mime_type
            )
            
            # プロンプトを設定
            prompt = """この音声は朝礼の議事録です。音声の内容を正確にテキストに変換してください。
話し手の言葉をそのまま記録し、言いよどみや繰り返しも含めて正確に書き起こしてください。
不要な編集は行わず、話された内容を忠実に記録してください。"""
            
            # 補助情報がある場合はプロンプトに追加
            if context_info and context_info.strip():
                prompt += f"""

以下の情報を参考にして、音声内の名前や固有名詞の認識精度を向上させてください：
{context_info}

これらの情報を参考にしながら、音声の内容を正確にテキストに変換してください。"""
            
            # 音声認識を実行
            response = model.generate_content([prompt, audio_file_obj])
            
            # テキストを取得
            transcribed_text = response.text.strip()
            
            # アップロードしたファイルを削除
            genai.delete_file(audio_file_obj.name)
            
            return True, transcribed_text
            
        except Exception as e:
            return False, f"音声認識エラー: {str(e)}"
    
    def generate_meeting_minutes_from_audio(self, audio_file_path: str, context_info: Optional[str] = None) -> Tuple[bool, Dict[str, str]]:
        """
        音声ファイルから朝礼議事録を生成（Gemini 3 Flash Preview使用）
        
        Args:
            audio_file_path: 音声ファイルのパス
            context_info: 補助情報（名前、固有名詞など）を記載したテキスト
            
        Returns:
            (成功フラグ, 議事録データの辞書またはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not os.path.exists(audio_file_path):
            return False, "音声ファイルが見つかりません。"
        
        try:
            # まず音声をテキストに変換（補助情報を含める）
            success, transcribed_text = self.transcribe_audio_to_text(audio_file_path, context_info)
            if not success:
                return False, transcribed_text
            
            # テキストから議事録を構造化
            return self.generate_meeting_minutes_from_text(transcribed_text)
            
        except Exception as e:
            return False, f"議事録生成エラー: {str(e)}"
    
    def generate_meeting_minutes_from_text(self, text: str) -> Tuple[bool, Dict[str, str]]:
        """
        テキストから朝礼議事録を構造化して生成（Gemini 3 Flash Preview使用）
        
        Args:
            text: 議事録の元となるテキスト
            
        Returns:
            (成功フラグ, 議事録データの辞書またはエラーメッセージ)
        """
        if not self.is_gemini_available():
            return False, "Gemini APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        if not text or not text.strip():
            return False, "テキストが空です。"
        
        # APIキーが正しく設定されているか確認
        if not self._ensure_gemini_configured():
            return False, "Gemini APIキーの設定に失敗しました。設定画面でAPIキーを確認してください。"
        
        try:
            # Gemini 3 Flash Previewを使用して議事録を構造化
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            prompt = f"""以下の朝礼の音声を書き起こしたテキストから、朝礼議事録を作成してください。

音声テキスト:
{text}

以下の形式でJSON形式で出力してください。各項目は適切に整理し、必要に応じて要約してください。

{{
    "議題・内容": "朝礼で話し合った主な議題や内容をまとめて記述してください",
    "決定事項": "決定した事項があれば箇条書きで記述してください。なければ空文字列にしてください",
    "共有事項": "スタッフ間で共有すべき事項を箇条書きで記述してください。なければ空文字列にしてください",
    "その他メモ": "その他の重要なメモがあれば記述してください。なければ空文字列にしてください"
}}

注意事項:
- 音声の内容を正確に反映してください
- 重要な情報を見落とさないようにしてください
- 各項目は適切に整理し、読みやすくしてください
- JSON形式のみを返してください（説明文は不要）
- 日本語で記述してください
"""
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            # JSONをパース
            import json
            import re
            
            response_text = response.text.strip()
            
            # JSON部分を抽出（コードブロックがあれば除去）
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
            
            # JSONをパース
            meeting_data = json.loads(json_str)
            
            # 必須フィールドの確認
            if "議題・内容" not in meeting_data:
                meeting_data["議題・内容"] = text[:500]  # フォールバック
            
            # 空のフィールドを空文字列に設定
            for key in ["決定事項", "共有事項", "その他メモ"]:
                if key not in meeting_data:
                    meeting_data[key] = ""
            
            return True, meeting_data
            
        except json.JSONDecodeError as e:
            # JSONパースエラーの場合、テキストをそのまま議題・内容として使用
            return True, {
                "議題・内容": text[:1000] if len(text) > 1000 else text,
                "決定事項": "",
                "共有事項": "",
                "その他メモ": ""
            }
        except Exception as e:
            return False, f"議事録生成エラー: {str(e)}"

