"""
ヒヤリハット報告書PDF生成モジュール
ReportLabを使用してヒヤリハット報告書のPDFを生成します
HTMLテンプレートに忠実なレイアウトを実現します
"""
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, pt
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class HiyariHattoGenerator:
    """
    ヒヤリハット報告書PDF生成クラス
    AI（grok-4-1-fast-reasoning等）からの構造化データ入力を想定
    HTMLテンプレートに忠実に実装
    """

    def __init__(self, filename="ヒヤリハット報告書.pdf"):
        """
        初期化
        
        Args:
            filename: 生成するPDFファイル名
        """
        self.filename = filename
        self.width, self.height = A4
        self.margin = 15 * mm  # HTMLのpadding: 15mmに合わせる
        
        # 日本語フォントの登録 (HeiseiMin=明朝体, HeiseiKakuGo=ゴシック体)
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3-Acro"))
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5-Acro"))
            self.font_reg = "HeiseiMin-W3-Acro"
            self.font_bold = "HeiseiKakuGo-W5-Acro"
        except Exception:
            # フォント登録に失敗した場合のフォールバック
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
        # 本文用スタイル（11pt、明朝体、line-height: 1.4）
        self.para_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontName=self.font_reg,
            fontSize=11,
            leading=15.4,  # line-height: 1.4
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
        )
        
        # セクションタイトル用スタイル（16px、太字）
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
        
        # セルの中央に配置
        center_x = x + width / 2
        center_y = y + height / 2
        
        # 文字間隔を計算（letter-spacing: 0.5em）
        char_spacing = font_size * 0.5
        
        # テキストの総高さを計算
        total_height = len(text) * (font_size + char_spacing) - char_spacing
        
        # 開始位置を計算（中央から上に）
        start_y = center_y + total_height / 2 - font_size
        
        # 各文字を縦に配置
        for i, char in enumerate(text):
            char_y = start_y - i * (font_size + char_spacing)
            canvas_obj.saveState()
            canvas_obj.translate(center_x, char_y)
            canvas_obj.rotate(90)
            canvas_obj.setFont(font_name, font_size)
            char_width = canvas_obj.stringWidth(char, font_name, font_size)
            canvas_obj.drawString(-char_width / 2, 0, char)
            canvas_obj.restoreState()
        
        canvas_obj.restoreState()
    
    def px_to_mm(self, px_value):
        """
        px値をmm値に変換（1px ≈ 0.264583mm）
        
        Args:
            px_value: px値
            
        Returns:
            mm値
        """
        return px_value * 0.264583
    
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
        # HTML: font-size: 24px, text-align: center, margin-bottom: 30px, letter-spacing: 2px
        title_y = current_y - self.px_to_mm(30)  # 30px margin-bottomをmmに変換
        c.setFont(self.font_bold, 24)
        title_text = "ヒヤリハット報告書"
        title_width = c.stringWidth(title_text, self.font_bold, 24)
        c.drawString((self.width - title_width) / 2, title_y, title_text)
        current_y = title_y - self.px_to_mm(30)  # margin-bottom: 30px

        # ===== 記入者欄 =====
        # HTML: text-align: right, border-bottom: 1px solid black, width: 150px
        reporter_y = current_y - self.px_to_mm(5)  # margin-bottom: 5px
        c.setFont(self.font_reg, 11)
        reporter_label = "記入者"
        reporter_input = reporter_name if reporter_name else ""
        
        # 右寄せで描画
        label_width = c.stringWidth(reporter_label, self.font_reg, 11)
        input_width = self.px_to_mm(150)  # 150pxをmmに変換
        input_x = self.width - self.margin - input_width
        label_x = input_x - label_width - 3 * mm
        
        c.drawString(label_x, reporter_y, reporter_label)
        # 下線を描画
        c.setLineWidth(1)
        c.line(input_x, reporter_y - 2, input_x + input_width, reporter_y - 2)
        if reporter_input:
            c.drawString(input_x + 2 * mm, reporter_y, reporter_input)
        
        current_y = reporter_y - self.px_to_mm(5)  # margin-bottom: 5px

        # ===== 【概要】セクション =====
        # HTML: section-title, font-size: 16px, margin-top: 20px, margin-bottom: 5px
        current_y -= self.px_to_mm(20)  # margin-top: 20px
        c.setFont(self.font_bold, 16)
        c.drawString(start_x, current_y, "【概要】")
        current_y -= self.px_to_mm(5)  # margin-bottom: 5px

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

        # 概要テーブル
        # HTML: テーブル構造
        # 行1: "いつ"（縦書き、letter-spacing: 0.5em）| 日時入力（colspan=2）
        # 行2: "どこで"（縦書き）| テキストエリア（60%幅、100px高さ）| "どうしていた時"（縦書き）| テキストエリア（30%幅、80px高さ）
        # 行3: "ヒヤリとした時のあらまし"（縦書き）| テキストエリア（colspan=2、120px高さ）
        
        # 列幅の計算（HTML: col-label-narrow: 10%, col-where: 60%, col-doing: 30%）
        label_col_width = content_width * 0.10
        where_col_width = content_width * 0.60
        doing_col_width = content_width * 0.30
        
        # 日時テキストの作成
        date_text = f"令和 {reiwa_year} 年 {dt.month} 月 {dt.day} 日 ( {weekday} 曜日)    {am_pm} {hour} 時 {minute} 分頃"
        
        summary_data = [
            ["", date_text, ""],  # 行1: "いつ"は後で縦書きで描画
            ["", Paragraph(data.get('location', ''), self.para_style), Paragraph(data.get('context', ''), self.para_style)],
            ["", Paragraph(data.get('details', ''), self.para_style), ""]
        ]
        
        # 行の高さ（HTML: 100px, 80px, 120px）
        summary_row_heights = [
            15 * mm,  # 行1（日時行）
            self.px_to_mm(100),  # 行2（どこで/どうしていた時）
            self.px_to_mm(120),  # 行3（あらまし）
        ]
        
        summary_table = Table(
            summary_data,
            colWidths=[label_col_width, where_col_width, doing_col_width],
            rowHeights=summary_row_heights
        )
        
        summary_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # border: 1px solid #000
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            # 行1の列2と列3を結合（colspan=2）
            ('SPAN', (1, 0), (2, 0)),
            # 行3の列2と列3を結合（colspan=2）
            ('SPAN', (1, 2), (2, 2)),
        ])
        
        summary_table.setStyle(summary_style)
        summary_w, summary_h = summary_table.wrapOn(c, content_width, content_height)
        summary_table_y = current_y - summary_h
        summary_table.drawOn(c, start_x, summary_table_y)
        
        # 縦書きテキストを描画
        # 行1: "いつ"（letter-spacing: 0.5em）
        cell_x = start_x
        cell_y = summary_table_y + summary_row_heights[2] + summary_row_heights[1]  # 下から2行目
        self.draw_vertical_text(c, "いつ", cell_x, cell_y, label_col_width, summary_row_heights[0], self.font_bold, 11)
        
        # 行2: "どこで"
        cell_y = summary_table_y + summary_row_heights[2]  # 下から1行目
        self.draw_vertical_text(c, "どこで", cell_x, cell_y, label_col_width, summary_row_heights[1], self.font_reg, 11)
        
        # 行2: "どうしていた時"（右側の列）
        doing_label_x = start_x + label_col_width + where_col_width
        self.draw_vertical_text(c, "どうして\nい た 時", doing_label_x, cell_y, doing_col_width, summary_row_heights[1], self.font_bold, 11)
        
        # 行3: "ヒヤリとした時のあらまし"
        cell_y = summary_table_y  # 最下段
        self.draw_vertical_text(c, "ヒヤリとした\n時のあらまし", cell_x, cell_y, label_col_width, summary_row_heights[2], self.font_reg, 11)
        
        current_y = summary_table_y - self.px_to_mm(20)  # margin-bottom: 20px

        # ===== 【原因】セクション =====
        # HTML: section-title, font-size: 16px, margin-top: 20px, margin-bottom: 5px
        current_y -= self.px_to_mm(20)  # margin-top: 20px
        c.setFont(self.font_bold, 16)
        c.drawString(start_x, current_y, "【原因】")
        current_y -= self.px_to_mm(5)  # margin-bottom: 5px

        # 原因テーブル
        # HTML: ヘッダー行（背景色#f9f9f9、14px、通常フォント）+ データ行（4列のテキストエリア、各100px高さ）
        category_index = data.get('category_index', -1)
        
        # 各カテゴリのテキストを取得（dataから、なければ空文字列）
        category_texts = {
            0: data.get('cause_environment', ''),
            1: data.get('cause_equipment', ''),
            2: data.get('cause_guidance', ''),
            3: data.get('cause_self', '')
        }
        
        # テーブルデータ: ヘッダー行 + データ行
        cause_header_row = [self.categories[0], self.categories[1], self.categories[2], self.categories[3]]
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
            rowHeights=[None, self.px_to_mm(100)]  # ヘッダー行は自動、データ行は100px
        )
        
        cause_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # ヘッダー行中央
            ('ALIGN', (0, 1), (-1, 1), 'LEFT'),    # データ行左
            ('FONT', (0, 0), (-1, 0), self.font_reg, 14),  # ヘッダー行: 14px
            ('FONT', (0, 1), (-1, 1), self.font_reg, 11),  # データ行: 11px
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f9f9f9')),  # ヘッダー背景色
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        
        cause_table.setStyle(cause_style)
        cause_w, cause_h = cause_table.wrapOn(c, content_width, content_height)
        cause_table_y = current_y - cause_h
        cause_table.drawOn(c, start_x, cause_table_y)
        current_y = cause_table_y - self.px_to_mm(5)  # margin-bottom: 5px

        # ===== 矢印 =====
        # HTML: arrow-container, text-align: right, padding-right: 12%, margin-top: -15px, margin-bottom: 5px, font-size: 30px
        current_y -= self.px_to_mm(-15)  # margin-top: -15px（上に移動）
        arrow_x = start_x + content_width - (content_width * 0.12)  # padding-right: 12%
        c.setFont(self.font_reg, 30)
        c.drawString(arrow_x, current_y, "⇩")
        current_y -= self.px_to_mm(5)  # margin-bottom: 5px

        # ===== 【教訓・対策】セクション =====
        # HTML: section-title + "該当する事項に○をつける"（右寄せ、14px）
        current_y -= self.px_to_mm(20)  # margin-top: 20px（section-titleのmargin-top）
        
        # セクションタイトルと説明文を横並びに
        c.setFont(self.font_bold, 16)
        c.drawString(start_x, current_y, "【教訓・対策】")
        
        # 説明文（右寄せ）
        instruction_text = "該当する事項に○をつける"
        c.setFont(self.font_reg, 14)
        instruction_width = c.stringWidth(instruction_text, self.font_reg, 14)
        c.drawString(start_x + content_width - instruction_width, current_y, instruction_text)
        
        current_y -= self.px_to_mm(5)  # margin-bottom: 5px

        # 教訓・対策テーブル
        # HTML: 左列（60%幅、350px高さのテキストエリア）+ 右列（チェックリスト）
        countermeasure = data.get('countermeasure', '')
        selected_indices = data.get('cause_indices', [])
        
        # テーブルデータ: 左列（教訓・対策）+ 右列（空、後で手動描画）
        countermeasure_col_width = content_width * 0.60
        checklist_col_width = content_width * 0.40
        
        countermeasure_table_data = [
            [Paragraph(countermeasure, self.para_style), ""]  # 右列は空、後で手動描画
        ]
        
        countermeasure_table = Table(
            countermeasure_table_data,
            colWidths=[countermeasure_col_width, checklist_col_width],
            rowHeights=[self.px_to_mm(350)]  # 350px高さ
        )
        
        countermeasure_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), self.px_to_mm(15)),  # padding: 15px
            ('RIGHTPADDING', (0, 0), (-1, -1), self.px_to_mm(15)),
            ('TOPPADDING', (0, 0), (-1, -1), self.px_to_mm(15)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), self.px_to_mm(15)),
        ])
        
        countermeasure_table.setStyle(countermeasure_style)
        countermeasure_w, countermeasure_h = countermeasure_table.wrapOn(c, content_width, content_height)
        countermeasure_table_y = current_y - countermeasure_h
        countermeasure_table.drawOn(c, start_x, countermeasure_table_y)
        
        # チェックリストを手動で描画
        # HTML: padding: 15px, font-size: 14px, margin-bottom: 8px
        checklist_cell_x = start_x + countermeasure_col_width + self.px_to_mm(15)  # padding考慮
        checklist_cell_y = countermeasure_table_y + countermeasure_h - self.px_to_mm(15)  # padding考慮（上から）
        
        # 円のサイズ（16px）
        circle_radius = self.px_to_mm(8)  # 16px / 2
        
        # チェックリストのフォントサイズ（14px）
        font_size_pt = 14
        c.setFont(self.font_reg, font_size_pt)
        
        # 行間（margin-bottom: 8px）
        line_spacing = self.px_to_mm(8)
        
        # フォントの高さ（14px ≈ 3.7mm）
        font_height = self.px_to_mm(14) * 1.4  # line-height考慮
        
        for i in range(1, 13):
            # 各項目のY位置を計算（上から下へ）
            # 最初の項目は上から15px（padding）の位置
            # 以降はフォント高さ + 行間ずつ下に
            item_y = checklist_cell_y - (i - 1) * (font_height + line_spacing)
            
            # 番号を描画（右寄せ、幅25px）
            num_text = str(i)
            num_width = c.stringWidth(num_text, self.font_reg, font_size_pt)
            num_x = checklist_cell_x + self.px_to_mm(25) - num_width
            c.drawString(num_x, item_y, num_text)
            
            # 円を描画（番号の後、margin-right: 5px）
            circle_x = checklist_cell_x + self.px_to_mm(25) + self.px_to_mm(5) + circle_radius
            circle_y = item_y + font_height * 0.5  # テキストのベースラインから円の中心まで
            
            if i in selected_indices:
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
        "location": "発生場所（具体的かつ簡潔に）",
        "context": "どうしていた時（例：送迎車から降りる際）",
        "details": "ヒヤリとした時のあらまし（客観的記述）",
        "cause_indices": [該当する原因IDのリスト(1-12)],
           1:よく見えなかった 2:気が付かなかった 3:忘れていた 4:知らなかった
           5:深く考えなかった 6:大丈夫だと思った 7:あわてていた 8:不愉快なことがあった
           9:疲れていた 10:無意識に手が動いた 11:やりにくかった 12:体のバランスを崩した
        "category_index": 該当する分類のインデックス(0:環境, 1:設備, 2:指導方法, 3:自分自身),
        "countermeasure": "教訓・対策（具体的かつ実行可能なアクションプラン）"
    }}
    """
    return prompt
