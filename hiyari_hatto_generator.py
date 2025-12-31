"""
ヒヤリハット報告書PDF生成モジュール
ReportLabを使用してヒヤリハット報告書のPDFを生成します
HTMLテンプレートに忠実なレイアウトを実現します
すべての文字は横書きで統一します
"""
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
try:
    from reportlab.lib.units import mm, pt
except (ImportError, AttributeError):
    try:
        import reportlab.lib.units as units
        mm = getattr(units, 'mm', 2.834645669291339)
        pt = getattr(units, 'pt', 1.0)
    except (ImportError, AttributeError):
        mm = 2.834645669291339
        pt = 1.0
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class HiyariHattoGenerator:
    """
    ヒヤリハット報告書PDF生成クラス
    HTMLテンプレートに忠実に実装
    すべての文字は横書きで統一
    """

    def __init__(self, filename="ヒヤリハット報告書.pdf"):
        """
        初期化
        
        Args:
            filename: 生成するPDFファイル名
        """
        self.filename = filename
        self.width, self.height = A4
        self.margin = 10 * mm  # A4縦に収めるため、マージンを最小限に
        
        # 日本語フォントの登録（明朝体を優先）
        font_registered = False
        
        # 明朝体の登録（優先順位順）
        mincho_fonts = [
            ("HiraginoMincho", "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"),
            ("NotoSansJP", "/Library/Fonts/NotoSansJP-VariableFont_wght.ttf"),
        ]
        
        # ゴシック体の登録（太字用）
        gothic_fonts = [
            ("HiraginoGothic", "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc"),
            ("HiraginoGothicW3", "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"),
            ("NotoGothic", "/Library/Fonts/NotoSansJP-VariableFont_wght.ttf"),
        ]
        
        # 明朝体の登録
        for font_name, font_path in mincho_fonts:
            if os.path.exists(font_path):
                try:
                    if font_path.endswith('.ttc'):
                        pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
                    else:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.font_reg = font_name
                    font_registered = True
                    break
                except Exception:
                    continue
        
        # ゴシック体の登録
        for font_name, font_path in gothic_fonts:
            if os.path.exists(font_path):
                try:
                    if font_path.endswith('.ttc'):
                        pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
                    else:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.font_bold = font_name
                    break
                except Exception:
                    continue
        
        # フォント登録に失敗した場合のフォールバック
        if not font_registered:
            try:
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3-Acro"))
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5-Acro"))
                self.font_reg = "HeiseiMin-W3-Acro"
                self.font_bold = "HeiseiKakuGo-W5-Acro"
            except Exception:
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
        # 本文用スタイル（8pt、明朝体、line-height: 1.15、A4縦に収めるため大幅縮小）
        self.para_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontName=self.font_reg,
            fontSize=8,
            leading=9.2,  # line-height: 1.15
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            wordWrap='CJK',  # 日本語の自動折り返し
        )
        
        # セクションタイトル用スタイル（16pt、太字）
        self.section_style = ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Normal'],
            fontName=self.font_bold,
            fontSize=16,
            leading=22.4,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
        )
    
    def px_to_mm(self, px_value):
        """
        px値をmm値に変換（1px ≈ 0.264583mm）
        
        Args:
            px_value: px値
            
        Returns:
            mm値
        """
        return px_value * 0.264583 * mm
    
    def draw_circle(self, canvas_obj, x, y, radius, filled=False):
        """
        円を描画（チェックリスト用）
        
        Args:
            canvas_obj: Canvasオブジェクト
            x, y: 円の中心座標
            radius: 半径
            filled: 塗りつぶすかどうか
        """
        canvas_obj.setLineWidth(1)
        if filled:
            canvas_obj.setFillColor(colors.black)
            canvas_obj.circle(x, y, radius, fill=1)
        else:
            canvas_obj.setStrokeColor(colors.HexColor('#333333'))
            canvas_obj.circle(x, y, radius, fill=0)

    def generate_report(self, data, filename=None, reporter_name=""):
        """
        全工程を実行してPDFファイルを保存
        
        Args:
            data: AIまたはユーザーから入力された辞書データ
                - datetime: 発生日時（文字列またはdatetimeオブジェクト）
                - location: 発生場所
                - context: どうしていた時
                - details: ヒヤリとした時のあらまし
                - cause_indices: 原因IDのリスト（1-12）
                - category_index: 分類のインデックス（0-3）
                - countermeasure: 教訓・対策
            filename: 出力ファイル名（省略時はself.filenameを使用）
            reporter_name: 記入者名
        """
        if filename:
            self.filename = filename
        
        c = canvas.Canvas(self.filename, pagesize=A4)
        c.setTitle("ヒヤリハット報告書")

        # ページマージンの設定
        content_width = self.width - 2 * self.margin
        content_height = self.height - 2 * self.margin
        start_x = self.margin
        start_y = self.height - self.margin
        
        # 現在のY位置を追跡
        current_y = start_y

        # ===== タイトル =====
        # A4縦に収めるため、マージンを最小限に
        title_y = current_y - 6 * mm  # margin-bottom: 6mm
        c.setFont(self.font_bold, 16)  # フォントサイズをさらに縮小
        title_text = "ヒヤリハット報告書"
        title_width = c.stringWidth(title_text, self.font_bold, 16)
        c.drawString((self.width - title_width) / 2, title_y, title_text)
        current_y = title_y - 6 * mm  # margin-bottom: 6mm

        # ===== 記入者欄 =====
        reporter_y = current_y - 1.5 * mm
        c.setFont(self.font_reg, 9)  # フォントサイズをさらに縮小
        reporter_label = "記入者"
        reporter_input = reporter_name if reporter_name else ""
        
        # 右寄せで描画
        label_width = c.stringWidth(reporter_label, self.font_reg, 9)
        input_width = 90 * mm / 25.4  # 入力欄の幅をさらに縮小
        input_x = self.width - self.margin - input_width
        label_x = input_x - label_width - 1 * mm
        
        c.drawString(label_x, reporter_y, reporter_label)
        # 下線を描画
        c.setLineWidth(0.5)
        c.line(input_x, reporter_y - 1, input_x + input_width, reporter_y - 1)
        if reporter_input:
            c.drawString(input_x + 0.5 * mm, reporter_y, reporter_input)
        
        current_y = reporter_y - 1.5 * mm

        # ===== 【概要】セクション =====
        current_y -= 4 * mm  # margin-top: 4mm
        c.setFont(self.font_bold, 11)  # フォントサイズをさらに縮小
        c.drawString(start_x, current_y, "【概要】")
        current_y -= 1.5 * mm  # margin-bottom: 1.5mm

        # 日時の処理
        dt = data.get('datetime')
        if isinstance(dt, str):
            try:
                dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except:
                dt = datetime.datetime.now()
        elif not isinstance(dt, datetime.datetime):
            dt = datetime.datetime.now()
        
        # 西暦から令和へ変換 (2019年5月1日以降)
        reiwa_year = dt.year - 2018
        weekday_map = ["月", "火", "水", "木", "金", "土", "日"]
        weekday = weekday_map[dt.weekday()]
        am_pm = "午前" if dt.hour < 12 else "午後"
        hour = dt.hour % 12 if dt.hour % 12 != 0 else 12
        minute = dt.minute

        # 概要テーブル（すべて横書き）
        # 列幅の計算（HTML: col-label-narrow: 10%, col-where: 60%, col-doing: 30%）
        label_col_width = content_width * 0.10
        where_col_width = content_width * 0.60
        doing_col_width = content_width * 0.30
        
        # 日時テキストの作成（分を2桁表示）
        minute_formatted = f"{minute:02d}"
        date_text = f"令和 {reiwa_year} 年 {dt.month} 月 {dt.day} 日 ( {weekday} 曜日)    {am_pm} {hour} 時 {minute_formatted} 分頃"
        
        # ラベル用スタイル（フォントサイズを大幅縮小）
        label_style = ParagraphStyle('Label', parent=self.styles['Normal'], fontName=self.font_bold, fontSize=8, alignment=TA_CENTER)
        label_style_reg = ParagraphStyle('LabelReg', parent=self.styles['Normal'], fontName=self.font_reg, fontSize=8, alignment=TA_CENTER)
        
        # テーブルデータ（すべて横書き、4列構造）
        summary_data = [
            [Paragraph("い　つ", label_style), 
             Paragraph(date_text, self.para_style), "", ""],  # 行1: 列2-3を結合
            [Paragraph("どこで", label_style_reg), 
             Paragraph(data.get('location', ''), self.para_style),
             Paragraph("どうして<br/>い た 時", label_style),
             Paragraph(data.get('context', ''), self.para_style)],  # 行2
            [Paragraph("ヒヤリとした<br/>時のあらまし", label_style_reg), 
             Paragraph(data.get('details', ''), self.para_style), "", ""]  # 行3: 列2-3を結合
        ]
        
        # 行の高さ（A4縦に収めるため大幅に縮小）
        summary_row_heights = [
            8 * mm,  # 行1（日時行）
            14 * mm,  # 行2（どこで/どうしていた時）
            16 * mm,  # 行3（あらまし）
        ]
        
        summary_table = Table(
            summary_data,
            colWidths=[label_col_width, where_col_width, label_col_width, doing_col_width],
            rowHeights=summary_row_heights
        )
        
        summary_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # 線の太さを縮小
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # ラベル列中央
            ('ALIGN', (2, 1), (2, 1), 'CENTER'),  # 行2の「どうしていた時」ラベル中央
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),   # 内容列左
            ('ALIGN', (3, 1), (3, 1), 'LEFT'),    # 行2の内容列左
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('SPAN', (1, 0), (3, 0)),  # 行1の列2-3を結合
            ('SPAN', (1, 2), (3, 2)),  # 行3の列2-3を結合
        ])
        
        summary_table.setStyle(summary_style)
        summary_w, summary_h = summary_table.wrapOn(c, content_width, content_height)
        summary_table_y = current_y - summary_h
        summary_table.drawOn(c, start_x, summary_table_y)
        
        current_y = summary_table_y - 4 * mm  # margin-bottom: 4mm

        # ===== 【原因】セクション =====
        current_y -= 4 * mm  # margin-top: 4mm
        c.setFont(self.font_bold, 11)  # フォントサイズをさらに縮小
        c.drawString(start_x, current_y, "【原因】")
        current_y -= 1.5 * mm  # margin-bottom: 1.5mm

        # 原因テーブル
        category_index = data.get('category_index', -1)
        
        # 各カテゴリのテキストを取得
        category_texts = {
            0: data.get('cause_environment', ''),
            1: data.get('cause_equipment', ''),
            2: data.get('cause_guidance', ''),
            3: data.get('cause_self', '')
        }
        
        # テーブルデータ: ヘッダー行 + データ行（フォントサイズを大幅縮小）
        cause_header_row = [
            Paragraph(self.categories[0], ParagraphStyle('CauseHeader', parent=self.styles['Normal'], fontName=self.font_reg, fontSize=8, alignment=TA_LEFT)),
            Paragraph(self.categories[1], ParagraphStyle('CauseHeader', parent=self.styles['Normal'], fontName=self.font_reg, fontSize=8, alignment=TA_LEFT)),
            Paragraph(self.categories[2], ParagraphStyle('CauseHeader', parent=self.styles['Normal'], fontName=self.font_reg, fontSize=8, alignment=TA_LEFT)),
            Paragraph(self.categories[3], ParagraphStyle('CauseHeader', parent=self.styles['Normal'], fontName=self.font_reg, fontSize=8, alignment=TA_LEFT))
        ]
        cause_data_row = [
            Paragraph(category_texts[0], self.para_style),
            Paragraph(category_texts[1], self.para_style),
            Paragraph(category_texts[2], self.para_style),
            Paragraph(category_texts[3], self.para_style)
        ]
        
        cause_table_data = [cause_header_row, cause_data_row]
        
        cause_col_width = content_width / 4
        cause_table = Table(
            cause_table_data,
            colWidths=[cause_col_width] * 4,
            rowHeights=[None, 12 * mm]  # ヘッダー行は自動、データ行の高さをさらに縮小
        )
        
        cause_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # 線の太さを縮小
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),  # ヘッダー行左
            ('ALIGN', (0, 1), (-1, 1), 'LEFT'),    # データ行左
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f9f9f9')),  # ヘッダー背景色
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ])
        
        cause_table.setStyle(cause_style)
        cause_w, cause_h = cause_table.wrapOn(c, content_width, content_height)
        cause_table_y = current_y - cause_h
        cause_table.drawOn(c, start_x, cause_table_y)
        current_y = cause_table_y - 1.5 * mm  # margin-bottom: 1.5mm

        # ===== 矢印 =====
        current_y -= 2 * mm  # margin-top調整
        arrow_x = start_x + content_width - (content_width * 0.12)  # padding-right: 12%
        c.setFont(self.font_reg, 16)  # フォントサイズをさらに縮小
        c.drawString(arrow_x, current_y, "⇩")
        current_y -= 1.5 * mm  # margin-bottom: 1.5mm

        # ===== 【教訓・対策】セクション =====
        current_y -= 4 * mm  # margin-top: 4mm
        
        # セクションタイトルと説明文を横並びに
        c.setFont(self.font_bold, 11)  # フォントサイズをさらに縮小
        c.drawString(start_x, current_y, "【教訓・対策】")
        
        # 説明文（右寄せ）
        instruction_text = "該当する事項に○をつける"
        c.setFont(self.font_reg, 9)  # フォントサイズをさらに縮小
        instruction_width = c.stringWidth(instruction_text, self.font_reg, 9)
        c.drawString(start_x + content_width - instruction_width, current_y, instruction_text)
        
        current_y -= 1.5 * mm  # margin-bottom: 1.5mm

        # 教訓・対策テーブル
        countermeasure = data.get('countermeasure', '')
        selected_indices = data.get('cause_indices', [])
        
        # テーブルデータ: 左列（教訓・対策）+ 右列（空、後で手動描画）
        countermeasure_col_width = content_width * 0.60
        checklist_col_width = content_width * 0.40
        
        countermeasure_table_data = [
            [Paragraph(countermeasure, self.para_style), ""]  # 右列は空、後で手動描画
        ]
        
        # A4縦に収めるため、残りの高さを正確に計算
        # 現在のY位置から下マージンまでの高さを計算
        remaining_height = current_y - self.margin
        
        # チェックリストに必要な高さを計算（12項目）
        # 最小サイズで計算して確実に収める
        font_size_pt = 7  # フォントサイズをさらに縮小
        line_spacing = 0.5 * mm  # 行間をさらに縮小
        font_height = font_size_pt * 0.352778 * 1.05  # pt to mm変換 * line-height (1.05に縮小)
        checklist_required_height = 12 * (font_height + line_spacing) - line_spacing + 1.5 * mm  # 上下パディングを縮小
        
        # テーブルの高さは、残りの高さとチェックリストに必要な高さの大きい方を使用
        # ただし、A4縦の高さ（297mm）を超えないようにする
        min_table_height = max(checklist_required_height, 20 * mm)  # 最小高さをさらに縮小
        table_height = min(min_table_height, remaining_height - 0.5 * mm)  # 0.5mmの余裕を残す
        
        # もしテーブル高さがチェックリストに必要な高さより小さい場合は、さらに縮小
        if table_height < checklist_required_height:
            # さらに縮小した設定で再計算
            font_size_pt = 6
            line_spacing = 0.4 * mm
            font_height = font_size_pt * 0.352778 * 1.0
            checklist_required_height = 12 * (font_height + line_spacing) - line_spacing + 1.5 * mm
            min_table_height = max(checklist_required_height, 18 * mm)
            table_height = min(min_table_height, remaining_height - 0.5 * mm)
        
        countermeasure_table = Table(
            countermeasure_table_data,
            colWidths=[countermeasure_col_width, checklist_col_width],
            rowHeights=[table_height]
        )
        
        countermeasure_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # 線の太さを縮小
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),  # paddingをさらに縮小
            ('RIGHTPADDING', (0, 0), (-1, -1), 2 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
        ])
        
        countermeasure_table.setStyle(countermeasure_style)
        countermeasure_w, countermeasure_h = countermeasure_table.wrapOn(c, content_width, content_height)
        countermeasure_table_y = current_y - countermeasure_h
        countermeasure_table.drawOn(c, start_x, countermeasure_table_y)
        
        # チェックリストを手動で描画
        checklist_cell_x = start_x + countermeasure_col_width + 2 * mm  # padding考慮
        checklist_cell_y = countermeasure_table_y + countermeasure_h - 2 * mm  # padding考慮（上から）
        
        # 円のサイズをさらに縮小
        circle_radius = 1.0 * mm
        
        # チェックリストのフォントサイズは上で計算した値を使用
        c.setFont(self.font_reg, font_size_pt)
        
        for i in range(1, 13):
            # 各項目のY位置を計算（上から下へ）
            item_y = checklist_cell_y - (i - 1) * (font_height + line_spacing)
            
            # 番号を描画（右寄せ、幅をさらに縮小）
            num_text = str(i)
            num_width = c.stringWidth(num_text, self.font_reg, font_size_pt)
            num_x = checklist_cell_x + 4 * mm - num_width
            c.drawString(num_x, item_y, num_text)
            
            # 円を描画（番号の後）
            circle_x = checklist_cell_x + 4 * mm + 0.8 * mm + circle_radius
            circle_y = item_y + font_height * 0.5  # テキストのベースラインから円の中心まで
            
            if i in selected_indices:
                # 選択されている場合は塗りつぶし
                c.setFillColor(colors.black)
                c.circle(circle_x, circle_y, circle_radius, fill=1)
            else:
                # 選択されていない場合は輪郭のみ
                c.setStrokeColor(colors.HexColor('#333333'))
                c.setLineWidth(0.5)
                c.circle(circle_x, circle_y, circle_radius, fill=0)
            
            # テキストを描画（円の後）
            text_x = circle_x + circle_radius + 0.8 * mm
            c.setFillColor(colors.black)  # テキスト色をリセット
            c.drawString(text_x, item_y, self.cause_items[i])

        # 保存
        c.save()
        return self.filename


