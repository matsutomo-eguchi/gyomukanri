"""
AI文章生成アシストモジュール
grok-4-1-fast-reasoningを使用した文章生成機能
Gemini 3 Flash Previewを使用した音声認識と議事録生成機能
"""
import os
from typing import Optional, Dict, Tuple, Any
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
            print("[DEBUG] Starting audio transcription")
            success, transcribed_text = self.transcribe_audio_to_text(audio_file_path, context_info)
            print(f"[DEBUG] Transcription result: success={success}, text_length={len(transcribed_text) if transcribed_text else 0}")
            if not success:
                return False, transcribed_text

            # テキストから議事録を構造化
            print("[DEBUG] Starting meeting minutes generation")
            result = self.generate_meeting_minutes_from_text(transcribed_text)
            print(f"[DEBUG] Final result: {result}")
            return result

        except Exception as e:
            print(f"[DEBUG] Exception in generate_meeting_minutes_from_audio: {str(e)}")
            import traceback
            traceback.print_exc()
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
    
    def generate_daily_comment(self, activity_content: str = "", challenges: str = "", improvements: str = "") -> tuple:
        """
        日報コメントを生成（職員が1日を振り返るコメント）
        
        Args:
            activity_content: 活動内容（学習支援、自由遊びの見守り、集団遊びの補助など）
            challenges: 課題
            improvements: 改善点
            
        Returns:
            (成功フラグ, 生成された日報コメント)
        """
        if not self.is_available():
            return False, "APIキーが設定されていません。設定画面でAPIキーを入力してください。"
        
        # プロンプトの構築
        prompt = f"""#命令書:
あなたは世界でトップで有能なプロの放課後等デイサービスの児童指導員です。職員が1日を振り返る日報コメントを作成してください。以下の｢要件｣を踏まえ、｢アウトプット例｣のように、最高の日報コメントを作成してください。

##要件:
･文字数は200字ていど
･文章は簡潔に書く
･語り口調で書く（「〜でした」「〜しました」「〜できました」など、自然な語り口調）
･世界でトップで有能なプロの放課後等デイサービスの職員として、専門性と経験に裏打ちされた文章にする
･【必須】活動内容: {activity_content if activity_content else "学習支援、自由遊びの見守り、集団遊びの補助"}
･課題: {challenges if challenges else "特になし"}
･改善点: {improvements if improvements else "特になし"}

【重要】必ず入力された活動内容を反映させてください。活動内容「{activity_content if activity_content else "なし"}」が入力されている場合は、それを基に日報コメントを作成してください。活動内容を無視したり、変更したりしないでください。

##アウトプット例:

【本日の活動内容】
{activity_content if activity_content else "本日は学習支援、自由遊びの見守り、集団遊びの補助を行いました。"}

【本日の課題】
{challenges if challenges else "特に大きな課題はなかったが、より良い支援ができるよう努めたい。"}

【今後の改善点】
{improvements if improvements else "より効果的な支援方法を検討していきたい。"}

上記の形式で、入力された情報を基に、語り口調で、世界でトップで有能なプロの放課後等デイサービスの職員としてふさわしい、最高の日報コメントを作成してください。

【最重要】活動内容「{activity_content}」を必ず反映させてください。この活動内容を基に日報コメントを作成してください。活動内容を無視したり、変更したり、追加したりしないでください。入力された活動内容を忠実に反映させてください。

遠慮せずに全力を尽くしてください。秀逸にultrahardに取り組んでください。最高を超えるアウトプットを実現してください。"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # システムメッセージをactivity_contentの有無で調整
            system_content = "あなたは世界でトップで有能なプロの放課後等デイサービスの児童指導員です。職員が1日を振り返る日報コメントを、語り口調で、専門性と経験に裏打ちされた文章として作成するのが得意です。"
            if activity_content:
                system_content += f" 必ず以下の活動内容を反映させてください：{activity_content}"
            system_content += " 遠慮せずに、全力を尽くしてください。秀逸にultrahardに取り組んでください。最高を超えるアウトプットを実現してください。"

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_content
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
                generated_text = result["choices"][0]["message"]["content"].strip()
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
            print("[DEBUG] Starting audio transcription")
            success, transcribed_text = self.transcribe_audio_to_text(audio_file_path, context_info)
            print(f"[DEBUG] Transcription result: success={success}, text_length={len(transcribed_text) if transcribed_text else 0}")
            if not success:
                return False, transcribed_text

            # テキストから議事録を構造化
            print("[DEBUG] Starting meeting minutes generation")
            result = self.generate_meeting_minutes_from_text(transcribed_text)
            print(f"[DEBUG] Final result: {result}")
            return result

        except Exception as e:
            print(f"[DEBUG] Exception in generate_meeting_minutes_from_audio: {str(e)}")
            import traceback
            traceback.print_exc()
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
            # 複数段階分析プロセス
            # ステップ1: テキストのクリーニングと前処理
            cleaned_text = self._preprocess_meeting_text(text)

            # ステップ2: テキストの分析と構造化
            analysis_result = self._analyze_meeting_content(cleaned_text)

            # ステップ3: 分類結果の検証と改善
            validated_result = self._validate_and_improve_classification(cleaned_text, analysis_result)

            return True, validated_result

        except Exception as e:
            print(f"[DEBUG] Exception in generate_meeting_minutes_from_text: {str(e)}")
            import traceback
            traceback.print_exc()
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
            print("[DEBUG] Starting audio transcription")
            success, transcribed_text = self.transcribe_audio_to_text(audio_file_path, context_info)
            print(f"[DEBUG] Transcription result: success={success}, text_length={len(transcribed_text) if transcribed_text else 0}")
            if not success:
                return False, transcribed_text

            # テキストから議事録を構造化
            print("[DEBUG] Starting meeting minutes generation")
            result = self.generate_meeting_minutes_from_text(transcribed_text)
            print(f"[DEBUG] Final result: {result}")
            return result

        except Exception as e:
            print(f"[DEBUG] Exception in generate_meeting_minutes_from_audio: {str(e)}")
            import traceback
            traceback.print_exc()
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
            # 複数段階分析プロセス
            # ステップ1: テキストのクリーニングと前処理
            cleaned_text = self._preprocess_meeting_text(text)

            # ステップ2: テキストの分析と構造化
            analysis_result = self._analyze_meeting_content(cleaned_text)

            # ステップ3: 分類結果の検証と改善
            validated_result = self._validate_and_improve_classification(cleaned_text, analysis_result)

            return True, validated_result

        except Exception as e:
            print(f"[DEBUG] Exception in generate_meeting_minutes_from_text: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"議事録生成エラー: {str(e)}"

    def _analyze_meeting_content(self, text: str) -> Dict[str, str]:
        """
        会議内容をAIで分析・構造化する
        """
        print(f"[DEBUG] _analyze_meeting_content called with text length: {len(text)}")

        try:
            # API設定の確認
            if not self._ensure_gemini_configured():
                print("[DEBUG] Gemini config failed, using fallback")
                return self._fallback_parse_meeting_text(text, "")

            # Gemini 3 Flash Previewを使用して高度な議事録構造化
            model = genai.GenerativeModel('gemini-3-flash-preview')
            print("[DEBUG] Gemini model created successfully")

            prompt = f"""あなたは保育園の朝礼を分析するアシスタントです。以下のテキストから議事録を作成してください。
            テキスト:            {text}
            以下のJSON形式で出力してください：            {{            "議題・内容": "会議の主要な話題と議論内容",            "決定事項": "決定された具体的な事項",            "共有事項": "スタッフへの連絡事項",            "その他メモ": "会議のタイムライン"            }}
            注意:            - 必ず有効なJSON形式で出力            - 各項目は簡潔にまとめる            - 日本語で記述            - JSON以外は何も出力しない            """
            print(f"[DEBUG] Sending prompt to Gemini, length: {len(prompt)}")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # より決定論的に
                    max_output_tokens=3000  # より長い出力に対応
                )
            )
            print(f"[DEBUG] Received response from Gemini")
            

            # JSONをパース
            # JSONをパース
            import json
            import re
            response_text = response.text.strip()
            print(f"[DEBUG] Response text length: {len(response_text)}")
            print(f"[DEBUG] Response text preview: {response_text[:200]}...")

            # レスポンスが空でないかチェック
            if not response_text:
                print("[DEBUG] Response text is empty")
                return {
                    "議題・内容": text[:1000] if len(text) > 1000 else text,
                    "決定事項": "",
                    "共有事項": "",
                    "その他メモ": ""
                }

            # JSON部分を抽出（コードブロックがあれば除去）
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text

            # JSONパースを試行
            print(f"[DEBUG] Attempting to parse JSON, length: {len(json_str)}")
            try:
                meeting_data = json.loads(json_str)
                print(f"[DEBUG] JSON parse successful, keys: {list(meeting_data.keys())}")
            except json.JSONDecodeError as json_error:
                # JSONパースに失敗した場合、テキストから手動で構造化
                print(f"[DEBUG] JSON parse failed: {json_error}, using fallback")
                meeting_data = self._fallback_parse_meeting_text(text, response_text)
        
            # 必須フィールドの確認
            if "議題・内容" not in meeting_data:
                meeting_data["議題・内容"] = text[:500]  # フォールバック

            # 空のフィールドを空文字列に設定
            for key in ["決定事項", "共有事項", "その他メモ"]:
                if key not in meeting_data:
                    meeting_data[key] = ""

            print(f"[DEBUG] Returning meeting_data with keys: {list(meeting_data.keys())}")
            return meeting_data

        except Exception as e:
            print(f"[DEBUG] Exception in _analyze_meeting_content: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._fallback_parse_meeting_text(text, "")

    def _fallback_parse_meeting_text(self, original_text: str, ai_response: str) -> Dict[str, str]:
        """
        AIレスポンスがJSONでない場合のフォールバック処理
        テキストから手動で構造化する
        """
        try:
            # AIレスポンスから各セクションを抽出しようとする
            content = ai_response.strip()

            # デフォルト値
            meeting_data = {
                "議題・内容": "",
                "決定事項": "",
                "共有事項": "",
                "その他メモ": ""
            }

            # シンプルなパースを試行
            lines = content.split('\n')
            current_section = "議題・内容"

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # セクションの判定
                if "議題・内容" in line or "会議の概要" in line:
                    current_section = "議題・内容"
                    continue
                elif "決定事項" in line or "決定した" in line:
                    current_section = "決定事項"
                    continue
                elif "共有事項" in line or "共有" in line:
                    current_section = "共有事項"
                    continue
                elif "その他メモ" in line or "タイムスタンプ" in line:
                    current_section = "その他メモ"
                    continue

                # 内容の追加
                if line.startswith('-') or line.startswith('・'):
                    if meeting_data[current_section]:
                        meeting_data[current_section] += '\n'
                    meeting_data[current_section] += line
                elif len(line) > 10:  # 意味のある長さの行
                    if meeting_data[current_section]:
                        meeting_data[current_section] += '\n'
                    meeting_data[current_section] += line

            # 議題・内容が空の場合、元のテキストを使用
            if not meeting_data["議題・内容"].strip():
                meeting_data["議題・内容"] = original_text[:1000] if len(original_text) > 1000 else original_text

            return meeting_data

        except Exception as e:
            # 最終フォールバック
            return {
                "議題・内容": original_text[:1000] if len(original_text) > 1000 else original_text,
                "決定事項": "",
                "共有事項": "",
                "その他メモ": ""
            }

    def _preprocess_meeting_text(self, text: str) -> str:
        """
        会議テキストの前処理を行う
        不要な部分の除去、整形など
        """
        # 基本的なクリーニング
        cleaned = text.strip()

        # 長すぎるテキストを適切に分割（トークン制限対策）
        if len(cleaned) > 10000:
            # 重要な部分を優先的に残す
            sentences = cleaned.split('。')
            if len(sentences) > 50:
                # 最初の30文と最後の20文を保持
                cleaned = '。'.join(sentences[:30] + sentences[-20:]) + '。'

        return cleaned

    def _validate_and_improve_classification(self, original_text: str, analysis_result: Dict[str, str]) -> Dict[str, str]:
        """
        分類結果の検証と改善を行う
        """
        try:
            # 結果の品質チェック
            improved_result = analysis_result.copy()

            # 議題・内容の検証
            if not analysis_result.get("議題・内容", "").strip():
                # フォールバックとして元のテキストから主要部分を抽出
                improved_result["議題・内容"] = original_text[:500]

            # 各カテゴリの重複チェックと整理
            all_content = []
            for key in ["議題・内容", "決定事項", "共有事項"]:
                content = analysis_result.get(key, "")
                if content and content not in all_content:
                    all_content.append(content)

            # その他メモの形式チェック
            notes = analysis_result.get("その他メモ", "")
            if notes and not notes.startswith("|タイムスタンプ|話題|備考|"):
                # 形式が正しくない場合は空にする
                improved_result["その他メモ"] = ""

            return improved_result

        except Exception as e:
            # エラーが発生した場合は元の結果を返す
            return analysis_result

    def validate_meeting_minutes_quality(self, meeting_data: Dict[str, str], original_text: str) -> Dict[str, Any]:
        """
        生成された議事録の品質を検証する

        Args:
            meeting_data: 生成された議事録データ
            original_text: 元のテキスト

        Returns:
            品質検証結果の辞書
        """
        quality_score = 0
        max_score = 100
        issues = []
        suggestions = []

        try:
            # 1. 必須フィールドのチェック (20点)
            required_fields = ["議題・内容", "決定事項", "共有事項", "その他メモ"]
            for field in required_fields:
                if field in meeting_data and meeting_data[field] and meeting_data[field].strip():
                    quality_score += 5
                else:
                    issues.append(f"必須フィールド '{field}' が空です")
                    suggestions.append(f"'{field}' フィールドに適切な内容を入力してください")

            # 2. 内容の妥当性チェック (30点)
            content = meeting_data.get("議題・内容", "")
            if content:
                # 文字数が適切かチェック
                if 50 <= len(content) <= 2000:
                    quality_score += 10
                elif len(content) < 50:
                    issues.append("議題・内容が短すぎます")
                    suggestions.append("会議の主要な議論内容をより詳細に記述してください")
                else:
                    issues.append("議題・内容が長すぎます")
                    suggestions.append("内容を簡潔に整理してください")

                # 保育園関連キーワードが含まれているかチェック
                childcare_keywords = ["児童", "子供", "園児", "保護者", "送迎", "学習", "遊び", "体調", "安全", "ヒヤリハット"]
                keyword_count = sum(1 for keyword in childcare_keywords if keyword in content)
                if keyword_count >= 2:
                    quality_score += 10
                elif keyword_count == 0:
                    issues.append("保育園運営に関連する内容が不足しています")
                    suggestions.append("児童の様子、業務連絡、安全管理などの保育園特有の内容を含めてください")

                # MECE原則のチェック（重複がないか）
                if len(content.split("。")) >= 3:  # 最低3つの文がある
                    quality_score += 10

            # 3. 分類の適切性チェック (25点)
            # 決定事項と共有事項が混在していないかチェック
            decisions = meeting_data.get("決定事項", "")
            shared = meeting_data.get("共有事項", "")

            if decisions and shared:
                # 決定事項に「共有」の表現が入っていないかチェック
                if not any(word in decisions.lower() for word in ["共有", "連絡", "お知らせ"]):
                    quality_score += 10
                else:
                    issues.append("決定事項に共有事項が混在している可能性があります")
                    suggestions.append("決定事項と共有事項を明確に分離してください")

                # 共有事項に「決定」の表現が入っていないかチェック
                if not any(word in shared.lower() for word in ["決定", "～する", "担当"]):
                    quality_score += 10
                else:
                    issues.append("共有事項に決定事項が混在している可能性があります")
                    suggestions.append("共有事項と決定事項を明確に分離してください")

            # 4. その他メモの形式チェック (15点)
            notes = meeting_data.get("その他メモ", "")
            if notes:
                if notes.startswith("|タイムスタンプ|話題|備考|"):
                    quality_score += 15
                else:
                    issues.append("その他メモの形式が正しくありません")
                    suggestions.append("タイムスタンプ表形式（|タイムスタンプ|話題|備考|）を使用してください")

            # 5. 全体的一貫性チェック (10点)
            total_content_length = sum(len(meeting_data.get(field, "")) for field in required_fields)
            if total_content_length >= 200:
                quality_score += 10
            else:
                issues.append("全体の記述量が不足しています")
                suggestions.append("各項目をより詳細に記述してください")

            # 品質レベル判定
            if quality_score >= 90:
                quality_level = "優秀"
            elif quality_score >= 75:
                quality_level = "良好"
            elif quality_score >= 60:
                quality_level = "可"
            else:
                quality_level = "要改善"

            return {
                "quality_score": quality_score,
                "max_score": max_score,
                "quality_level": quality_level,
                "issues": issues,
                "suggestions": suggestions,
                "details": {
                    "content_length": len(content),
                    "has_required_fields": all(field in meeting_data and meeting_data[field].strip() for field in required_fields),
                    "keyword_count": keyword_count if 'keyword_count' in locals() else 0,
                    "has_proper_format": notes.startswith("|タイムスタンプ|話題|備考|") if notes else False
                }
            }

        except Exception as e:
            return {
                "quality_score": 0,
                "max_score": max_score,
                "quality_level": "評価エラー",
                "issues": [f"品質評価中にエラーが発生しました: {str(e)}"],
                "suggestions": ["システム管理者にお問い合わせください"],
                "details": {}
            }

