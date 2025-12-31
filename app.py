"""
放課後等デイサービス 業務管理フォーム（日報）
Streamlitアプリケーション
"""
import streamlit as st
import os
from datetime import date, datetime, time
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
import tempfile
import calendar

from data_manager import DataManager
from ai_helper import AIHelper
from accident_report_generator import AccidentReportGenerator
from hiyari_hatto_generator import HiyariHattoGenerator


# ページ設定
st.set_page_config(
    page_title="業務管理フォーム",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #4ECDC4;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #4ECDC4;
        padding-bottom: 0.5rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4ECDC4;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #45B8B0;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
    
    # データ保護の確認と警告表示
    data_dir = Path("data")
    if data_dir.exists():
        # 既存データが存在する場合、保護されていることを確認
        protection_marker = data_dir / ".data_protected"
        if protection_marker.exists():
            # データ保護が有効になっていることを確認（初回のみ表示）
            if 'data_protection_notified' not in st.session_state:
                st.session_state.data_protection_notified = True
                # サイドバーに情報を表示（初回のみ）
                with st.sidebar:
                    st.info("✅ データ保護が有効です。コード更新時も記録は保持されます。")

if 'ai_helper' not in st.session_state:
    # APIキーの取得（優先順位: 環境変数 > Streamlit Secrets > 保存された設定）
    api_key = None
    gemini_api_key = None
    
    # 1. 環境変数から取得
    api_key = os.getenv("GROK_API_KEY", None)
    gemini_api_key = os.getenv("GEMINI_API_KEY", None)
    
    # 2. Streamlit Secretsから取得
    if not api_key:
        try:
            if hasattr(st, 'secrets') and hasattr(st.secrets, 'get'):
                api_key = st.secrets.get("GROK_API_KEY", None)
        except (FileNotFoundError, AttributeError):
            pass
    
    if not gemini_api_key:
        try:
            if hasattr(st, 'secrets') and hasattr(st.secrets, 'get'):
                gemini_api_key = st.secrets.get("GEMINI_API_KEY", None)
        except (FileNotFoundError, AttributeError):
            pass
    
    # 3. 保存された設定から取得
    if not api_key:
        api_key = st.session_state.data_manager.get_api_key()
    
    if not gemini_api_key:
        gemini_api_key = st.session_state.data_manager.get_gemini_api_key()
    
    st.session_state.ai_helper = AIHelper(api_key=api_key, gemini_api_key=gemini_api_key)

if 'current_page' not in st.session_state:
    st.session_state.current_page = "日報入力"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# 定型タグの定義（初期値、データマネージャーから動的に取得される）
LEARNING_TAGS_DEFAULT = [
    "プリント学習", "宿題", "SST（ソーシャルスキルトレーニング）", 
    "読み書き練習", "計算練習", "工作", "絵本の読み聞かせ"
]

FREE_PLAY_TAGS_DEFAULT = [
    "ブロック遊び", "お絵描き", "読書", "パズル", "カードゲーム",
    "ままごと", "積み木", "折り紙", "ぬりえ", "音楽鑑賞"
]

GROUP_PLAY_TAGS_DEFAULT = [
    "リトミック", "体操", "公園遊び", "ボール遊び", "鬼ごっこ",
    "ダンス", "集団ゲーム", "散歩", "運動遊び", "歌"
]

VEHICLE_OPTIONS = [
    "ノア", "セレナ（シルバー）", "セレナ（白）"
]


def generate_time_options():
    """5分刻みの時刻リストを生成（9:00〜18:30の範囲）"""
    times = []
    # 9:00から18:30まで
    start_hour = 9
    end_hour = 18
    end_minute = 30
    
    for hour in range(start_hour, end_hour + 1):
        minute_range = range(0, 60, 5) if hour < end_hour else range(0, end_minute + 1, 5)
        for minute in minute_range:
            time_str = f"{hour:02d}:{minute:02d}"
            times.append(time_str)
    return times


def render_login_page():
    """ログインページの描画"""
    st.markdown('<div class="main-header">🔐 ログイン</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        with st.form("login_form"):
            st.markdown("#### スタッフログイン")
            
            user_id = st.text_input(
                "ユーザーID",
                key="login_user_id",
                placeholder="ユーザーIDを入力してください"
            )
            
            password = st.text_input(
                "パスワード",
                type="password",
                key="login_password",
                placeholder="パスワードを入力してください"
            )
            
            login_submitted = st.form_submit_button("ログイン", use_container_width=True, type="primary")
            
            if login_submitted:
                if not user_id or not password:
                    st.error("ユーザーIDとパスワードを入力してください")
                else:
                    account = st.session_state.data_manager.verify_login(user_id, password)
                    if account:
                        st.session_state.logged_in = True
                        st.session_state.logged_in_user = account
                        st.session_state.staff_name = account["name"]
                        st.success(f"✅ {account['name']}さん、ようこそ！")
                        st.rerun()
                    else:
                        st.error("ユーザーIDまたはパスワードが正しくありません")
        
        st.markdown("---")
        
        # アカウント作成セクション
        with st.expander("📝 新規アカウント作成", expanded=False):
            with st.form("create_account_form"):
                st.markdown("#### 新規スタッフアカウント作成")
                
                new_user_id = st.text_input(
                    "ユーザーID",
                    key="new_user_id",
                    placeholder="英数字で入力してください",
                    help="ログイン時に使用するIDです"
                )
                
                new_password = st.text_input(
                    "パスワード",
                    type="password",
                    key="new_password",
                    placeholder="パスワードを入力してください"
                )
                
                new_password_confirm = st.text_input(
                    "パスワード（確認）",
                    type="password",
                    key="new_password_confirm",
                    placeholder="パスワードを再度入力してください"
                )
                
                new_staff_name = st.text_input(
                    "スタッフ名",
                    key="new_staff_name",
                    placeholder="表示名を入力してください"
                )
                
                create_submitted = st.form_submit_button("アカウント作成", use_container_width=True)
                
                if create_submitted:
                    errors = []
                    if not new_user_id or not new_user_id.strip():
                        errors.append("ユーザーIDを入力してください")
                    if not new_password:
                        errors.append("パスワードを入力してください")
                    elif len(new_password) < 4:
                        errors.append("パスワードは4文字以上にしてください")
                    elif new_password != new_password_confirm:
                        errors.append("パスワードが一致しません")
                    if not new_staff_name or not new_staff_name.strip():
                        errors.append("スタッフ名を入力してください")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        if st.session_state.data_manager.create_staff_account(
                            new_user_id.strip(),
                            new_password,
                            new_staff_name.strip()
                        ):
                            st.success(f"✅ アカウント '{new_user_id}' を作成しました！ログインしてください。")
                            st.rerun()
                        else:
                            st.error("アカウント作成に失敗しました。ユーザーIDが既に使用されている可能性があります。")


def render_sidebar():
    """サイドバーの描画"""
    with st.sidebar:
        st.title("📋 業務管理フォーム")
        
        # ログイン情報表示
        if st.session_state.logged_in and st.session_state.logged_in_user:
            st.info(f"👤 {st.session_state.logged_in_user['name']} ({st.session_state.logged_in_user['user_id']})")
            if st.button("🚪 ログアウト", use_container_width=True, type="secondary"):
                st.session_state.logged_in = False
                st.session_state.logged_in_user = None
                st.session_state.staff_name = ""
                st.rerun()
        
        st.markdown("---")
        
        # ページ選択
        page = st.radio(
            "メニュー",
            ["日報入力", "保存済み日報閲覧", "利用者記録閲覧", "朝礼議事録", "利用者マスタ管理", "設定"],
            key="page_selector"
        )
        st.session_state.current_page = page
        
        st.markdown("---")
        
        # 基本情報（全ページ共通）
        st.subheader("基本情報")
        work_date = st.date_input(
            "業務日",
            value=date.today(),
            key="work_date"
        )
        
        # ログイン済みの場合はスタッフ名を自動設定
        if st.session_state.logged_in and st.session_state.logged_in_user:
            staff_name = st.text_input(
                "記入スタッフ名",
                value=st.session_state.logged_in_user["name"],
                key="staff_name",
                disabled=True
            )
        else:
            staff_name = st.text_input(
                "記入スタッフ名",
                value=st.session_state.get("staff_name", ""),
                key="staff_name"
            )
        
        st.markdown("---")
        
        # 勤務時間
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("始業時間", value=time(9, 0), key="start_time")
        with col2:
            end_time = st.time_input("終業時間", value=time(17, 0), key="end_time")
        
        st.markdown("---")
        
        # 1日の利用者数合計を表示
        try:
            daily_user_count = st.session_state.data_manager.get_daily_user_count(
                work_date.isoformat()
            )
        except Exception as e:
            # エラーが発生した場合は0を返す
            daily_user_count = 0
            # デバッグ用（必要に応じてコメントアウト）
            # st.error(f"利用者数取得エラー: {str(e)}")
        
        # 常に表示（データがない場合は0名）
        st.metric(
            label="📊 本日の利用者数",
            value=f"{daily_user_count}名"
        )
        
        st.markdown("---")
        
        # 簡易利用者記録機能
        st.subheader("👥 利用者記録")
        
        # 登録済み利用者を取得
        registered_users = st.session_state.data_manager.get_active_users()
        
        if registered_users:
            # その日の利用者記録を取得
            today_users = st.session_state.data_manager.get_daily_users(
                work_date.isoformat()
            )
            
            # プルダウンで利用者を選択（複数選択可能）
            selected_users = st.multiselect(
                "利用者を選択",
                options=registered_users,
                default=today_users,
                key="daily_users_selection",
                help="その日の利用者を選択してください"
            )
            
            # 選択した利用者の一覧を表示
            if selected_users:
                st.markdown("**選択中の利用者:**")
                for idx, user_name in enumerate(selected_users, 1):
                    st.markdown(f"{idx}. {user_name}")
                
                st.markdown(f"**合計: {len(selected_users)}名**")
                
                # 保存ボタン
                if st.button("💾 利用者記録を保存", use_container_width=True, type="primary"):
                    if st.session_state.data_manager.save_daily_users(
                        work_date.isoformat(),
                        selected_users
                    ):
                        st.success(f"✅ {len(selected_users)}名の利用者を記録しました")
                        st.rerun()
                    else:
                        st.error("保存に失敗しました")
            else:
                st.info("利用者を選択してください")
                
                # 既存の記録がある場合は表示
                if today_users:
                    st.markdown("**現在の記録:**")
                    for idx, user_name in enumerate(today_users, 1):
                        st.markdown(f"{idx}. {user_name}")
                    st.markdown(f"**合計: {len(today_users)}名**")
        else:
            st.warning("利用者が登録されていません。先に「利用者マスタ管理」で利用者を追加してください。")


def render_ai_assistant(text_area_key: str, child_name: Optional[str] = None):
    """AI文章生成アシストUI"""
    st.markdown("#### 🤖 AI文章作成アシスト")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        keywords = st.text_area(
            "キーワードや箇条書きを入力してください",
            height=100,
            key=f"keywords_{text_area_key}",
            placeholder="例: 機嫌良し、給食完食、公園で鬼ごっこを楽しむ、お友達と仲良く遊ぶ"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("✨ 文章生成", key=f"generate_{text_area_key}", use_container_width=True)
        improve_btn = st.button("📝 文章改善", key=f"improve_{text_area_key}", use_container_width=True)
    
    if generate_btn and keywords:
        with st.spinner("AIが文章を生成中..."):
            success, result = st.session_state.ai_helper.generate_report_text(keywords, child_name)
            if success:
                st.session_state[f"generated_text_{text_area_key}"] = result
                st.success("文章を生成しました！")
            else:
                st.error(result)
    
    if improve_btn:
        current_text = st.session_state.get(text_area_key, "")
        if current_text:
            with st.spinner("AIが文章を改善中..."):
                success, result = st.session_state.ai_helper.improve_text(current_text)
                if success:
                    st.session_state[f"generated_text_{text_area_key}"] = result
                    st.success("文章を改善しました！")
                else:
                    st.error(result)
        else:
            st.warning("改善したい文章を先に入力してください。")
    
    # 生成された文章の表示と適用
    if f"generated_text_{text_area_key}" in st.session_state:
        st.markdown("**生成された文章:**")
        st.text_area(
            "プレビュー",
            value=st.session_state[f"generated_text_{text_area_key}"],
            height=150,
            key=f"preview_{text_area_key}",
            disabled=True
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ この文章を使用", key=f"apply_{text_area_key}"):
                st.session_state[text_area_key] = st.session_state[f"generated_text_{text_area_key}"]
                del st.session_state[f"generated_text_{text_area_key}"]
                st.rerun()
        with col2:
            if st.button("❌ キャンセル", key=f"cancel_{text_area_key}"):
                del st.session_state[f"generated_text_{text_area_key}"]
                st.rerun()


def render_accident_ai_assistant(text_area_key: str, report_type: str):
    """事故報告書用AI文章生成アシストUI"""
    st.markdown(f"#### 🤖 AI文章作成アシスト（{report_type}）")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        keywords = st.text_area(
            "キーワードや箇条書きを入力してください",
            height=80,
            key=f"keywords_{text_area_key}",
            placeholder="例: プレイルーム、バランスボール、転倒しそうになった、マットがなかった"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("✨ 文章生成", key=f"generate_{text_area_key}", use_container_width=True)
    
    if generate_btn and keywords:
        with st.spinner("AIが文章を生成中..."):
            success, result = st.session_state.ai_helper.generate_accident_report(keywords, report_type)
            if success:
                st.session_state[f"generated_text_{text_area_key}"] = result
                st.success("文章を生成しました！")
            else:
                st.error(result)
    
    # 生成された文章の表示と適用
    if f"generated_text_{text_area_key}" in st.session_state:
        st.markdown("**生成された文章:**")
        st.text_area(
            "プレビュー",
            value=st.session_state[f"generated_text_{text_area_key}"],
            height=100,
            key=f"preview_{text_area_key}",
            disabled=True
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ この文章を使用", key=f"apply_{text_area_key}"):
                st.session_state[text_area_key] = st.session_state[f"generated_text_{text_area_key}"]
                del st.session_state[f"generated_text_{text_area_key}"]
                st.rerun()
        with col2:
            if st.button("❌ キャンセル", key=f"cancel_{text_area_key}"):
                del st.session_state[f"generated_text_{text_area_key}"]
                st.rerun()


def render_hiyari_ai_assistant(text_area_key: str, report_type: str):
    """ヒヤリハット報告書用AI文章生成アシストUI"""
    type_names = {
        "context": "どうしていた時",
        "details": "ヒヤリとした時のあらまし",
        "countermeasure": "教訓・対策"
    }
    type_name = type_names.get(report_type, report_type)
    
    st.markdown(f"#### 🤖 AI文章作成アシスト（{type_name}）")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        keywords = st.text_area(
            "キーワードや箇条書きを入力してください",
            height=80,
            key=f"keywords_{text_area_key}",
            placeholder="例: 送迎車から降りる際、バランスを崩した、マットがなかった"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("✨ 文章生成", key=f"generate_{text_area_key}", use_container_width=True)
    
    if generate_btn and keywords:
        with st.spinner("AIが文章を生成中..."):
            success, result = st.session_state.ai_helper.generate_hiyari_hatto_report(keywords, report_type)
            if success:
                st.session_state[f"generated_text_{text_area_key}"] = result
                st.success("文章を生成しました！")
            else:
                st.error(result)
    
    # 生成された文章の表示と適用
    if f"generated_text_{text_area_key}" in st.session_state:
        st.markdown("**生成された文章:**")
        st.text_area(
            "プレビュー",
            value=st.session_state[f"generated_text_{text_area_key}"],
            height=100,
            key=f"preview_{text_area_key}",
            disabled=True
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ この文章を使用", key=f"apply_{text_area_key}"):
                st.session_state[text_area_key] = st.session_state[f"generated_text_{text_area_key}"]
                del st.session_state[f"generated_text_{text_area_key}"]
                st.rerun()
        with col2:
            if st.button("❌ キャンセル", key=f"cancel_{text_area_key}"):
                del st.session_state[f"generated_text_{text_area_key}"]
                st.rerun()


def render_daily_report_form():
    """日報入力フォームの描画"""
    st.markdown('<div class="main-header">📋 日報入力</div>', unsafe_allow_html=True)
    
    # 利用者リストを取得
    users = st.session_state.data_manager.get_active_users()
    
    if not users:
        st.warning("⚠️ 利用者が登録されていません。先に「利用者マスタ管理」で利用者を追加してください。")
        return
    
    # 複数名担当対応のため、タブを使用（最大15名まで）
    tab_labels = [f"担当児童{i+1}" for i in range(15)]
    tabs = st.tabs(tab_labels)
    
    all_reports = []
    
    for tab_idx, tab in enumerate(tabs):
        with tab:
            st.markdown(f'<div class="section-header">担当児童 {tab_idx + 1}</div>', unsafe_allow_html=True)
            
            # 担当利用者名（フォーム外）
            child_name = st.selectbox(
                "担当利用者名 *",
                options=[""] + users,
                key=f"child_name_{tab_idx}",
                help="連絡帳を作成する児童を選択してください"
            )
            
            if child_name:  # 児童が選択されている場合のみフォームを表示
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### バイタル")
                        temperature = st.number_input(
                            "体温 *",
                            min_value=34.0,
                            max_value=42.0,
                            value=36.5,
                            step=0.1,
                            format="%.1f",
                            key=f"temperature_{tab_idx}"
                        )
                        vital_other = st.text_input(
                            "その他（血圧、脈拍、SPO2等）",
                            key=f"vital_other_{tab_idx}"
                        )
                        
                        mood = st.radio(
                            "気分・顔色",
                            options=["良", "普通", "悪"],
                            horizontal=True,
                            key=f"mood_{tab_idx}"
                        )
                    
                    with col2:
                        st.markdown("#### 食事・健康")
                        meal_status = st.radio(
                            "食事・おやつ",
                            options=["完食", "残食あり", "未摂取"],
                            key=f"meal_status_{tab_idx}"
                        )
                        meal_detail = st.text_input(
                            "メニュー内容",
                            key=f"meal_detail_{tab_idx}",
                            placeholder="例: カレーライス、おにぎり"
                        )
                        water_intake = st.number_input(
                            "水分補給量 (ml)",
                            min_value=0,
                            value=0,
                            key=f"water_{tab_idx}"
                        )
                        excretion = st.text_input(
                            "排泄記録",
                            key=f"excretion_{tab_idx}",
                            placeholder="例: 2回、便あり"
                        )
                    
                    st.markdown("#### 活動内容")
                    
                    # 学習内容（フォーム外）
                    learning_tags_list = st.session_state.data_manager.get_tags("learning")
                    learning_tags = st.multiselect(
                        "学習内容 *",
                        options=learning_tags_list,
                        key=f"learning_tags_{tab_idx}"
                    )
                    # 学習内容タグ追加・削除（フォーム外）
                    col_learn1, col_learn2 = st.columns([3, 1])
                    with col_learn1:
                        new_learning_tag = st.text_input(
                            "新しい学習内容タグを追加",
                            key=f"new_learning_tag_{tab_idx}",
                            placeholder="例: プログラミング学習"
                        )
                    with col_learn2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("追加", key=f"add_learning_tag_{tab_idx}", use_container_width=True):
                            if new_learning_tag and new_learning_tag.strip():
                                if st.session_state.data_manager.add_tag("learning", new_learning_tag):
                                    st.success(f"✅ '{new_learning_tag}' を追加しました")
                                    st.rerun()
                                else:
                                    st.error("既に登録されているか、追加に失敗しました")
                            else:
                                st.warning("タグ名を入力してください")
                    
                    # 学習内容タグ削除
                    if learning_tags_list:
                        with st.expander("🗑️ 学習内容タグを削除", expanded=False):
                            tags_to_delete_learn = st.multiselect(
                                "削除するタグを選択",
                                options=learning_tags_list,
                                key=f"delete_learning_tags_{tab_idx}"
                            )
                            if st.button("選択したタグを削除", key=f"confirm_delete_learning_{tab_idx}", type="secondary"):
                                if tags_to_delete_learn:
                                    deleted_count = 0
                                    for tag in tags_to_delete_learn:
                                        if st.session_state.data_manager.delete_tag("learning", tag):
                                            deleted_count += 1
                                    if deleted_count > 0:
                                        st.success(f"✅ {deleted_count}個のタグを削除しました")
                                        st.rerun()
                                else:
                                    st.warning("削除するタグを選択してください")
                    
                    # 学習内容の詳細（フォーム外）
                    learning_detail = st.text_area(
                        "学習内容の詳細",
                        height=80,
                        key=f"learning_detail_{tab_idx}",
                        placeholder="実施した内容の詳細を記入してください"
                    )
                    
                    # 自由遊び（フォーム外）
                    free_play_tags_list = st.session_state.data_manager.get_tags("free_play")
                    free_play_tags = st.multiselect(
                        "自由遊び *",
                        options=free_play_tags_list,
                        key=f"free_play_tags_{tab_idx}"
                    )
                    # 自由遊びタグ追加・削除（フォーム外）
                    col_free1, col_free2 = st.columns([3, 1])
                    with col_free1:
                        new_free_play_tag = st.text_input(
                            "新しい自由遊びタグを追加",
                            key=f"new_free_play_tag_{tab_idx}",
                            placeholder="例: レゴブロック"
                        )
                    with col_free2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("追加", key=f"add_free_play_tag_{tab_idx}", use_container_width=True):
                            if new_free_play_tag and new_free_play_tag.strip():
                                if st.session_state.data_manager.add_tag("free_play", new_free_play_tag):
                                    st.success(f"✅ '{new_free_play_tag}' を追加しました")
                                    st.rerun()
                                else:
                                    st.error("既に登録されているか、追加に失敗しました")
                            else:
                                st.warning("タグ名を入力してください")
                    
                    # 自由遊びタグ削除
                    if free_play_tags_list:
                        with st.expander("🗑️ 自由遊びタグを削除", expanded=False):
                            tags_to_delete_free = st.multiselect(
                                "削除するタグを選択",
                                options=free_play_tags_list,
                                key=f"delete_free_play_tags_{tab_idx}"
                            )
                            if st.button("選択したタグを削除", key=f"confirm_delete_free_{tab_idx}", type="secondary"):
                                if tags_to_delete_free:
                                    deleted_count = 0
                                    for tag in tags_to_delete_free:
                                        if st.session_state.data_manager.delete_tag("free_play", tag):
                                            deleted_count += 1
                                    if deleted_count > 0:
                                        st.success(f"✅ {deleted_count}個のタグを削除しました")
                                        st.rerun()
                                else:
                                    st.warning("削除するタグを選択してください")
                    
                    # 自由遊びの詳細（フォーム外）
                    free_play_detail = st.text_area(
                        "自由遊びの詳細",
                        height=80,
                        key=f"free_play_detail_{tab_idx}",
                        placeholder="実施した内容の詳細を記入してください"
                    )
                    
                    # 集団遊び（フォーム外）
                    group_play_tags_list = st.session_state.data_manager.get_tags("group_play")
                    group_play_tags = st.multiselect(
                        "集団遊び *",
                        options=group_play_tags_list,
                        key=f"group_play_tags_{tab_idx}"
                    )
                    # 集団遊びタグ追加・削除（フォーム外）
                    col_group1, col_group2 = st.columns([3, 1])
                    with col_group1:
                        new_group_play_tag = st.text_input(
                            "新しい集団遊びタグを追加",
                            key=f"new_group_play_tag_{tab_idx}",
                            placeholder="例: サッカー"
                        )
                    with col_group2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("追加", key=f"add_group_play_tag_{tab_idx}", use_container_width=True):
                            if new_group_play_tag and new_group_play_tag.strip():
                                if st.session_state.data_manager.add_tag("group_play", new_group_play_tag):
                                    st.success(f"✅ '{new_group_play_tag}' を追加しました")
                                    st.rerun()
                                else:
                                    st.error("既に登録されているか、追加に失敗しました")
                            else:
                                st.warning("タグ名を入力してください")
                    
                    # 集団遊びタグ削除
                    if group_play_tags_list:
                        with st.expander("🗑️ 集団遊びタグを削除", expanded=False):
                            tags_to_delete_group = st.multiselect(
                                "削除するタグを選択",
                                options=group_play_tags_list,
                                key=f"delete_group_play_tags_{tab_idx}"
                            )
                            if st.button("選択したタグを削除", key=f"confirm_delete_group_{tab_idx}", type="secondary"):
                                if tags_to_delete_group:
                                    deleted_count = 0
                                    for tag in tags_to_delete_group:
                                        if st.session_state.data_manager.delete_tag("group_play", tag):
                                            deleted_count += 1
                                    if deleted_count > 0:
                                        st.success(f"✅ {deleted_count}個のタグを削除しました")
                                        st.rerun()
                                else:
                                    st.warning("削除するタグを選択してください")
                    
                    # 集団遊びの詳細（フォーム外）
                    group_play_detail = st.text_area(
                        "集団遊びの詳細",
                        height=80,
                        key=f"group_play_detail_{tab_idx}",
                        placeholder="実施した内容の詳細を記入してください"
                    )
                    
                    # 特記事項（AIアシスト付き、フォーム外）
                    st.markdown("#### 特記事項 *")
                    render_ai_assistant(f"notes_{tab_idx}", child_name)
                    
                    # フォーム内の項目
                    with st.form(f"report_form_{tab_idx}", clear_on_submit=False):
                        
                        notes = st.text_area(
                            "特記事項",
                            height=150,
                            key=f"notes_{tab_idx}",
                            placeholder="保護者に伝えるべき詳細、変化、成長記録を記入してください",
                            help="AIアシスト機能を使用して文章を作成することもできます"
                        )
                        
                        # 送信ボタン
                        submitted = st.form_submit_button(
                            f"💾 保存（{child_name}）",
                            use_container_width=True,
                            type="primary"
                        )
                        
                        if submitted:
                            # バリデーション
                            errors = []
                            if not child_name:
                                errors.append("担当利用者名を選択してください")
                            if not learning_tags and not learning_detail:
                                errors.append("学習内容を入力してください")
                            if not free_play_tags and not free_play_detail:
                                errors.append("自由遊びを入力してください")
                            if not group_play_tags and not group_play_detail:
                                errors.append("集団遊びを入力してください")
                            if not notes:
                                errors.append("特記事項を入力してください")
                            
                            if errors:
                                for error in errors:
                                    st.error(error)
                            else:
                                # データをまとめる
                                report_data = {
                                    "業務日": st.session_state.work_date.isoformat(),
                                    "記入スタッフ名": st.session_state.staff_name,
                                    "始業時間": st.session_state.start_time.strftime("%H:%M"),
                                    "終業時間": st.session_state.end_time.strftime("%H:%M"),
                                    "担当利用者名": child_name,
                                    "体温": temperature,
                                    "バイタルその他": vital_other,
                                    "気分顔色": mood,
                                    "学習内容タグ": ", ".join(learning_tags),
                                    "学習内容詳細": learning_detail,
                                    "自由遊びタグ": ", ".join(free_play_tags),
                                    "自由遊び詳細": free_play_detail,
                                    "集団遊びタグ": ", ".join(group_play_tags),
                                    "集団遊び詳細": group_play_detail,
                                    "食事状態": meal_status,
                                    "食事詳細": meal_detail,
                                    "水分補給量": water_intake,
                                    "排泄記録": excretion,
                                    "特記事項": notes
                                }
                                
                                # 保存
                                if st.session_state.data_manager.save_daily_report(report_data):
                                    st.success(f"✅ {child_name}の日報を保存しました！")
                                    st.balloons()
                                    all_reports.append(report_data)
                                else:
                                    st.error("保存に失敗しました。")
            else:
                st.info("担当児童を選択すると、フォームが表示されます。")
    
    # 送迎業務記録
    st.markdown("---")
    st.markdown('<div class="section-header">🚗 送迎業務記録</div>', unsafe_allow_html=True)
    
    with st.expander("送迎業務を記録する", expanded=False):
        # 迎え（行き）- 3回分（フォーム外のチェックボックス）
        st.markdown("#### 🚗 迎え（行き）")
        
        pickup_enabled_list = []
        for i in range(1, 4):
            pickup_enabled = st.checkbox(f"迎え{i}回目を記録する", key=f"pickup_enabled_{i}")
            pickup_enabled_list.append(pickup_enabled)
            if i < 3:
                st.markdown("---")
        
        st.markdown("---")
        
        # 送り（帰り）（フォーム外のチェックボックス）
        st.markdown("#### 🚗 送り（帰り）")
        dropoff_enabled = st.checkbox("送りを記録する", key="dropoff_enabled")
        
        st.markdown("---")
        
        # フォーム内の項目
        with st.form("transport_form"):
            pickup_data_list = []
            for i in range(1, 4):
                pickup_enabled = pickup_enabled_list[i - 1]
                
                # チェックが入っている場合のみ表示
                if pickup_enabled:
                    st.markdown(f"**迎え{i}回目**")
                    pickup_vehicle = st.selectbox(
                        f"使用車両（迎え{i}回目）",
                        options=[""] + VEHICLE_OPTIONS,
                        key=f"pickup_vehicle_{i}"
                    )
                    pickup_children = st.multiselect(
                        f"迎えた児童名（迎え{i}回目）",
                        options=users,
                        max_selections=6,
                        key=f"pickup_children_{i}",
                        help="最大6名まで選択可能"
                    )
                    # 到着時刻（5分単位）
                    time_options = generate_time_options()
                    pickup_arrival_time = st.selectbox(
                        f"到着時刻（迎え{i}回目）",
                        options=[""] + time_options,
                        key=f"pickup_arrival_time_{i}",
                        help="5分単位で選択してください"
                    )
                    pickup_data_list.append({
                        "enabled": True,
                        "vehicle": pickup_vehicle,
                        "children": pickup_children,
                        "arrival_time": pickup_arrival_time,
                        "index": i
                    })
                    if i < 3:
                        st.markdown("---")
                else:
                    # チェックが外れている場合は空の値を設定
                    pickup_data_list.append({
                        "enabled": False,
                        "vehicle": "",
                        "children": [],
                        "arrival_time": "",
                        "index": i
                    })
            
            # 送り（帰り）のフォーム内項目
            if dropoff_enabled:
                st.markdown("**送り**")
                dropoff_vehicle = st.selectbox(
                    "使用車両（送り）",
                    options=[""] + VEHICLE_OPTIONS,
                    key="dropoff_vehicle"
                )
                dropoff_children = st.multiselect(
                    "送った児童名",
                    options=users,
                    max_selections=6,
                    key="dropoff_children",
                    help="最大6名まで選択可能"
                )
                # 退所時間（5分単位）
                time_options = generate_time_options()
                dropoff_departure_time = st.selectbox(
                    "退所時間（送り）",
                    options=[""] + time_options,
                    key="dropoff_departure_time",
                    help="5分単位で選択してください"
                )
            else:
                dropoff_vehicle = ""
                dropoff_children = []
                dropoff_departure_time = ""
            
            transport_submitted = st.form_submit_button("💾 送迎記録を保存", use_container_width=True)
            
            if transport_submitted:
                errors = []
                success_messages = []
                
                # 迎えのバリデーションと保存
                pickup_count = 0
                for pickup_data in pickup_data_list:
                    if pickup_data["enabled"]:
                        pickup_count += 1
                        if not pickup_data["vehicle"]:
                            errors.append(f"迎え{pickup_data['index']}回目の使用車両を選択してください")
                        if not pickup_data["children"]:
                            errors.append(f"迎え{pickup_data['index']}回目の児童名を選択してください")
                        elif len(pickup_data["children"]) > 6:
                            errors.append(f"迎え{pickup_data['index']}回目の児童は最大6名までです")
                
                # 送りのバリデーション
                if dropoff_enabled:
                    if not dropoff_vehicle:
                        errors.append("送りの使用車両を選択してください")
                    if not dropoff_children:
                        errors.append("送った児童名を選択してください")
                    elif len(dropoff_children) > 6:
                        errors.append("送りの児童は最大6名までです")
                
                if pickup_count == 0 and not dropoff_enabled:
                    errors.append("迎えまたは送りのいずれかを記録してください")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # 迎えの記録を保存（有効なもののみ）
                    for pickup_data in pickup_data_list:
                        if pickup_data["enabled"]:
                            pickup_record = {
                                "業務日": st.session_state.work_date.isoformat(),
                                "記入スタッフ名": st.session_state.staff_name,
                                "送迎区分": f"迎え（{pickup_data['index']}回目）",
                                "使用車両": pickup_data["vehicle"],
                                "送迎児童名": ", ".join(pickup_data["children"]),
                                "送迎人数": len(pickup_data["children"]),
                                "到着時刻": pickup_data.get("arrival_time", "")
                            }
                            st.session_state.data_manager.save_daily_report(pickup_record)
                            success_messages.append(f"迎え{pickup_data['index']}回目: {len(pickup_data['children'])}名")
                    
                    # 送りの記録を保存
                    if dropoff_enabled:
                        dropoff_data = {
                            "業務日": st.session_state.work_date.isoformat(),
                            "記入スタッフ名": st.session_state.staff_name,
                            "送迎区分": "送り",
                            "使用車両": dropoff_vehicle,
                            "送迎児童名": ", ".join(dropoff_children),
                            "送迎人数": len(dropoff_children),
                            "退所時間": dropoff_departure_time
                        }
                        st.session_state.data_manager.save_daily_report(dropoff_data)
                        success_messages.append(f"送り: {len(dropoff_children)}名")
                    
                    st.success(f"✅ 送迎記録を保存しました！ ({', '.join(success_messages)})")
                    st.balloons()
    
    # 業務報告・共有事項
    st.markdown("---")
    st.markdown('<div class="section-header">📢 業務報告・共有事項</div>', unsafe_allow_html=True)
    
    incident_toggle = st.toggle("ヒヤリハット・事故報告", key="incident_toggle")
    
    if incident_toggle:
        # 報告書タイプの選択
        report_type = st.radio(
            "報告書タイプ",
            ["事故報告書（PDF）", "ヒヤリハット報告書（PDF）"],
            key="report_type",
            horizontal=True,
            index=0
        )
        
        st.markdown("---")
        
        if report_type == "事故報告書（PDF）":
            st.markdown("#### 📋 事故報告詳細")
            
            # 基本情報
            col1, col2 = st.columns(2)
            with col1:
                incident_location = st.text_input(
                    "発生場所 *",
                    key="incident_location",
                    placeholder="例: プレイルーム、送迎車内"
                )
                incident_subject = st.selectbox(
                    "対象者 *",
                    options=[""] + st.session_state.data_manager.get_active_users(),
                    key="incident_subject"
                )
            
            with col2:
                incident_time_hour = st.number_input(
                    "発生時刻（時）",
                    min_value=0,
                    max_value=23,
                    value=datetime.now().hour,
                    key="incident_time_hour"
                )
                incident_time_min = st.number_input(
                    "発生時刻（分）",
                    min_value=0,
                    max_value=59,
                    value=datetime.now().minute,
                    key="incident_time_min"
                )
            
            # 詳細情報（AIアシストはフォーム外）
            render_accident_ai_assistant("incident_situation", "situation")
            render_accident_ai_assistant("incident_process", "process")
            render_accident_ai_assistant("incident_cause", "cause")
            render_accident_ai_assistant("incident_countermeasure", "countermeasure")
        else:
            # ヒヤリハット報告書用のAIアシスト（フォーム外）
            render_hiyari_ai_assistant("hiyari_context", "context")
            render_hiyari_ai_assistant("hiyari_details", "details")
            render_hiyari_ai_assistant("hiyari_countermeasure", "countermeasure")
    
    with st.form("report_form"):
        # フォーム内の入力フィールド（セッション状態から取得）
        form_incident_toggle = st.session_state.get("incident_toggle", False)
        form_report_type = st.session_state.get("report_type", "事故報告書（PDF）")
        
        if form_incident_toggle:
            if form_report_type == "事故報告書（PDF）":
                # 詳細情報（フォーム内）
                incident_situation = st.text_area(
                    "事故発生の状況 *",
                    height=100,
                    key="incident_situation",
                    placeholder="事故がどのように発生したか、具体的な状況を記入してください",
                    value=st.session_state.get("incident_situation", "")
                )
                
                incident_process = st.text_area(
                    "経過 *",
                    height=100,
                    key="incident_process",
                    placeholder="事故発生後の対応や経過を記入してください",
                    value=st.session_state.get("incident_process", "")
                )
                
                incident_cause = st.text_area(
                    "事故原因 *",
                    height=100,
                    key="incident_cause",
                    placeholder="事故の原因を分析して記入してください",
                    value=st.session_state.get("incident_cause", "")
                )
                
                incident_countermeasure = st.text_area(
                    "対策 *",
                    height=100,
                    key="incident_countermeasure",
                    placeholder="今後の対策や防止策を記入してください",
                    value=st.session_state.get("incident_countermeasure", "")
                )
                
                incident_others = st.text_area(
                    "その他",
                    height=80,
                    key="incident_others",
                    placeholder="その他の情報があれば記入してください"
                )
                
                # 簡易版の詳細（従来の形式）
                incident_detail = st.text_area(
                    "簡易詳細（従来形式）",
                    height=100,
                    key="incident_detail",
                    placeholder="発生状況、対応内容などを詳しく記入してください（PDF生成には上記の詳細項目を使用）"
                )
                
                # ヒヤリハット用の変数を空に設定
                hiyari_location = ""
                hiyari_context = ""
                hiyari_time_hour = datetime.now().hour
                hiyari_time_min = datetime.now().minute
                hiyari_details = ""
                selected_causes = []
                category_index = -1
                hiyari_countermeasure = ""
            else:
                # ヒヤリハット報告書用の入力フィールド（フォーム内）
                hiyari_context = st.text_area(
                    "どうしていた時 *",
                    height=80,
                    key="hiyari_context",
                    placeholder="例: 送迎車から降りる際、自由遊びの時間中",
                    value=st.session_state.get("hiyari_context", "")
                )
                
                hiyari_details = st.text_area(
                    "ヒヤリとした時のあらまし *",
                    height=120,
                    key="hiyari_details",
                    placeholder="ヒヤリとした時の具体的な状況を客観的に記述してください",
                    value=st.session_state.get("hiyari_details", "")
                )
                
                hiyari_countermeasure = st.text_area(
                    "教訓・対策 *",
                    height=120,
                    key="hiyari_countermeasure",
                    placeholder="具体的かつ実行可能なアクションプランを記入してください",
                    value=st.session_state.get("hiyari_countermeasure", "")
                )
                
                # 事故報告用の変数を空に設定
                incident_location = ""
                incident_subject = ""
                incident_time_hour = datetime.now().hour
                incident_time_min = datetime.now().minute
                incident_situation = ""
                incident_process = ""
                incident_cause = ""
                incident_countermeasure = ""
                incident_others = ""
                incident_detail = ""
        else:
            incident_detail = ""
            incident_location = ""
            incident_subject = ""
            incident_time_hour = datetime.now().hour
            incident_time_min = datetime.now().minute
            incident_situation = ""
            incident_process = ""
            incident_cause = ""
            incident_countermeasure = ""
            incident_others = ""
            report_type = ""
            hiyari_location = ""
            hiyari_context = ""
            hiyari_time_hour = datetime.now().hour
            hiyari_time_min = datetime.now().minute
            hiyari_details = ""
            selected_causes = []
            category_index = -1
            hiyari_countermeasure = ""
        
        handover = st.text_area(
            "申し送り事項",
            height=100,
            key="handover",
            placeholder="翌日以降のスタッフへの共有事項"
        )
        
        request = st.text_input(
            "備品購入・要望",
            key="request",
            placeholder="消耗品の補充依頼など"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            report_submitted = st.form_submit_button("💾 業務報告を保存", use_container_width=True)
        with col2:
            pdf_generate = st.form_submit_button("📄 PDF報告書を生成", use_container_width=True, type="secondary")
        
        if report_submitted:
            form_incident_toggle = st.session_state.get("incident_toggle", False)
            report_data = {
                "業務日": st.session_state.work_date.isoformat(),
                "記入スタッフ名": st.session_state.staff_name,
                "ヒヤリハット事故": "あり" if form_incident_toggle else "なし",
                "ヒヤリハット詳細": incident_detail if form_incident_toggle else "",
                "発生場所": incident_location if form_incident_toggle else "",
                "対象者": incident_subject if form_incident_toggle else "",
                "事故発生の状況": incident_situation if form_incident_toggle else "",
                "経過": incident_process if form_incident_toggle else "",
                "事故原因": incident_cause if form_incident_toggle else "",
                "対策": incident_countermeasure if form_incident_toggle else "",
                "その他": incident_others if form_incident_toggle else "",
                "申し送り事項": handover,
                "備品購入要望": request
            }
            
            if st.session_state.data_manager.save_daily_report(report_data):
                st.success("✅ 業務報告を保存しました！")
                st.balloons()
            else:
                st.error("保存に失敗しました。")
        
        if pdf_generate:
            form_incident_toggle = st.session_state.get("incident_toggle", False)
            form_report_type = st.session_state.get("report_type", "事故報告書（PDF）")
            
            if form_incident_toggle and form_report_type == "事故報告書（PDF）":
                # バリデーション
                errors = []
                if not incident_location:
                    errors.append("発生場所を入力してください")
                if not incident_subject:
                    errors.append("対象者を選択してください")
                if not incident_situation:
                    errors.append("事故発生の状況を入力してください")
                if not incident_process:
                    errors.append("経過を入力してください")
                if not incident_cause:
                    errors.append("事故原因を入力してください")
                if not incident_countermeasure:
                    errors.append("対策を入力してください")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        # 日付情報の準備
                        work_date = st.session_state.work_date
                        date_info = AccidentReportGenerator.format_date_for_report(work_date)
                        
                        # PDF生成用のデータを準備
                        pdf_data = {
                            "facility_name": "放課後等デイサービス",  # 必要に応じて設定可能にする
                            "date_year": date_info["date_year"],
                            "date_month": date_info["date_month"],
                            "date_day": date_info["date_day"],
                            "date_weekday": date_info["date_weekday"],
                            "time_hour": str(incident_time_hour).zfill(2),
                            "time_min": str(incident_time_min).zfill(2),
                            "location": incident_location,
                            "subject_name": incident_subject,
                            "situation": incident_situation,
                            "process": incident_process,
                            "cause": incident_cause,
                            "countermeasure": incident_countermeasure,
                            "others": incident_others,
                            "reporter_name": st.session_state.staff_name,
                            "record_date": work_date.strftime("%Y年%m月%d日"),
                            "record_date_year": date_info.get("record_date_year", date_info["date_year"]),
                            "record_date_month": date_info.get("record_date_month", date_info["date_month"]),
                            "record_date_day": date_info.get("record_date_day", date_info["date_day"])
                        }
                        
                        # 一時ファイルにPDFを生成
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            pdf_filename = tmp_file.name
                            generator = AccidentReportGenerator(pdf_filename)
                            generator.generate(pdf_data)
                            
                            # PDFファイルを読み込んでダウンロードボタンを表示
                            with open(pdf_filename, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                                st.download_button(
                                    label="📥 事故報告書PDFをダウンロード",
                                    data=pdf_bytes,
                                    file_name=f"事故報告書_{work_date.strftime('%Y%m%d')}_{incident_subject}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            
                            # 一時ファイルを削除
                            os.unlink(pdf_filename)
                            
                            st.success("✅ PDF報告書を生成しました！")
                            
                    except Exception as e:
                        st.error(f"PDF生成エラー: {str(e)}")
                        st.exception(e)
            
            elif form_incident_toggle and form_report_type == "ヒヤリハット報告書（PDF）":
                # バリデーション
                errors = []
                hiyari_location = st.session_state.get("hiyari_location", "")
                hiyari_time_hour = st.session_state.get("hiyari_time_hour", datetime.now().hour)
                hiyari_time_min = st.session_state.get("hiyari_time_min", datetime.now().minute)
                selected_causes = []
                for i in range(1, 13):
                    if st.session_state.get(f"cause_{i}", False):
                        selected_causes.append(i)
                category_options = [
                    "環境に問題があった",
                    "設備・機器等に問題があった",
                    "指導方法に問題があった",
                    "自分自身に問題があった"
                ]
                selected_category = st.session_state.get("hiyari_category", "")
                category_index = category_options.index(selected_category) if selected_category in category_options else -1
                
                if not hiyari_location:
                    errors.append("発生場所を入力してください")
                if not hiyari_context:
                    errors.append("どうしていた時を入力してください")
                if not hiyari_details:
                    errors.append("ヒヤリとした時のあらましを入力してください")
                if not selected_causes:
                    errors.append("原因チェックリストから1つ以上選択してください")
                if category_index == -1:
                    errors.append("分類を選択してください")
                if not hiyari_countermeasure:
                    errors.append("教訓・対策を入力してください")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        # 日時情報の準備
                        work_date = st.session_state.work_date
                        incident_datetime = datetime.combine(
                            work_date,
                            time(hiyari_time_hour, hiyari_time_min)
                        )
                        
                        # PDF生成用のデータを準備
                        pdf_data = {
                            "datetime": incident_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                            "location": hiyari_location,
                            "context": hiyari_context,
                            "details": hiyari_details,
                            "cause_indices": selected_causes,
                            "category_index": category_index,
                            "countermeasure": hiyari_countermeasure
                        }
                        
                        # 一時ファイルにPDFを生成
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            pdf_filename = tmp_file.name
                            generator = HiyariHattoGenerator(pdf_filename)
                            generator.generate_report(
                                pdf_data,
                                reporter_name=st.session_state.staff_name
                            )
                            
                            # PDFファイルを読み込んでダウンロードボタンを表示
                            with open(pdf_filename, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                                st.download_button(
                                    label="📥 ヒヤリハット報告書PDFをダウンロード",
                                    data=pdf_bytes,
                                    file_name=f"ヒヤリハット報告書_{work_date.strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            
                            # 一時ファイルを削除
                            os.unlink(pdf_filename)
                            
                            st.success("✅ ヒヤリハット報告書PDFを生成しました！")
                            
                    except Exception as e:
                        st.error(f"PDF生成エラー: {str(e)}")
                        st.exception(e)


def render_user_master():
    """利用者マスタ管理画面の描画"""
    st.markdown('<div class="main-header">👥 利用者マスタ管理</div>', unsafe_allow_html=True)
    
    dm = st.session_state.data_manager
    
    # 新規追加
    st.markdown('<div class="section-header">➕ 新規利用者追加</div>', unsafe_allow_html=True)
    with st.form("add_user_form"):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            new_user_name = st.text_input(
                "利用者名",
                key="new_user_name",
                placeholder="児童の名前を入力してください"
            )
        with col2:
            new_user_classification = st.selectbox(
                "利用者区分",
                options=["放課後等デイサービス", "児童発達支援"],
                key="new_user_classification",
                help="放課後等デイサービス（放デイ）または児童発達支援（児発）を選択してください"
            )
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            add_submitted = st.form_submit_button("追加", use_container_width=True)
        
        if add_submitted:
            if not new_user_name or not new_user_name.strip():
                st.error("利用者名を入力してください")
            else:
                if dm.add_user(new_user_name, new_user_classification):
                    st.success(f"✅ {new_user_name}（{new_user_classification}）を追加しました！")
                    st.rerun()
                else:
                    st.error("追加に失敗しました。既に登録されている可能性があります。")
    
    st.markdown("---")
    
    # 利用者一覧
    st.markdown('<div class="section-header">📋 利用者一覧</div>', unsafe_allow_html=True)
    
    users = dm.get_all_users()
    
    if not users:
        st.info("利用者が登録されていません。")
    else:
        # アクティブな利用者と無効化された利用者を分けて表示
        active_users = [u for u in users if u.get("active", True)]
        inactive_users = [u for u in users if not u.get("active", True)]
        
        if active_users:
            st.markdown("#### アクティブな利用者")
            df_active = pd.DataFrame([
                {
                    "ID": u["id"], 
                    "名前": u["name"], 
                    "区分": u.get("classification", "放課後等デイサービス"),
                    "登録日": u.get("created_at", "-")[:10] if u.get("created_at") else "-"
                }
                for u in active_users
            ])
            st.dataframe(df_active, use_container_width=True, hide_index=True)
            
            # 削除機能
            with st.expander("🗑️ 利用者を削除（無効化）"):
                users_to_delete = st.multiselect(
                    "削除する利用者を選択",
                    options=[u["name"] for u in active_users],
                    key="users_to_delete"
                )
                
                if st.button("選択した利用者を削除", type="secondary"):
                    if users_to_delete:
                        deleted_count = dm.delete_users(users_to_delete)
                        if deleted_count > 0:
                            st.success(f"✅ {deleted_count}名の利用者を削除しました")
                            st.rerun()
                    else:
                        st.warning("削除する利用者を選択してください")
        
        if inactive_users:
            st.markdown("#### 無効化された利用者")
            df_inactive = pd.DataFrame([
                {
                    "ID": u["id"], 
                    "名前": u["name"], 
                    "区分": u.get("classification", "放課後等デイサービス"),
                    "削除日": u.get("deleted_at", "-")[:10] if u.get("deleted_at") else "-"
                }
                for u in inactive_users
            ])
            st.dataframe(df_inactive, use_container_width=True, hide_index=True)
            
            # 復元機能
            with st.expander("♻️ 利用者を復元"):
                users_to_restore = st.multiselect(
                    "復元する利用者を選択",
                    options=[u["name"] for u in inactive_users],
                    key="users_to_restore"
                )
                
                if st.button("選択した利用者を復元", type="secondary"):
                    if users_to_restore:
                        restored_count = 0
                        for name in users_to_restore:
                            if dm.restore_user(name):
                                restored_count += 1
                        if restored_count > 0:
                            st.success(f"✅ {restored_count}名の利用者を復元しました")
                            st.rerun()
                    else:
                        st.warning("復元する利用者を選択してください")


def render_saved_reports_viewer():
    """保存済み日報閲覧画面の描画"""
    st.markdown('<div class="main-header">📚 保存済み日報閲覧</div>', unsafe_allow_html=True)
    
    dm = st.session_state.data_manager
    
    # 保存済み日報の一覧を取得
    saved_reports = dm.get_saved_reports()
    
    if not saved_reports:
        st.info("保存済みの日報がありません。")
        return
    
    st.markdown('<div class="section-header">📋 保存済み日報一覧</div>', unsafe_allow_html=True)
    
    # 日付でフィルタリング
    col1, col2 = st.columns(2)
    with col1:
        filter_start_date = st.date_input(
            "開始日",
            value=None,
            key="filter_start_date"
        )
    with col2:
        filter_end_date = st.date_input(
            "終了日",
            value=None,
            key="filter_end_date"
        )
    
    # フィルタリング処理
    filtered_reports = saved_reports
    if filter_start_date:
        filtered_reports = [
            r for r in filtered_reports
            if datetime.fromisoformat(r["created_at"]).date() >= filter_start_date
        ]
    if filter_end_date:
        filtered_reports = [
            r for r in filtered_reports
            if datetime.fromisoformat(r["created_at"]).date() <= filter_end_date
        ]
    
    if not filtered_reports:
        st.warning("該当する日報がありません。")
        return
    
    # 日報一覧を表示
    st.markdown(f"**{len(filtered_reports)}件の日報が見つかりました**")
    
    # 日報を選択
    report_options = {}
    for report in filtered_reports:
        # ファイル名から日付と利用者名を抽出
        filename = report["filename"]
        created_at = datetime.fromisoformat(report["created_at"])
        display_name = f"{created_at.strftime('%Y年%m月%d日 %H:%M')} - {filename}"
        report_options[display_name] = report
    
    selected_display = st.selectbox(
        "閲覧する日報を選択してください",
        options=list(report_options.keys()),
        key="selected_report"
    )
    
    if selected_display:
        selected_report = report_options[selected_display]
        
        st.markdown("---")
        st.markdown('<div class="section-header">📄 日報内容</div>', unsafe_allow_html=True)
        
        # Markdownファイルの内容を読み込んで表示
        md_content = dm.load_report_markdown(selected_report["filename"])
        
        if md_content:
            # Markdown形式で表示
            st.markdown(md_content)
            
            # ダウンロードボタン
            st.markdown("---")
            col1, col2 = st.columns([1, 1])
            with col1:
                st.download_button(
                    label="📥 Markdownファイルをダウンロード",
                    data=md_content,
                    file_name=selected_report["filename"],
                    mime="text/markdown",
                    use_container_width=True
                )
            with col2:
                if st.button("🗑️ この日報を削除", use_container_width=True, type="secondary"):
                    try:
                        import os
                        os.remove(selected_report["filepath"])
                        st.success("✅ 日報を削除しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除エラー: {str(e)}")
        else:
            st.error("日報ファイルの読み込みに失敗しました。")


def render_daily_users_calendar():
    """利用者記録カレンダー閲覧画面の描画"""
    st.markdown('<div class="main-header">📅 利用者記録閲覧</div>', unsafe_allow_html=True)
    
    dm = st.session_state.data_manager
    
    # 全期間の利用者記録を取得
    all_daily_users = dm.get_all_daily_users()
    
    if not all_daily_users:
        st.info("利用者記録が登録されていません。")
        return
    
    st.markdown('<div class="section-header">📅 カレンダー表示</div>', unsafe_allow_html=True)
    
    # 月選択
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_year = st.selectbox(
            "年",
            options=range(2020, 2030),
            index=date.today().year - 2020,
            key="calendar_year"
        )
    with col2:
        selected_month = st.selectbox(
            "月",
            options=range(1, 13),
            index=date.today().month - 1,
            key="calendar_month"
        )
    
    # カレンダーのヘッダー
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    
    # カレンダーグリッドを作成
    cal = calendar.monthcalendar(selected_year, selected_month)
    
    # カレンダーを表示
    st.markdown(f"### {selected_year}年{selected_month}月")
    
    # 曜日ヘッダーを表示
    header_cols = st.columns(7)
    for i, weekday in enumerate(weekdays):
        with header_cols[i]:
            st.markdown(f"**{weekday}**", unsafe_allow_html=True)
    
    # 週ごとに表示
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("")
                else:
                    current_date = date(selected_year, selected_month, day)
                    date_str = current_date.isoformat()
                    
                    # その日の利用者記録を取得
                    users = all_daily_users.get(date_str, [])
                    user_count = len(users)
                    
                    # 日付のスタイルを決定
                    is_today = current_date == date.today()
                    has_records = user_count > 0
                    
                    # カレンダーセルのスタイル
                    if is_today:
                        cell_style = "background-color: #FFE5B4; border: 2px solid #FF6B6B; border-radius: 5px; padding: 8px; min-height: 60px;"
                    elif has_records:
                        cell_style = "background-color: #E8F5E9; border: 1px solid #4ECDC4; border-radius: 5px; padding: 8px; min-height: 60px;"
                    else:
                        cell_style = "border: 1px solid #E0E0E0; border-radius: 5px; padding: 8px; min-height: 60px;"
                    
                    st.markdown(
                        f'<div style="{cell_style}">',
                        unsafe_allow_html=True
                    )
                    
                    # 日付を表示
                    if is_today:
                        st.markdown(f"**{day}**<br><small>(今日)</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{day}**", unsafe_allow_html=True)
                    
                    # 利用者数を表示
                    if has_records:
                        st.markdown(f"👥 {user_count}名", unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 日付を選択して詳細を表示
    st.markdown('<div class="section-header">📋 詳細表示</div>', unsafe_allow_html=True)
    
    # 記録がある日付のリストを作成
    recorded_dates = []
    for date_str in sorted(all_daily_users.keys(), reverse=True):
        try:
            date_obj = datetime.fromisoformat(date_str).date()
            if date_obj.year == selected_year and date_obj.month == selected_month:
                users = all_daily_users[date_str]
                if users:
                    recorded_dates.append((date_str, date_obj, users))
        except:
            continue
    
    if recorded_dates:
        # 日付選択
        date_options = {}
        for date_str, date_obj, users in recorded_dates:
            display_name = f"{date_obj.strftime('%Y年%m月%d日')} ({len(users)}名)"
            date_options[display_name] = (date_str, date_obj, users)
        
        selected_display = st.selectbox(
            "日付を選択して詳細を表示",
            options=list(date_options.keys()),
            key="selected_date_detail"
        )
        
        if selected_display:
            date_str, date_obj, users = date_options[selected_display]
            
            st.markdown("---")
            # 日本語の曜日名を取得
            weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
            weekday_name = weekday_names[date_obj.weekday()]
            st.markdown(f"### {date_obj.strftime('%Y年%m月%d日')} ({weekday_name})")
            
            if users:
                st.markdown(f"**利用者数: {len(users)}名**")
                st.markdown("")
                st.markdown("**利用者一覧:**")
                for idx, user_name in enumerate(users, 1):
                    st.markdown(f"{idx}. {user_name}")
            else:
                st.info("この日の利用者記録はありません。")
    else:
        st.info(f"{selected_year}年{selected_month}月には利用者記録がありません。")
    
    # 統計情報
    st.markdown("---")
    st.markdown('<div class="section-header">📊 統計情報</div>', unsafe_allow_html=True)
    
    # 選択した月の統計
    month_recorded_dates = [d for d in recorded_dates]
    if month_recorded_dates:
        total_users_all_days = sum(len(users) for _, _, users in month_recorded_days)
        avg_users_per_day = total_users_all_days / len(month_recorded_days) if month_recorded_days else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("記録日数", f"{len(month_recorded_days)}日")
        with col2:
            st.metric("総利用者数", f"{total_users_all_days}名")
        with col3:
            st.metric("1日平均利用者数", f"{avg_users_per_day:.1f}名")


def render_morning_meeting():
    """朝礼議事録画面の描画"""
    st.markdown('<div class="main-header">📝 朝礼議事録</div>', unsafe_allow_html=True)
    
    # タブで入力と閲覧を分ける
    tab1, tab2 = st.tabs(["📝 議事録入力", "📚 議事録閲覧"])
    
    with tab1:
        st.markdown('<div class="section-header">📝 朝礼議事録入力</div>', unsafe_allow_html=True)
        
        # 音声から議事録を生成する機能
        st.markdown("#### 🎤 音声から議事録を生成（Gemini 3 Flash Preview）")
        st.info("音声ファイルをアップロードすると、自動的に議事録を作成します。")
        
        # 補助情報入力欄
        with st.expander("📝 補助情報を入力（任意）", expanded=False):
            st.markdown("**名前や固有名詞などの補助情報を入力すると、音声認識の精度が向上します。**")
            st.markdown("例：")
            st.markdown("- 参加者の名前：田中太郎、佐藤花子")
            st.markdown("- 施設名：○○デイサービス")
            st.markdown("- その他の固有名詞：○○公園、○○小学校")
            
            context_info = st.text_area(
                "補助情報を入力してください",
                height=100,
                key="audio_context_info",
                placeholder="例：参加者：田中太郎、佐藤花子、鈴木一郎\n施設名：○○デイサービス\nその他：○○公園、○○小学校",
                help="音声内で使用される可能性のある名前や固有名詞を記載してください。改行で区切って複数入力できます。"
            )
        
        uploaded_audio = st.file_uploader(
            "音声ファイルをアップロード",
            type=['mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm'],
            key="audio_upload",
            help="対応形式: MP3, WAV, M4A, OGG, FLAC, WEBM"
        )
        
        if uploaded_audio is not None:
            # Gemini APIキーの確認
            # まず、ai_helperに既に設定されているかチェック
            gemini_api_key = None
            if hasattr(st.session_state.ai_helper, 'gemini_api_key'):
                key = st.session_state.ai_helper.gemini_api_key
                if isinstance(key, str) and key.strip():
                    gemini_api_key = key
            
            # なければ環境変数から取得
            if not gemini_api_key:
                gemini_api_key = os.getenv("GEMINI_API_KEY", None)
            
            # なければStreamlit Secretsから取得
            if not gemini_api_key and hasattr(st, 'secrets') and hasattr(st.secrets, 'get'):
                try:
                    gemini_api_key = st.secrets.get("GEMINI_API_KEY", None)
                except:
                    pass
            
            # なければdata_managerから取得
            if not gemini_api_key:
                gemini_api_key = st.session_state.data_manager.get_gemini_api_key()
            
            # AIHelperにGemini APIキーを設定
            if gemini_api_key:
                # APIキーをクリーンアップ（余分な空白や改行を削除）
                gemini_api_key = gemini_api_key.strip()
                # 複数のAPIキーが結合されている可能性があるため、最初の有効なキーのみを使用
                if ' ' in gemini_api_key:
                    # スペースで区切られている場合、最初の部分のみを使用
                    gemini_api_key = gemini_api_key.split()[0]
                
                # APIキーを設定し、genai.configure()を呼び出す
                st.session_state.ai_helper.gemini_api_key = gemini_api_key
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_api_key)
                except ImportError:
                    st.error("google-generativeaiパッケージがインストールされていません。requirements.txtからインストールしてください。")
            
            # 最終的にis_gemini_available()で確認
            if not st.session_state.ai_helper.is_gemini_available():
                st.warning("⚠️ Gemini APIキーが設定されていません。設定画面でAPIキーを設定してください。")
            else:
                
                if st.button("🎤 音声から議事録を生成", use_container_width=True, type="primary"):
                    with st.spinner("音声を解析中...（数分かかる場合があります）"):
                        # 一時ファイルに保存
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_audio.name)[1]) as tmp_file:
                            tmp_file.write(uploaded_audio.getvalue())
                            tmp_audio_path = tmp_file.name
                        
                        try:
                            # 補助情報を取得
                            context_info = st.session_state.get("audio_context_info", "")
                            
                            # 音声から議事録を生成（補助情報を含める）
                            success, result = st.session_state.ai_helper.generate_meeting_minutes_from_audio(
                                tmp_audio_path,
                                context_info=context_info if context_info else None
                            )
                            
                            if success and isinstance(result, dict):
                                # 生成された議事録をフォームに反映
                                st.session_state.meeting_agenda = result.get("議題・内容", "")
                                st.session_state.meeting_decisions = result.get("決定事項", "")
                                st.session_state.meeting_shared = result.get("共有事項", "")
                                st.session_state.meeting_notes = result.get("その他メモ", "")
                                
                                st.success("✅ 議事録を生成しました！以下の内容を確認・編集して保存してください。")
                                st.rerun()
                            else:
                                st.error(f"議事録の生成に失敗しました: {result}")
                        except Exception as e:
                            st.error(f"エラーが発生しました: {str(e)}")
                        finally:
                            # 一時ファイルを削除
                            if os.path.exists(tmp_audio_path):
                                os.unlink(tmp_audio_path)
        
        st.markdown("---")
        
        # セッションステートの初期化（フォーム外で行う）
        if "meeting_agenda" not in st.session_state:
            st.session_state.meeting_agenda = ""
        if "meeting_decisions" not in st.session_state:
            st.session_state.meeting_decisions = ""
        if "meeting_shared" not in st.session_state:
            st.session_state.meeting_shared = ""
        if "meeting_notes" not in st.session_state:
            st.session_state.meeting_notes = ""
        
        with st.form("morning_meeting_form"):
            meeting_date = st.date_input(
                "日付 *",
                value=date.today(),
                key="meeting_date"
            )
            
            st.markdown("#### 議題・内容")
            agenda = st.text_area(
                "議題・内容 *",
                height=150,
                key="meeting_agenda",
                placeholder="朝礼で話し合った内容を記入してください"
            )
            
            st.markdown("#### 決定事項")
            decisions = st.text_area(
                "決定事項",
                height=120,
                key="meeting_decisions",
                placeholder="決定した事項があれば記入してください"
            )
            
            st.markdown("#### 共有事項")
            shared_items = st.text_area(
                "共有事項",
                height=120,
                key="meeting_shared",
                placeholder="スタッフ間で共有すべき事項を記入してください"
            )
            
            st.markdown("#### その他メモ")
            notes = st.text_area(
                "その他メモ",
                height=100,
                key="meeting_notes",
                placeholder="その他のメモがあれば記入してください"
            )
            
            submitted = st.form_submit_button("💾 議事録を保存", use_container_width=True, type="primary")
            
            if submitted:
                errors = []
                if not agenda or not agenda.strip():
                    errors.append("議題・内容を入力してください")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    meeting_data = {
                        "日付": meeting_date.isoformat(),
                        "記入スタッフ名": st.session_state.staff_name,
                        "議題・内容": agenda,
                        "決定事項": decisions if decisions else "",
                        "共有事項": shared_items if shared_items else "",
                        "その他メモ": notes if notes else ""
                    }
                    
                    if st.session_state.data_manager.save_morning_meeting(meeting_data):
                        st.success("✅ 朝礼議事録を保存しました！")
                        st.balloons()
                        # セッション状態をクリア
                        if "meeting_agenda" in st.session_state:
                            del st.session_state.meeting_agenda
                        if "meeting_decisions" in st.session_state:
                            del st.session_state.meeting_decisions
                        if "meeting_shared" in st.session_state:
                            del st.session_state.meeting_shared
                        if "meeting_notes" in st.session_state:
                            del st.session_state.meeting_notes
                        st.rerun()
                    else:
                        st.error("保存に失敗しました。")
    
    with tab2:
        st.markdown('<div class="section-header">📚 朝礼議事録一覧</div>', unsafe_allow_html=True)
        
        dm = st.session_state.data_manager
        
        # メソッドの存在確認
        if not hasattr(dm, 'get_morning_meetings'):
            st.error("エラー: get_morning_meetings メソッドが見つかりません。DataManagerクラスを確認してください。")
            st.stop()
        
        # 日付でフィルタリング
        col1, col2 = st.columns(2)
        with col1:
            filter_start_date = st.date_input(
                "開始日",
                value=None,
                key="meeting_filter_start_date"
            )
        with col2:
            filter_end_date = st.date_input(
                "終了日",
                value=None,
                key="meeting_filter_end_date"
            )
        
        # フィルタリング処理
        start_date_str = filter_start_date.isoformat() if filter_start_date else None
        end_date_str = filter_end_date.isoformat() if filter_end_date else None
        
        try:
            meetings = dm.get_morning_meetings(start_date_str, end_date_str)
        except AttributeError as e:
            st.error(f"エラー: get_morning_meetings メソッドの呼び出しに失敗しました: {str(e)}")
            st.info("DataManagerクラスにget_morning_meetingsメソッドが存在するか確認してください。")
            st.stop()
        except Exception as e:
            st.error(f"エラー: 朝礼議事録の取得に失敗しました: {str(e)}")
            st.stop()
        
        if not meetings:
            st.info("朝礼議事録が登録されていません。")
        else:
            st.markdown(f"**{len(meetings)}件の議事録が見つかりました**")
            
            # 検索機能
            search_query = st.text_input(
                "🔍 検索（議題・内容、決定事項、共有事項、メモ、スタッフ名で検索）",
                key="meeting_search",
                placeholder="検索キーワードを入力..."
            )
            
            # 並び替えオプション
            sort_option = st.selectbox(
                "並び替え",
                options=["日付（新しい順）", "日付（古い順）", "スタッフ名", "作成日時（新しい順）"],
                key="meeting_sort",
                index=0
            )
            
            # 検索と並び替えを適用
            filtered_meetings = meetings
            if search_query:
                search_lower = search_query.lower()
                filtered_meetings = [
                    m for m in meetings
                    if search_lower in m.get("議題・内容", "").lower()
                    or search_lower in m.get("決定事項", "").lower()
                    or search_lower in m.get("共有事項", "").lower()
                    or search_lower in m.get("その他メモ", "").lower()
                    or search_lower in m.get("記入スタッフ名", "").lower()
                ]
            
            # 並び替え
            if sort_option == "日付（新しい順）":
                filtered_meetings.sort(key=lambda x: x.get("日付", ""), reverse=True)
            elif sort_option == "日付（古い順）":
                filtered_meetings.sort(key=lambda x: x.get("日付", ""))
            elif sort_option == "スタッフ名":
                filtered_meetings.sort(key=lambda x: x.get("記入スタッフ名", ""))
            elif sort_option == "作成日時（新しい順）":
                filtered_meetings.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            if search_query and not filtered_meetings:
                st.warning(f"「{search_query}」に一致する議事録が見つかりませんでした。")
            
            # 議事録を選択
            meeting_options = {}
            for meeting in filtered_meetings:
                meeting_date_str = meeting.get("日付", "")
                created_at = meeting.get("created_at", "")
                try:
                    if meeting_date_str:
                        date_obj = datetime.fromisoformat(meeting_date_str).date()
                        date_display = date_obj.strftime('%Y年%m月%d日')
                    else:
                        date_display = "日付不明"
                    
                    if created_at:
                        created_at_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        time_display = created_at_obj.strftime('%H:%M')
                    else:
                        time_display = ""
                    
                    display_name = f"{date_display} {time_display} - {meeting.get('記入スタッフ名', '不明')}"
                    meeting_options[display_name] = meeting
                except:
                    display_name = f"議事録 - {meeting.get('記入スタッフ名', '不明')}"
                    meeting_options[display_name] = meeting
            
            if meeting_options:
                selected_display = st.selectbox(
                    f"閲覧する議事録を選択してください（{len(meeting_options)}件）",
                    options=list(meeting_options.keys()),
                    key="selected_meeting"
                )
            else:
                selected_display = None
                st.info("表示する議事録がありません。")
            
            if selected_display and selected_display in meeting_options:
                selected_meeting = meeting_options[selected_display]
                
                st.markdown("---")
                st.markdown('<div class="section-header">📄 議事録内容</div>', unsafe_allow_html=True)
                
                # 議事録の内容を表示
                meeting_date_str = selected_meeting.get("日付", "")
                if meeting_date_str:
                    try:
                        date_obj = datetime.fromisoformat(meeting_date_str).date()
                        st.markdown(f"### {date_obj.strftime('%Y年%m月%d日')} の朝礼議事録")
                    except:
                        st.markdown(f"### 朝礼議事録")
                else:
                    st.markdown(f"### 朝礼議事録")
                
                st.markdown("---")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"**記入スタッフ**: {selected_meeting.get('記入スタッフ名', '不明')}")
                with col2:
                    created_at = selected_meeting.get("created_at", "")
                    if created_at:
                        try:
                            created_at_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            st.markdown(f"**作成日時**: {created_at_obj.strftime('%Y年%m月%d日 %H:%M:%S')}")
                        except:
                            st.markdown(f"**作成日時**: {created_at}")
                
                st.markdown("---")
                
                st.markdown("#### 議題・内容")
                st.markdown(selected_meeting.get("議題・内容", ""))
                
                if selected_meeting.get("決定事項"):
                    st.markdown("---")
                    st.markdown("#### 決定事項")
                    st.markdown(selected_meeting.get("決定事項", ""))
                
                if selected_meeting.get("共有事項"):
                    st.markdown("---")
                    st.markdown("#### 共有事項")
                    st.markdown(selected_meeting.get("共有事項", ""))
                
                if selected_meeting.get("その他メモ"):
                    st.markdown("---")
                    st.markdown("#### その他メモ")
                    st.markdown(selected_meeting.get("その他メモ", ""))
                
                st.markdown("---")
                
                # ダウンロード機能と削除機能
                col1, col2 = st.columns([1, 1])
                with col1:
                    # Markdown形式でダウンロード
                    md_content = dm.format_morning_meeting_as_markdown(selected_meeting)
                    meeting_date_str = selected_meeting.get("日付", "")
                    if meeting_date_str:
                        try:
                            date_obj = datetime.fromisoformat(meeting_date_str).date()
                            filename = f"朝礼議事録_{date_obj.strftime('%Y%m%d')}.md"
                        except:
                            filename = f"朝礼議事録_{datetime.now().strftime('%Y%m%d')}.md"
                    else:
                        filename = f"朝礼議事録_{datetime.now().strftime('%Y%m%d')}.md"
                    
                    st.download_button(
                        label="📥 Markdownファイルをダウンロード",
                        data=md_content,
                        file_name=filename,
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                with col2:
                    # 削除確認用のセッションステート
                    delete_key = f"delete_meeting_{selected_meeting.get('created_at', '')}"
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False
                    
                    if not st.session_state[delete_key]:
                        if st.button("🗑️ この議事録を削除", use_container_width=True, type="secondary"):
                            st.session_state[delete_key] = True
                            st.rerun()
                    else:
                        st.warning("⚠️ 本当に削除しますか？")
                        col_confirm1, col_confirm2 = st.columns([1, 1])
                        with col_confirm1:
                            if st.button("✅ 削除する", use_container_width=True, type="primary"):
                                meeting_id = selected_meeting.get("created_at")
                                if meeting_id and dm.delete_morning_meeting(meeting_id):
                                    st.success("✅ 議事録を削除しました")
                                    # セッションステートをクリア
                                    if delete_key in st.session_state:
                                        del st.session_state[delete_key]
                                    st.rerun()
                                else:
                                    st.error("削除に失敗しました")
                                    st.session_state[delete_key] = False
                        with col_confirm2:
                            if st.button("❌ キャンセル", use_container_width=True):
                                st.session_state[delete_key] = False
                                st.rerun()


def render_settings():
    """設定画面の描画"""
    st.markdown('<div class="main-header">⚙️ 設定</div>', unsafe_allow_html=True)
    
    # アカウント管理セクション
    if st.session_state.logged_in and st.session_state.logged_in_user:
        st.markdown('<div class="section-header">👤 アカウント管理</div>', unsafe_allow_html=True)
        
        st.markdown("#### パスワード変更")
        with st.form("change_password_form"):
            old_password = st.text_input(
                "現在のパスワード",
                type="password",
                key="old_password"
            )
            
            new_password = st.text_input(
                "新しいパスワード",
                type="password",
                key="new_password",
                help="4文字以上にしてください"
            )
            
            new_password_confirm = st.text_input(
                "新しいパスワード（確認）",
                type="password",
                key="new_password_confirm"
            )
            
            change_submitted = st.form_submit_button("パスワードを変更", use_container_width=True)
            
            if change_submitted:
                errors = []
                if not old_password:
                    errors.append("現在のパスワードを入力してください")
                if not new_password:
                    errors.append("新しいパスワードを入力してください")
                elif len(new_password) < 4:
                    errors.append("パスワードは4文字以上にしてください")
                elif new_password != new_password_confirm:
                    errors.append("新しいパスワードが一致しません")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    if st.session_state.data_manager.change_password(
                        st.session_state.logged_in_user["user_id"],
                        old_password,
                        new_password
                    ):
                        st.success("✅ パスワードを変更しました")
                        st.rerun()
                    else:
                        st.error("パスワードの変更に失敗しました。現在のパスワードが正しくない可能性があります。")
        
        st.markdown("---")
        
        # スタッフアカウント一覧（管理者向け）
        st.markdown("#### スタッフアカウント一覧")
        accounts = st.session_state.data_manager.get_all_staff_accounts()
        if accounts:
            df_accounts = pd.DataFrame([
                {
                    "ユーザーID": acc["user_id"],
                    "スタッフ名": acc["name"],
                    "登録日": acc.get("created_at", "-")[:10] if acc.get("created_at") else "-",
                    "状態": "アクティブ" if acc.get("active", True) else "無効"
                }
                for acc in accounts
            ])
            st.dataframe(df_accounts, use_container_width=True, hide_index=True)
        else:
            st.info("アカウントが登録されていません。")
        
        st.markdown("---")
    
    st.markdown('<div class="section-header">🔑 API設定</div>', unsafe_allow_html=True)
    
    # Grok APIキーの設定
    st.markdown("#### Grok API キー設定")
    st.info("AI文章生成機能を使用するには、Grok APIキーが必要です。")
    
    current_key = st.session_state.ai_helper.api_key or ""
    masked_key = "***" + current_key[-4:] if len(current_key) > 4 else ""
    
    if current_key:
        st.success(f"✅ APIキーが設定されています（末尾4桁: {masked_key}）")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🗑️ APIキーを削除", type="secondary", use_container_width=True):
                if st.session_state.data_manager.delete_api_key():
                    st.session_state.ai_helper = AIHelper(api_key=None)
                    st.success("✅ APIキーを削除しました")
                    st.rerun()
    else:
        st.warning("⚠️ APIキーが設定されていません")
    
    new_api_key = st.text_input(
        "新しいAPIキーを入力",
        type="password",
        key="new_api_key",
        placeholder="APIキーを入力してください",
        help="環境変数 GROK_API_KEY に設定することもできます"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 APIキーを保存", use_container_width=True):
            if new_api_key and new_api_key.strip():
                if st.session_state.data_manager.save_api_key(new_api_key.strip()):
                    st.session_state.ai_helper = AIHelper(api_key=new_api_key.strip())
                    st.success("✅ APIキーを保存しました")
                    st.rerun()
                else:
                    st.error("APIキーの保存に失敗しました")
            else:
                st.error("APIキーを入力してください")
    
    with col2:
        if st.button("🔄 APIキーを更新（一時的）", use_container_width=True):
            if new_api_key and new_api_key.strip():
                st.session_state.ai_helper = AIHelper(api_key=new_api_key.strip())
                st.success("✅ APIキーを更新しました（このセッションのみ有効）")
                st.info("💡 永続的に保存するには「APIキーを保存」ボタンを使用してください")
                st.rerun()
            else:
                st.error("APIキーを入力してください")
    
    st.markdown("---")
    
    # Gemini APIキーの設定
    st.markdown("#### Gemini API キー設定")
    st.info("音声から朝礼議事録を作成する機能を使用するには、Gemini APIキーが必要です。")
    
    current_gemini_key = ""
    if hasattr(st.session_state.ai_helper, 'gemini_api_key'):
        key = st.session_state.ai_helper.gemini_api_key
        current_gemini_key = key if isinstance(key, str) and key else ""
    masked_gemini_key = "***" + current_gemini_key[-4:] if isinstance(current_gemini_key, str) and len(current_gemini_key) > 4 else ""
    
    if current_gemini_key:
        st.success(f"✅ Gemini APIキーが設定されています（末尾4桁: {masked_gemini_key}）")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🗑️ Gemini APIキーを削除", type="secondary", use_container_width=True):
                if st.session_state.data_manager.delete_gemini_api_key():
                    st.session_state.ai_helper.gemini_api_key = None
                    st.success("✅ Gemini APIキーを削除しました")
                    st.rerun()
    else:
        st.warning("⚠️ Gemini APIキーが設定されていません")
    
    new_gemini_api_key = st.text_input(
        "新しいGemini APIキーを入力",
        type="password",
        key="new_gemini_api_key",
        placeholder="Gemini APIキーを入力してください",
        help="環境変数 GEMINI_API_KEY に設定することもできます"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 Gemini APIキーを保存", use_container_width=True):
            if new_gemini_api_key and new_gemini_api_key.strip():
                if st.session_state.data_manager.save_gemini_api_key(new_gemini_api_key.strip()):
                    st.session_state.ai_helper.gemini_api_key = new_gemini_api_key.strip()
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=new_gemini_api_key.strip())
                    except ImportError:
                        st.error("google-generativeaiパッケージがインストールされていません。")
                    st.success("✅ Gemini APIキーを保存しました")
                    st.rerun()
                else:
                    st.error("Gemini APIキーの保存に失敗しました")
            else:
                st.error("Gemini APIキーを入力してください")
    
    with col2:
        if st.button("🔄 Gemini APIキーを更新（一時的）", use_container_width=True):
            if new_gemini_api_key and new_gemini_api_key.strip():
                st.session_state.ai_helper.gemini_api_key = new_gemini_api_key.strip()
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=new_gemini_api_key.strip())
                    st.success("✅ Gemini APIキーを更新しました（このセッションのみ有効）")
                    st.info("💡 永続的に保存するには「Gemini APIキーを保存」ボタンを使用してください")
                    st.rerun()
                except ImportError:
                    st.error("google-generativeaiパッケージがインストールされていません。")
            else:
                st.error("Gemini APIキーを入力してください")
    
    st.markdown("---")
    
    # データエクスポート
    st.markdown('<div class="section-header">📊 データ管理</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 日報データのエクスポート")
        if st.button("CSV形式でダウンロード"):
            df = st.session_state.data_manager.get_reports()
            if not df.empty:
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 ダウンロード",
                    data=csv,
                    file_name=f"daily_reports_{date.today().isoformat()}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("エクスポートするデータがありません")
    
    with col2:
        st.markdown("#### データの確認")
        if st.button("日報データを表示"):
            df = st.session_state.data_manager.get_reports()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("データがありません")


def main():
    """メイン関数"""
    # セッション状態の初期化（初回のみ）
    if 'work_date' not in st.session_state:
        st.session_state.work_date = date.today()
    if 'staff_name' not in st.session_state:
        st.session_state.staff_name = ""
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time(9, 0)
    if 'end_time' not in st.session_state:
        st.session_state.end_time = time(17, 0)
    
    # ログイン状態をチェック
    if not st.session_state.logged_in:
        # ログインしていない場合はログインページを表示
        render_login_page()
        return
    
    # ログイン済みの場合は通常のアプリケーションを表示
    # サイドバーの描画（ウィジェットが自動的にセッション状態を更新）
    render_sidebar()
    
    # ページに応じたコンテンツを表示
    if st.session_state.current_page == "日報入力":
        render_daily_report_form()
    elif st.session_state.current_page == "保存済み日報閲覧":
        render_saved_reports_viewer()
    elif st.session_state.current_page == "利用者記録閲覧":
        render_daily_users_calendar()
    elif st.session_state.current_page == "利用者マスタ管理":
        render_user_master()
    elif st.session_state.current_page == "朝礼議事録":
        render_morning_meeting()
    elif st.session_state.current_page == "設定":
        render_settings()


if __name__ == "__main__":
    main()

