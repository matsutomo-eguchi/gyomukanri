"""
ヒヤリハット報告書PDF生成モジュール
ReportLabを使用してヒヤリハット報告書のPDFを生成します
"""
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


class HiyariHattoGenerator:
    """
    ヒヤリハット報告書PDF生成クラス
    AI（grok-4-1-fast-reasoning等）からの構造化データ入力を想定
    """

    def __init__(self, filename="ヒヤリハット報告書.pdf"):
        """
        初期化
        
        Args:
            filename: 生成するPDFファイル名
        """
        self.filename = filename
        self.width, self.height = A4
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

        # --- タイトル ---
        c.setFont(self.font_bold, 18)
        c.drawCentredString(self.width / 2, self.height - 20 * mm, "ヒヤリハット報告書")

        # --- 記入者欄 ---
        y_pos = self.height - 40 * mm
        c.setFont(self.font_reg, 11)
        reporter_text = f"記入者: {reporter_name}" if reporter_name else "記入者: ____________________"
        c.drawString(self.width - 80 * mm, y_pos, reporter_text)

        y_pos -= 15 * mm

        # --- 【概要】セクション ---
        c.setFont(self.font_bold, 14)
        c.drawString(20 * mm, y_pos, "【概要】")
        y_pos -= 8 * mm

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
        time_str = f"{'午前' if dt.hour < 12 else '午後'} {dt.hour % 12 if dt.hour % 12 != 0 else 12}時 {dt.minute}分頃"
        date_text = f"令和 {reiwa_year} 年 {dt.month} 月 {dt.day} 日 ({weekday}曜日)  {time_str}"

        # 概要テーブル
        summary_data = [
            ["いつ", date_text],
            ["どこで", data.get('location', '')],
            ["どうして\nいた時", data.get('context', '')],
            ["ヒヤリとした\n時のあらまし", data.get('details', '')]
        ]

        summary_table = Table(summary_data, colWidths=[30 * mm, 140 * mm], rowHeights=[15 * mm, 15 * mm, 20 * mm, 40 * mm])
        summary_style = TableStyle([
            ('FONT', (0, 0), (-1, -1), self.font_reg, 10),
            ('FONT', (0, 0), (0, -1), self.font_bold, 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        summary_table.setStyle(summary_style)
        
        w, h = summary_table.wrapOn(c, self.width, self.height)
        summary_table.drawOn(c, 20 * mm, y_pos - h)
        y_pos -= h + 10 * mm

        # --- 【原因】セクション ---
        c.setFont(self.font_bold, 14)
        c.drawString(20 * mm, y_pos, "【原因】")
        y_pos -= 5 * mm
        
        c.setFont(self.font_reg, 9)
        c.drawString(20 * mm, y_pos, "該当する事項に○をつける")
        y_pos -= 8 * mm

        # 原因チェックリスト（2列で表示）
        selected_indices = data.get('cause_indices', [])
        cause_data = []
        keys = list(self.cause_items.keys())
        for i in range(0, len(keys), 2):
            row = []
            for j in range(2):
                if i + j < len(keys):
                    key = keys[i + j]
                    mark = "【○】" if key in selected_indices else "[   ]"
                    row.append(f"{mark} {key}. {self.cause_items[key]}")
                else:
                    row.append("")
            cause_data.append(row)

        cause_table = Table(cause_data, colWidths=[85 * mm, 85 * mm], rowHeights=[12 * mm] * len(cause_data))
        cause_style = TableStyle([
            ('FONT', (0, 0), (-1, -1), self.font_reg, 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ])
        cause_table.setStyle(cause_style)
        
        w, h = cause_table.wrapOn(c, self.width, self.height)
        cause_table.drawOn(c, 20 * mm, y_pos - h)
        y_pos -= h + 10 * mm

        # --- 【分類】セクション ---
        c.setFont(self.font_bold, 14)
        c.drawString(20 * mm, y_pos, "【分類】")
        y_pos -= 8 * mm

        category_index = data.get('category_index', -1)
        # 選択された分類にマークを追加（1行4列で表示）
        category_row = []
        for i, cat in enumerate(self.categories):
            if i == category_index:
                category_row.append(f"【○】\n{cat}")
            else:
                category_row.append(cat)
        
        category_data = [category_row]
        category_table = Table(category_data, colWidths=[42.5 * mm] * 4, rowHeights=[15 * mm])
        category_style = TableStyle([
            ('FONT', (0, 0), (-1, -1), self.font_reg, 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ])
        category_table.setStyle(category_style)
        
        w, h = category_table.wrapOn(c, self.width, self.height)
        category_table.drawOn(c, 20 * mm, y_pos - h)
        y_pos -= h + 10 * mm

        # --- 【教訓・対策】セクション ---
        c.setFont(self.font_bold, 14)
        c.drawString(20 * mm, y_pos, "【教訓・対策】")
        y_pos -= 8 * mm

        countermeasure = data.get('countermeasure', '')
        countermeasure_data = [[countermeasure]]
        countermeasure_table = Table(countermeasure_data, colWidths=[170 * mm], rowHeights=[60 * mm])
        countermeasure_style = TableStyle([
            ('FONT', (0, 0), (-1, -1), self.font_reg, 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        countermeasure_table.setStyle(countermeasure_style)
        
        w, h = countermeasure_table.wrapOn(c, self.width, self.height)
        countermeasure_table.drawOn(c, 20 * mm, y_pos - h)

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