def get_ai_prompt_template(situation_text):
    """
    grok-4-1-fast-reasoning 等に投げるためのプロンプトを生成する関数。
    このプロンプトの回答をパースして generate_report の data 引数にする。
    """
    prompt = f"""
    あなたは放課後等デイサービスのベテラン職員です。以下の「状況」に基づき、
    ヒヤリハット報告書の各項目を埋めるためのJSONデータを作成してください。
    
    ## 状況入力
    {situation_text}

    ## 出力JSONフォーマット要件
    {{
        "location": "発生場所（具体的かつ簡潔に、100字以内）",
        "context": "どうしていた時（例：送迎車から降りる際、100字以内）",
        "details": "ヒヤリとした時のあらまし（客観的記述、100字以内）",
        "cause_indices": [該当する原因IDのリスト(1-12)],
           1:よく見えなかった 2:気が付かなかった 3:忘れていた 4:知らなかった
           5:深く考えなかった 6:大丈夫だと思った 7:あわてていた 8:不愉快なことがあった
           9:疲れていた 10:無意識に手が動いた 11:やりにくかった 12:体のバランスを崩した
        "category_index": 該当する分類のインデックス(0:環境, 1:設備, 2:指導方法, 3:自分自身),
        "countermeasure": "教訓・対策（具体的かつ実行可能なアクションプラン、100字以内）"
    }}
    
    重要: 各テキストフィールド（location, context, details, countermeasure）は必ず100字以内で記述してください。
    """
    return prompt
