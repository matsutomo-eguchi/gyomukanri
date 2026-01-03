"""
事故報告書PDF生成モジュール
ReportLabを使用して事故報告書のPDFを生成します
HTMLテンプレートに忠実なレイアウトを実現します
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
try:
    from reportlab.lib.units import mm, pt
except (ImportError, AttributeError):
    # ReportLabのバージョンによっては直接インポートできない場合があるため、
    # モジュールをインポートして使用する
    try:
        import reportlab.lib.units as units
        mm = getattr(units, 'mm', 2.834645669291339)  # 1mm = 2.834645669291339 points
        pt = getattr(units, 'pt', 1.0)  # 1pt = 1.0 point
    except (ImportError, AttributeError):
        # フォールバック: 標準的な値を直接定義
        mm = 2.834645669291339  # 1mm = 2.834645669291339 points
        pt = 1.0  # 1pt = 1.0 point
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import math


class AccidentReportGenerator:
    """事故報告書PDF生成クラス"""
    
    def __init__(self, filename="事故報告書.pdf"):
        """
        初期化
        
        Args:
            filename: 生成するPDFファイル名
        """
        self.filename = filename
        self.width, self.height = A4
        self.margin = 15 * mm  # HTMLの@page marginに合わせる
        
        # 日本語フォントの登録
        # macOSの標準日本語フォントを使用
        font_registered = False
        
        # 明朝体の登録（優先順位順）
        mincho_fonts = [
            ("NotoSansJP", "/Library/Fonts/NotoSansJP-VariableFont_wght.ttf"),  # Noto Sans JP（可変フォント）
            ("HiraginoMincho", "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"),  # ヒラギノ明朝
        ]
        
        # ゴシック体の登録（優先順位順）
        gothic_fonts = [
            ("NotoGothic", "/Library/Fonts/NotoSansJP-VariableFont_wght.ttf"),  # Noto Sans JP（可変フォント）
            ("HiraginoGothic", "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc"),  # ヒラギノ角ゴ W5
            ("HiraginoGothicW3", "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"),  # ヒラギノ角ゴ W3
        ]
        
        # 明朝体の登録
        for font_name, font_path in mincho_fonts:
            if os.path.exists(font_path):
                try:
                    # TTCファイルの場合はsubfontIndexを指定
                    if font_path.endswith('.ttc'):
                        pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
                    else:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.font_reg = font_name
                    font_registered = True
                    break
                except Exception as e:
                    continue
        
        # ゴシック体の登録
        for font_name, font_path in gothic_fonts:
            if os.path.exists(font_path):
                try:
                    # TTCファイルの場合はsubfontIndexを指定
                    if font_path.endswith('.ttc'):
                        pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
                    else:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.font_bold = font_name
                    break
                except Exception as e:
                    continue
        
        # フォント登録に失敗した場合のフォールバック
        if not font_registered:
            try:
                # UnicodeCIDFontを試す（Adobe Acrobatフォントがある場合）
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3-Acro"))
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5-Acro"))
                self.font_reg = "HeiseiMin-W3-Acro"
                self.font_bold = "HeiseiKakuGo-W5-Acro"
            except Exception:
                # 最終的なフォールバック
                self.font_reg = "Helvetica"
                self.font_bold = "Helvetica-Bold"
        
        # スタイルシートの準備
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
        # 原因チェックリスト
        self.cause_items = {
            1: "よく見え(聞こえ)なかった",
            2: "気が付かなかった",
            3: "忘れていた",
            4: "知らなかった",
            5: "深く考えなかった",
            6: "大丈夫だと思った",
            7: "あわてていた",
            8: "不愉快なことがあった",
            9: "疲れていた",
            10: "無意識に手が動いた",
            11: "やりにくかった",
            12: "体のバランスを崩した"
        }
        
        # 分類
        self.categories = [
            "環境に問題があった",
            "設備・機器等に問題があった",
            "指導方法に問題があった",
            "自分自身に問題があった"
        ]
    
    def setup_custom_styles(self):
        """カスタムスタイルの設定"""
        # 本文用スタイル（11pt、明朝体）
        self.para_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontName=self.font_reg,
            fontSize=11,
            leading=15.4,  # line-height: 1.4
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            wordWrap='CJK',  # 日本語の自動折り返しを有効化
        )
        
        # タイトル用スタイル
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Normal'],
            fontName=self.font_bold,
            fontSize=16.5,  # 1.5em = 11pt * 1.5
            leading=23.1,
            alignment=TA_CENTER,
            wordWrap='CJK',  # 日本語の自動折り返しを有効化
        )
        
        # ラベル用スタイル（0.9em = 9.9pt）
        self.label_style = ParagraphStyle(
            'CustomLabel',
            parent=self.styles['Normal'],
            fontName=self.font_bold,
            fontSize=9.9,
            leading=13.86,
            alignment=TA_LEFT,
            wordWrap='CJK',  # 日本語の自動折り返しを有効化
        )
        
        # 本文テーブルのラベル用スタイル（横書き、太字、中央揃え）
        self.body_label_style = ParagraphStyle(
            'BodyLabel',
            parent=self.styles['Normal'],
            fontName=self.font_bold,
            fontSize=11,
            leading=15.4,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=0,
            wordWrap='CJK',  # 日本語の自動折り返しを有効化（はみ出し防止）
        )
    
    def draw_vertical_text(self, canvas_obj, text, x, y, width, height, font_name, font_size):
        """
        縦書きテキストを描画
        
        Args:
            canvas_obj: Canvasオブジェクト
            text: 描画するテキスト
            x, y: テキストの基準位置（左下、セルの左下）
            width, height: セルの幅と高さ
            font_name: フォント名
            font_size: フォントサイズ
        """
        canvas_obj.saveState()
        
        # セルの中央に配置（パディングを考慮）
        padding = 5  # セルのパディング
        center_x = x + width / 2
        center_y = y + height / 2
        
        # 文字間隔を計算（letter-spacing: 5px、HTMLテンプレートに合わせる）
        char_spacing = 5 * 0.264583 * mm  # 5pxをmmに変換
        
        # テキストの総高さを計算
        total_height = len(text) * (font_size + char_spacing) - char_spacing
        
        # 開始位置を計算（中央から上に）
        start_y = center_y + total_height / 2 - font_size
        
        # 各文字を縦に配置
        for i, char in enumerate(text):
            char_y = start_y - i * (font_size + char_spacing)
            # 文字を回転させて描画
            canvas_obj.saveState()
            canvas_obj.translate(center_x, char_y)
            canvas_obj.rotate(90)
            canvas_obj.setFont(font_name, font_size)
            # 文字の中央揃えのため、文字幅の半分だけ左にずらす
            char_width = canvas_obj.stringWidth(char, font_name, font_size)
            canvas_obj.drawString(-char_width / 2, 0, char)
            canvas_obj.restoreState()
        
        canvas_obj.restoreState()
    
    def px_to_mm(self, px_value):
        """
        px値をmm値に変換
        
        Args:
            px_value: px値
            
        Returns:
            mm値（ReportLabの単位）
        """
        return px_value * 0.264583 * mm
    
    def draw_underline(self, canvas_obj, x, y, width, line_width=0.5):
        """
        下線を描画（入力欄用）
        
        Args:
            canvas_obj: Canvasオブジェクト
            x, y: 線の開始位置
            width: 線の幅
            line_width: 線の太さ
        """
        canvas_obj.setLineWidth(line_width)
        canvas_obj.line(x, y, x + width, y)
    
    def generate(self, data):
        """
        AIが生成したデータを受け取りPDFを作成する
        
        Args:
            data: 事故報告の内容を含む辞書
                - facility_name: 事業所名
                - report_content: 報告内容（新規追加）
                - date_year, date_month, date_day: 発生日（年、月、日）
                - date_weekday: 曜日
                - time_hour, time_min: 発生時刻（時、分）
                - location: 発生場所
                - subject_name: 対象者名
                - situation: 事故発生の状況と経過（統合）
                - process: 経過（situationに統合される可能性あり）
                - cause: 事故原因
                - cause_indices: 原因チェックリストの選択項目（1-12のリスト）
                - category_index: 分類のインデックス（0-3）
                - category: 分類のテキスト
                - countermeasure: 対策
                - others: その他
                - reporter_name: 報告者氏名
                - record_date_year, record_date_month, record_date_day: 記録日（年、月、日）
        """
        c = canvas.Canvas(self.filename, pagesize=A4)
        c.setTitle("事故状況・対策報告書")
        
        # ページマージンの設定
        content_width = self.width - 2 * self.margin
        content_height = self.height - 2 * self.margin
        start_x = self.margin
        start_y = self.height - self.margin
        
        # 現在のY位置を追跡
        current_y = start_y
        
        # ===== ヘッダー部分 =====
        # タイトル（左側）と事業所名・管理者（右側テーブル）を横並び
        px_to_mm = 0.264583
        
        # タイトルを描画（左側、下揃え）
        c.setFont(self.font_bold, 20)  # 20pt
        title_text = "事故状況・対策報告書"
        title_y = current_y - 10 * mm  # 下から10mm（少し上に上げる）
        c.drawString(start_x + 6 * mm, title_y, title_text)
        
        # 右側のテーブル（事業所名と管理者）
        right_table_width = 90 * mm  # 350px相当
        right_table_x = start_x + content_width - right_table_width
        
        # 事業所名と管理者のテーブル
        header_right_data = [
            [
                Paragraph(
                    f'<para leading="13.86"><b>事業所名</b><br/>{data.get("facility_name", "")}</para>',
                    self.para_style
                ),
                ""  # 管理者セルは後で手動描画
            ]
        ]
        
        header_right_col_widths = [
            right_table_width * 0.65,  # 事業所名 65%（バランス調整）
            right_table_width * 0.35,  # 管理者 35%（少し広げる）
        ]
        
        header_right_table = Table(
            header_right_data,
            colWidths=header_right_col_widths,
            rowHeights=[50 * px_to_mm * mm]  # 50px高さ
        )
        
        header_right_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),  # 内側は1px
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # 外枠を太く（上と右）
            ('LINEABOVE', (0, 0), (-1, 0), 2.0, colors.black),
            ('LINEAFTER', (-1, 0), (-1, 0), 2.0, colors.black),
        ])
        
        header_right_table.setStyle(header_right_style)
        header_right_w, header_right_h = header_right_table.wrapOn(c, right_table_width, content_height)
        header_right_y = current_y - header_right_h
        header_right_table.drawOn(c, right_table_x, header_right_y)
        
        # 管理者セルに「管理者」と「㊞」を手動描画
        manager_cell_x = right_table_x + header_right_col_widths[0] + 1.0
        manager_cell_y = header_right_y
        manager_cell_width = header_right_col_widths[1] - 1.0 * 2
        manager_cell_height = header_right_h - 1.0 * 2
        
        # 左上に「管理者」を描画
        c.setFont(self.font_bold, 9)  # 9pt
        manager_label_x = manager_cell_x + 6
        manager_label_y = header_right_y + manager_cell_height - 6
        c.drawString(manager_label_x, manager_label_y, "管理者")
        
        # 右下に「㊞」を描画（フォントサイズを小さく）
        c.setFont(self.font_reg, 12)  # 12pt（小さく調整）
        stamp_text = "㊞"
        stamp_width = c.stringWidth(stamp_text, self.font_reg, 12)
        stamp_x = manager_cell_x + manager_cell_width - stamp_width - 5
        stamp_y = manager_cell_y + 5
        c.drawString(stamp_x, stamp_y, stamp_text)
        
        # タイトル下の太い線（2px）を描画
        line_y = current_y - header_right_h - 2 * mm
        c.setLineWidth(2.0)
        c.line(start_x, line_y, start_x + content_width, line_y)
        
        # マージンを調整（A4に収まるように）
        current_y = line_y - 1 * mm
        
        # ===== 情報テーブル（第1行） =====
        # 報告内容、報告者氏名、記録日
        record_date_year = data.get("record_date_year", "")
        record_date_month = data.get("record_date_month", "")
        record_date_day = data.get("record_date_day", "")
        
        # 記録日が文字列の場合、パースを試みる
        if not record_date_year and data.get("record_date"):
            try:
                # "2024年01月15日"形式から抽出
                date_str = data.get("record_date", "")
                if "年" in date_str:
                    parts = date_str.replace("年", " ").replace("月", " ").replace("日", "").split()
                    if len(parts) >= 3:
                        record_date_year = parts[0]
                        record_date_month = parts[1]
                        record_date_day = parts[2]
            except:
                pass
        
        # 報告内容が指定されていない場合は空文字列
        report_content = data.get("report_content", "")
        if not report_content:
            # situationから簡潔に抽出するか、空のまま
            report_content = ""
        
        info_row1_data = [
            [
                Paragraph(
                    f'<para leading="13.86"><b>報告内容</b><br/>{report_content}</para>',
                    self.para_style
                ),
                Paragraph(
                    f'<para leading="13.86"><b>報告者氏名</b><br/>{data.get("reporter_name", "")}</para>',
                    self.para_style
                ),
                Paragraph(
                    f'<para leading="13.86" align="right"><b>記録日</b><br/>{record_date_year} 年 {record_date_month} 月 {record_date_day} 日</para>',
                    self.para_style
                )
            ]
        ]
        
        info_row1_col_widths = [
            content_width * 0.35,  # 報告内容 35%
            content_width * 0.30,  # 報告者氏名 30%
            content_width * 0.35,  # 記録日 35%
        ]
        
        info_row1_table = Table(
            info_row1_data,
            colWidths=info_row1_col_widths,
            rowHeights=[None]  # 自動調整
        )
        
        info_row1_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),  # 内側は1px
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (1, 0), 'LEFT'),  # 報告内容、報告者氏名は左
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),  # 記録日は右
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # 外枠を太く（左と右）
            ('LINEBEFORE', (0, 0), (0, 0), 2.0, colors.black),
            ('LINEAFTER', (-1, 0), (-1, 0), 2.0, colors.black),
        ])
        
        info_row1_table.setStyle(info_row1_style)
        info_row1_w, info_row1_h = info_row1_table.wrapOn(c, content_width, content_height)
        info_row1_table.drawOn(c, start_x, current_y - info_row1_h)
        # マージンを調整（A4に収まるように）
        current_y -= info_row1_h + 2 * mm
        
        # ===== 情報テーブル（第2行） =====
        # 事故発生日時、発生場所、対象者
        date_year = data.get("date_year", "")
        date_month = data.get("date_month", "")
        date_day = data.get("date_day", "")
        time_hour = data.get("time_hour", "")
        time_min = data.get("time_min", "")
        date_weekday = data.get("date_weekday", "")
        
        # 分を2桁表示に変換
        try:
            time_min_formatted = str(int(time_min)).zfill(2) if time_min else ""
        except (ValueError, TypeError):
            time_min_formatted = str(time_min).zfill(2) if time_min else ""
        
        datetime_text = f'<para leading="13.86"><b>事故発生日時</b><br/>{date_year} 年 {date_month} 月 {date_day} 日<br/>{time_hour} 時 {time_min_formatted} 分頃<br/>（ {date_weekday} ）曜日</para>'
        
        # 対象者名を処理（複数の場合は「、」で区切る）
        subject_name = str(data.get("subject_name", ""))
        if isinstance(subject_name, list):
            # リストの場合は「、」で結合
            subject_name = "、".join(subject_name) if subject_name else ""
        elif isinstance(subject_name, str):
            # 文字列の場合、改行やカンマが含まれている場合は「、」に統一
            # 改行を「、」に置換
            subject_name = subject_name.replace("\n", "、")
            # カンマも「、」に置換（英語のカンマを日本語の読点に統一）
            subject_name = subject_name.replace(",", "、")
            # 連続する「、」を1つに統一
            while "、、" in subject_name:
                subject_name = subject_name.replace("、、", "、")
            # 前後の空白と「、」を削除
            subject_name = subject_name.strip("、").strip()
        # 対象者名が長い場合や複数の場合に備えて、フォントサイズを少し小さく
        subject_text = f'<para leading="12"><b>対象者</b><br/><font size="10">{subject_name}</font></para>'
        
        info_row2_data = [
            [
                Paragraph(datetime_text, self.para_style),
                Paragraph(
                    f'<para leading="13.86"><b>発生場所</b><br/>{data.get("location", "")}</para>',
                    self.para_style
                ),
                Paragraph(
                    subject_text,
                    self.para_style
                )
            ]
        ]
        
        info_row2_col_widths = [
            content_width * 0.40,  # 事故発生日時
            content_width * 0.30,  # 発生場所
            content_width * 0.30,  # 対象者
        ]
        
        info_row2_table = Table(
            info_row2_data,
            colWidths=info_row2_col_widths,
            rowHeights=[None]
        )
        
        info_row2_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),  # 内側は1px
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # 外枠を太く（左、右、下）
            ('LINEBEFORE', (0, 0), (0, 0), 2.0, colors.black),
            ('LINEAFTER', (-1, 0), (-1, 0), 2.0, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2.0, colors.black),
        ])
        
        info_row2_table.setStyle(info_row2_style)
        info_row2_w, info_row2_h = info_row2_table.wrapOn(c, content_width, content_height)
        info_row2_table.drawOn(c, start_x, current_y - info_row2_h)
        # マージンを調整（A4に収まるように）
        current_y -= info_row2_h + 2 * mm
        
        # ===== 本文テーブル =====
        # 横書きカテゴリと横書き内容
        # situationとprocessを統合
        situation_text = data.get("situation", "")
        process_text = data.get("process", "")
        if process_text and process_text != situation_text:
            situation_full = f"{situation_text}\n\n【経過】\n{process_text}"
        else:
            situation_full = situation_text
        
        # 横書きカテゴリのテキスト
        horizontal_labels = [
            "事故発生状況と経過",
            "事故原因",
            "対　策",
            "その他"
        ]
        
        # 本文テーブルの列幅（ラベルカラム: 適切な幅、内容カラム: 残り）
        # A4に収まるように調整
        label_col_width = 35 * mm  # 横書きラベル用の幅
        body_col_width = content_width - label_col_width - 1.0 * 2  # 内容（境界線分を引く）
        
        # 事故原因セクションの準備（原因チェックリストと分類を含む）
        cause_text = data.get("cause", "")
        selected_cause_indices = data.get("cause_indices", [])
        category_index = data.get("category_index", -1)
        category_text = data.get("category", "")
        
        # 原因テキストと分類を組み合わせ
        cause_content_parts = []
        if cause_text:
            cause_content_parts.append(cause_text)
        if category_text and category_index >= 0:
            cause_content_parts.append(f"\n\n【分類】\n{category_text}")
        cause_content = "\n".join(cause_content_parts) if cause_content_parts else ""
        
        # 原因セクション用のテーブル（左列: 原因テキスト、右列: チェックリスト用の空セル）
        cause_text_width = body_col_width * 0.60  # 左60%
        cause_checklist_width = body_col_width * 0.40  # 右40%
        
        # 原因セクションの内部テーブル（左: 原因テキスト、右: 空セル（後で手動描画））
        cause_inner_table_data = [
            [Paragraph(cause_content, self.para_style), ""]  # 右列は空、後で手動描画
        ]
        cause_inner_table = Table(
            cause_inner_table_data,
            colWidths=[cause_text_width, cause_checklist_width],
            rowHeights=[None]
        )
        cause_inner_table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ])
        cause_inner_table.setStyle(cause_inner_table_style)
        
        body_table_data = [
            [
                Paragraph(horizontal_labels[0], self.body_label_style),
                Paragraph(situation_full, self.para_style)
            ],
            [
                Paragraph(horizontal_labels[1], self.body_label_style),
                cause_inner_table
            ],
            [
                Paragraph(horizontal_labels[2], self.body_label_style),
                Paragraph(data.get("countermeasure", ""), self.para_style)
            ],
            [
                Paragraph(horizontal_labels[3], self.body_label_style),
                Paragraph(data.get("others", ""), self.para_style)
            ]
        ]
        
        body_col_widths = [
            label_col_width,  # 横書きカテゴリ
            body_col_width,  # 内容
        ]
        
        # 行の高さをA4に収まるように調整（HTMLの比率を維持しつつ縮小）
        # 利用可能な高さを計算: A4高さ297mm - マージン30mm - ヘッダー約30mm - 情報テーブル約40mm - フッター約50mm = 約147mm
        # HTMLの比率: 250:150:150:100 = 5:3:3:2
        # 合計13単位で約120mmに調整
        available_height = 120 * mm
        unit_height = available_height / 13
        body_row_heights = [
            unit_height * 5,  # 事故発生状況と経過
            unit_height * 3,  # 事故原因
            unit_height * 3,  # 対策
            unit_height * 2,  # その他
        ]
        
        body_table = Table(
            body_table_data,
            colWidths=body_col_widths,
            rowHeights=body_row_heights
        )
        
        body_table_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.0, colors.black),  # 内側は1px
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # ラベルカラム中央
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # 内容左
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (1, 0), (1, -1), 6),
            ('RIGHTPADDING', (1, 0), (1, -1), 6),
            ('TOPPADDING', (1, 0), (1, -1), 6),
            ('BOTTOMPADDING', (1, 0), (1, -1), 6),
            # 外枠を太く（左、右、下）
            ('LINEBEFORE', (0, 0), (0, -1), 2.0, colors.black),
            ('LINEAFTER', (-1, 0), (-1, -1), 2.0, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 2.0, colors.black),
        ])
        
        body_table.setStyle(body_table_style)
        body_w, body_h = body_table.wrapOn(c, content_width, content_height)
        body_table_y = current_y - body_h
        body_table.drawOn(c, start_x, body_table_y)
        
        # 原因セクションの右側にチェックリストを手動描画
        if selected_cause_indices:
            # 原因セクションの行の位置を計算（2行目）
            cause_row_y_top = body_table_y + body_h - body_row_heights[0] - body_row_heights[1]
            cause_row_y_bottom = body_table_y + body_h - body_row_heights[0]
            
            # チェックリストの描画位置を計算
            checklist_cell_x = start_x + label_col_width + cause_text_width + 6  # パディング6pt
            checklist_cell_y = cause_row_y_bottom - 6  # パディング6pt
            
            # フォントサイズと行間
            font_size_pt = 11
            line_spacing = 2 * mm
            circle_radius = 2 * mm
            
            # フォントの高さ
            c.setFont(self.font_reg, font_size_pt)
            font_height = font_size_pt * 1.4
            
            # 「該当する事項に○をつける」の説明文を描画
            instruction_text = "該当する事項に○をつける"
            c.setFont(self.font_reg, 10)
            instruction_y = checklist_cell_y - 3 * mm
            c.drawString(checklist_cell_x, instruction_y, instruction_text)
            
            # チェックリストの配置範囲を計算
            # 説明文の下からセルの最下部まで
            checklist_top = instruction_y - font_height - line_spacing - 3 * mm  # 説明文の下に少し余裕
            checklist_bottom = cause_row_y_bottom + 6  # パディング考慮（下から6pt）
            
            # 12項目を均等に配置するための計算
            num_items = 12
            # 上下のパディング（少し余裕を持たせる）
            vertical_padding = 3 * mm
            
            # 選択肢1のY位置（最上部から少し下げる）
            first_item_y = checklist_top - vertical_padding
            # 選択肢12のY位置（最下部から少し上げる）
            last_item_y = checklist_bottom + vertical_padding
            
            # 選択肢1と12の間の距離
            total_spacing = first_item_y - last_item_y
            # 11個の間隔で均等に分割（選択肢1と12の間には11個の間隔がある）
            item_spacing = total_spacing / 11
            
            # 各チェックリスト項目を描画
            c.setFont(self.font_reg, font_size_pt)
            for i in range(1, 13):
                # 各項目のY位置を計算（選択肢1を最上部、選択肢12を最下部に均等配置）
                item_y = first_item_y - (i - 1) * item_spacing
                
                # 番号を描画（右寄せ、幅25px）
                num_text = str(i)
                num_width = c.stringWidth(num_text, self.font_reg, font_size_pt)
                num_x = checklist_cell_x + self.px_to_mm(25) - num_width
                c.drawString(num_x, item_y, num_text)
                
                # 円を描画（番号の後、margin-right: 5px）
                circle_x = checklist_cell_x + self.px_to_mm(25) + self.px_to_mm(5) + circle_radius
                circle_y = item_y + font_height * 0.5
                
                if i in selected_cause_indices:
                    # 選択されている場合は塗りつぶし
                    c.setFillColor(colors.black)
                    c.circle(circle_x, circle_y, circle_radius, fill=1)
                else:
                    # 選択されていない場合は輪郭のみ
                    c.setStrokeColor(colors.HexColor('#333333'))
                    c.setLineWidth(1)
                    c.circle(circle_x, circle_y, circle_radius, fill=0)
                
                # テキストを描画（円の後、margin-right: 5px）
                text_x = circle_x + circle_radius + self.px_to_mm(5)
                c.setFillColor(colors.black)
                c.drawString(text_x, item_y, self.cause_items[i])
        
        current_y -= body_h + 3 * mm
        
        # ===== フッター =====
        # 説明文と確認文（A4に収まるようにマージンを調整）
        footer_y = current_y - 8 * mm
        
        # 説明文（10pt）
        c.setFont(self.font_reg, 10)
        c.drawString(start_x, footer_y, "（説明が必要な場合に署名・捺印を頂きます）")
        
        footer_y -= 8 * mm
        
        # 確認文（14pt、左マージン20px = 約5.3mm）
        c.setFont(self.font_reg, 14)
        c.drawString(start_x + 5.3 * mm, footer_y, "上記について、説明を受けました。")
        
        footer_y -= 15 * mm
        
        # 署名欄（HTMLでは右寄せ、margin-right: 20px）
        sign_area_y = footer_y
        c.setFont(self.font_reg, 11)
        right_margin = 5.3 * mm
        sign_area_right = start_x + content_width - right_margin
        
        # 日付欄（右寄せ、空欄で「年　　月　　日」のみ表示）
        space_width = c.stringWidth(" ", self.font_reg, 11)
        nen_width = c.stringWidth("年", self.font_reg, 11)
        gatsu_width = c.stringWidth("月", self.font_reg, 11)
        nichi_width = c.stringWidth("日", self.font_reg, 11)
        
        # 空欄の幅を設定（適切な間隔）
        blank_width = 15 * mm  # 空欄の幅
        
        # 全体の幅を計算（空欄 + 年 + 空欄 + 月 + 空欄 + 日）
        total_date_width = blank_width + nen_width + blank_width + gatsu_width + blank_width + nichi_width
        
        # 右寄せで描画
        date_start_x = sign_area_right - total_date_width
        x_pos = date_start_x
        # 空欄（年）
        x_pos += blank_width
        c.drawString(x_pos, sign_area_y, "年")
        x_pos += nen_width + blank_width
        # 空欄（月）
        c.drawString(x_pos, sign_area_y, "月")
        x_pos += gatsu_width + blank_width
        # 空欄（日）
        c.drawString(x_pos, sign_area_y, "日")
        
        # 改行後の氏名欄（右寄せ、line-height: 2.5相当）
        sign_area_y -= 20 * mm
        
        # 氏名ラベル
        name_label = "氏名"
        name_label_width = c.stringWidth(name_label, self.font_reg, 11)
        # 下線幅200px = 約53mm、印鑑マーク幅、マージンを考慮
        underline_width = 53 * mm
        stamp_width = c.stringWidth("印", self.font_reg, 11)
        total_name_width = name_label_width + 10 * mm + underline_width + 5 * mm + stamp_width
        
        name_label_x = sign_area_right - total_name_width
        c.drawString(name_label_x, sign_area_y, name_label)
        
        # 氏名の下線（200px = 約53mm）
        underline_x = name_label_x + name_label_width + 10 * mm
        c.setLineWidth(0.5)
        c.line(underline_x, sign_area_y - 2, underline_x + underline_width, sign_area_y - 2)
        
        # 印鑑マーク「印」（下線の右側、margin-left: 5px = 約1.3mm）
        stamp_x = underline_x + underline_width + 5 * mm
        c.drawString(stamp_x, sign_area_y, "印")
        
        # 保存
        c.save()
        return self.filename
    
    @staticmethod
    def format_date_for_report(date_obj):
        """
        日付オブジェクトを報告書用の形式に変換
        
        Args:
            date_obj: datetime.dateまたはdatetimeオブジェクト
            
        Returns:
            dict: 年、月、日、曜日の辞書
        """
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                date_obj = datetime.now().date()
        
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        weekday = weekdays[date_obj.weekday()]
        
        return {
            "date_year": str(date_obj.year),
            "date_month": str(date_obj.month),
            "date_day": str(date_obj.day),
            "date_weekday": weekday,
            "record_date_year": str(date_obj.year),
            "record_date_month": str(date_obj.month),
            "record_date_day": str(date_obj.day),
        }
