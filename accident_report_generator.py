"""
事故報告書PDF生成モジュール
ReportLabを使用して事故報告書のPDFを生成します
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


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

    def generate(self, data):
        """
        AIが生成したデータを受け取りPDFを作成する
        
        Args:
            data: 事故報告の内容を含む辞書
                - facility_name: 事業所名
                - date_year, date_month, date_day: 発生日（年、月、日）
                - date_weekday: 曜日
                - time_hour, time_min: 発生時刻（時、分）
                - location: 発生場所
                - subject_name: 対象者名
                - situation: 事故発生の状況
                - process: 経過
                - cause: 事故原因
                - countermeasure: 対策
                - others: その他
                - reporter_name: 報告者氏名
                - record_date: 記録日
        """
        c = canvas.Canvas(self.filename, pagesize=A4)
        c.setTitle("事故状況・対策報告書")

        # --- タイトル ---
        c.setFont(self.font_bold, 18)
        c.drawCentredString(self.width / 2, self.height - 20 * mm, "事故状況・対策報告書")

        # --- ヘッダー情報 (事業所名など) ---
        y_pos = self.height - 40 * mm
        c.setFont(self.font_bold, 11)
        c.drawString(20 * mm, y_pos, "【事業所名】")
        c.setFont(self.font_reg, 11)
        # 事業所名の下線
        c.line(45 * mm, y_pos - 1 * mm, 120 * mm, y_pos - 1 * mm)
        c.drawString(45 * mm, y_pos, data.get("facility_name", ""))

        # --- 事故基本情報 (グリッドレイアウト) ---
        # 報告内容, 発生場所, 対象者などを配置
        y_pos -= 10 * mm
        
        # 発生日時
        c.setFont(self.font_bold, 10)
        c.drawString(20 * mm, y_pos, "事故発生日時：")
        c.setFont(self.font_reg, 10)
        date_str = f"{data.get('date_year', '    ')} 年  {data.get('date_month', '  ')} 月  {data.get('date_day', '  ')} 日"
        time_str = f"{data.get('time_hour', '  ')} 時  {data.get('time_min', '  ')} 分頃"
        weekday = f"({data.get('date_weekday', '  ')})曜日"
        c.drawString(50 * mm, y_pos, f"{date_str}   {time_str}   {weekday}")

        y_pos -= 8 * mm
        c.setFont(self.font_bold, 10)
        c.drawString(20 * mm, y_pos, "発生場所：")
        c.setFont(self.font_reg, 10)
        c.drawString(50 * mm, y_pos, data.get("location", ""))

        c.setFont(self.font_bold, 10)
        c.drawString(110 * mm, y_pos, "対象者：")
        c.setFont(self.font_reg, 10)
        c.drawString(130 * mm, y_pos, data.get("subject_name", ""))

        # --- メインテーブル (状況、経過、原因、対策、その他) ---
        # テーブルの定義
        headers = [
            ("事故発生の\n状況", data.get("situation", "")),
            ("経過", data.get("process", "")),
            ("事故原因", data.get("cause", "")),
            ("対策", data.get("countermeasure", "")),
            ("その他", data.get("others", ""))
        ]

        table_data = []
        for title, content in headers:
            table_data.append([title, content])

        # テーブルスタイル
        t_style = [
            ('FONT', (0, 0), (-1, -1), self.font_reg, 10),
            ('FONT', (0, 0), (0, -1), self.font_bold, 10),  # 左列は太字
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # 左列は中央揃え
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),     # 右列は左揃え
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]

        # 列幅の設定 (左カラム: 30mm, 右カラム: 残り)
        col_widths = [30 * mm, 140 * mm]
        # 行の高さ (概算で配分)
        row_heights = [50 * mm, 30 * mm, 30 * mm, 40 * mm, 20 * mm]

        t = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
        t.setStyle(TableStyle(t_style))
        
        # テーブルを描画
        w, h = t.wrapOn(c, self.width, self.height)
        t.drawOn(c, 20 * mm, y_pos - h - 5 * mm)  # 前の要素の下に配置

        footer_y_start = y_pos - h - 15 * mm

        # --- フッター (署名欄) ---
        # 管理者、報告者、記録日
        c.setFont(self.font_reg, 10)
        
        # 枠線ボックスの作成
        box_y = footer_y_start - 20 * mm
        
        # 管理者印欄
        c.rect(110 * mm, box_y, 25 * mm, 20 * mm)
        c.drawString(112 * mm, box_y + 16 * mm, "管理者")
        
        # 報告者氏名欄
        c.rect(140 * mm, box_y, 40 * mm, 20 * mm)
        c.drawString(142 * mm, box_y + 16 * mm, "報告者氏名")
        c.drawString(145 * mm, box_y + 5 * mm, data.get("reporter_name", ""))

        # 記録日
        c.drawString(140 * mm, box_y + 22 * mm, f"記録日: {data.get('record_date', '')}")

        # --- 保護者確認欄 ---
        confirm_y = box_y - 35 * mm
        c.rect(20 * mm, confirm_y, 160 * mm, 30 * mm)
        
        c.setFont(self.font_reg, 9)
        c.drawString(25 * mm, confirm_y + 25 * mm, "上記について、説明を受けました。")
        c.drawString(100 * mm, confirm_y + 25 * mm, "(説明が必要な場合に署名・捺印を頂きます)")
        
        # 日付署名欄
        c.setFont(self.font_reg, 11)
        c.drawString(30 * mm, confirm_y + 10 * mm, "年       月       日")
        c.drawString(90 * mm, confirm_y + 10 * mm, "氏名")
        c.line(105 * mm, confirm_y + 10 * mm, 170 * mm, confirm_y + 10 * mm)  # 氏名の下線

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
            "date_weekday": weekday
        }

