"""
放課後等デイサービス 業務管理フォーム（日報）
Streamlitアプリケーション
"""
import streamlit as st
import os
import json
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
    page_title="放課後等デイサービス 業務管理フォーム",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# HTMLタイトルと言語属性を設定
st.markdown("""
<script>
document.title = "放課後等デイサービス 業務管理フォーム";
document.documentElement.lang = "ja";
</script>
""", unsafe_allow_html=True)

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

# タイトル用のセッション状態の初期化
if 'accident_title' not in st.session_state:
    st.session_state.accident_title = ""
if 'hiyari_title' not in st.session_state:
    st.session_state.hiyari_title = ""

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
        
        # data_managerの初期化確認
        if 'data_manager' not in st.session_state:
            st.error("❌ データマネージャーが初期化されていません。ページを再読み込みしてください。")
            return
        
        # 接続状態の表示（デバッグ用）
        try:
            is_supabase_enabled = st.session_state.data_manager._is_supabase_enabled()
        except Exception as e:
            st.error(f"❌ データマネージャーの接続状態確認中にエラーが発生しました: {str(e)}")
            st.exception(e)
            is_supabase_enabled = False
        
        if is_supabase_enabled:
            st.info("🔗 Supabaseデータベースに接続しています")
            
            # 接続テストボタン
            if st.button("🔍 接続テスト", help="Supabaseへの接続をテストします"):
                try:
                    test_result = st.session_state.data_manager.supabase_manager.test_connection()
                    if test_result["connected"] and test_result["table_accessible"]:
                        st.success(f"✅ 接続成功！データベース内のアカウント数: {test_result['account_count']}")
                    elif not test_result["enabled"]:
                        st.info("""
                        ℹ️ **Supabaseが設定されていません**

                        現在、ローカルファイルストレージを使用しています。Supabaseを使用するには:

                        1. [Supabase](https://supabase.com/)でプロジェクトを作成
                        2. 環境変数 `SUPABASE_URL` と `SUPABASE_KEY` を設定
                        3. `supabase_schema.sql` をSQL Editorで実行

                        詳細: `SUPABASE_SETUP.md` を参照してください。
                        """)
                    else:
                        error_detail = test_result.get("error", "不明なエラー")
                        st.error(f"❌ 接続エラー: {error_detail}")
                        if "Row Level Security" in error_detail or "permission denied" in error_detail.lower():
                            st.warning("""
                            ⚠️ **Row Level Security (RLS) が有効になっている可能性があります**

                            **解決方法:**
                            1. Supabase Dashboard → SQL Editor を開く
                            2. 以下のSQLを実行してください:

                            ```sql
                            ALTER TABLE staff_accounts DISABLE ROW LEVEL SECURITY;
                            ```

                            または、`supabase_schema.sql` ファイルのRLS無効化コマンドを実行してください。
                            """)
                        elif "nodename nor servname provided" in error_detail or "Name resolution failure" in error_detail:
                            st.warning("""
                            ⚠️ **Supabase URLが無効です**

                            **考えられる原因:**
                            - SUPABASE_URLが正しく設定されていない
                            - Supabaseプロジェクトが存在しない

                            **解決方法:**
                            1. Supabaseプロジェクトを作成してください
                            2. Settings → API から正しいURLを取得してください
                            """)
                except Exception as e:
                    st.error(f"接続テスト中にエラーが発生しました: {str(e)}")
        else:
            st.info("📁 ローカルファイルストレージを使用しています")
        
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
                    try:
                        # data_managerの確認
                        if 'data_manager' not in st.session_state:
                            st.error("❌ データマネージャーが初期化されていません。ページを再読み込みしてください。")
                            return
                        
                        # Supabase接続状態を確認
                        try:
                            is_supabase_enabled = st.session_state.data_manager._is_supabase_enabled()
                        except Exception as e:
                            st.warning(f"⚠️ 接続状態の確認中にエラーが発生しました: {str(e)}")
                            is_supabase_enabled = False
                        
                        # ログイン試行
                        account = None
                        try:
                            account = st.session_state.data_manager.verify_login(user_id, password)
                        except Exception as login_error:
                            error_str = str(login_error)
                            st.error(f"❌ ログイン認証処理中にエラーが発生しました: {error_str}")
                            
                            # RLSエラーの場合、特別なメッセージを表示
                            if "Row Level Security" in error_str or "permission denied" in error_str.lower():
                                st.warning("""
                                ⚠️ **Row Level Security (RLS) エラーが検出されました**
                                
                                **解決方法:**
                                1. Supabase Dashboard → SQL Editor を開く
                                2. 以下のSQLを実行してください:
                                
                                ```sql
                                ALTER TABLE staff_accounts DISABLE ROW LEVEL SECURITY;
                                ```
                                
                                または、`supabase_schema.sql` ファイルのRLS無効化コマンドを実行してください。
                                """)
                            else:
                                st.exception(login_error)
                            return
                        
                        if account:
                            st.session_state.logged_in = True
                            st.session_state.logged_in_user = account
                            st.session_state.staff_name = account["name"]
                            st.success(f"✅ {account['name']}さん、ようこそ！")
                            st.rerun()
                        else:
                            # より詳細なエラーメッセージ
                            error_msg = "ユーザーIDまたはパスワードが正しくありません"
                            
                            # デバッグ情報を追加
                            debug_info = []
                            if is_supabase_enabled:
                                debug_info.append("🔗 Supabaseデータベースを使用しています")
                                try:
                                    # データベース内のアカウント数を確認
                                    test_result = st.session_state.data_manager.supabase_manager.test_connection()
                                    if test_result.get("connected"):
                                        debug_info.append(f"📊 データベース内のアカウント数: {test_result.get('account_count', 0)}")
                                except Exception as debug_error:
                                    debug_info.append(f"⚠️ デバッグ情報取得エラー: {str(debug_error)}")
                            else:
                                debug_info.append("📁 ローカルファイルストレージを使用しています")
                                try:
                                    # get_all_staff_accounts()を使用（パブリックメソッド）
                                    accounts = st.session_state.data_manager.get_all_staff_accounts()
                                    debug_info.append(f"📊 ローカルアカウント数: {len(accounts) if accounts else 0}")
                                    if accounts:
                                        user_ids = [acc.get("user_id", "N/A") for acc in accounts]
                                        debug_info.append(f"登録されているユーザーID: {', '.join(user_ids)}")
                                except Exception as debug_error:
                                    debug_info.append(f"⚠️ デバッグ情報取得エラー: {str(debug_error)}")
                            
                            error_msg += "\n\n" + "\n".join(debug_info)
                            
                            if is_supabase_enabled:
                                error_msg += "\n\n💡 ヒント:"
                                error_msg += "\n- Supabaseデータベースにアカウントが存在するか確認してください"
                                error_msg += "\n- 接続テストボタンでデータベース接続を確認できます"
                                error_msg += "\n- Row Level Security (RLS) が有効になっている場合は、無効化してください"
                            else:
                                error_msg += "\n\n💡 ヒント: ローカルファイルストレージを使用しています。アカウントが作成されているか確認してください。"
                            st.error(error_msg)
                    except Exception as e:
                        error_str = str(e)
                        st.error(f"❌ ログイン処理中に予期しないエラーが発生しました: {error_str}")
                        st.exception(e)
        
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
                        try:
                            is_supabase_enabled = st.session_state.data_manager._is_supabase_enabled()
                            if st.session_state.data_manager.create_staff_account(
                                new_user_id.strip(),
                                new_password,
                                new_staff_name.strip()
                            ):
                                st.success(f"✅ アカウント '{new_user_id}' を作成しました！ログインしてください。")
                                st.rerun()
                            else:
                                error_msg = "アカウント作成に失敗しました。"
                                if is_supabase_enabled:
                                    error_msg += "\n\n💡 ヒント: ユーザーIDが既に使用されているか、Supabaseデータベースへの接続に問題がある可能性があります。"
                                else:
                                    error_msg += "\n\n💡 ヒント: ユーザーIDが既に使用されている可能性があります。"
                                st.error(error_msg)
                        except Exception as e:
                            st.error(f"アカウント作成処理中にエラーが発生しました: {str(e)}")
                            st.exception(e)


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
            ["日報入力", "保存済み日報閲覧", "利用者記録閲覧", "日報コメント確認", "朝礼議事録", "利用者マスタ管理", "設定"],
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


def render_daily_comment_ai_assistant(text_area_key: str):
    """日報コメント用AI文章生成アシストUI"""
    st.markdown("#### 🤖 AI日報コメント生成アシスト")

    # ウィジェット作成前にクリア処理を実行
    if st.session_state.get(f"clear_inputs_{text_area_key}", False):
        st.session_state[f"activity_content_{text_area_key}"] = ""
        st.session_state[f"challenges_{text_area_key}"] = ""
        st.session_state[f"improvements_{text_area_key}"] = ""
        st.session_state[f"clear_inputs_{text_area_key}"] = False

    activity_content = st.text_area(
        "活動内容",
        height=80,
        key=f"activity_content_{text_area_key}",
        placeholder="例: 学習支援、自由遊びの見守り、集団遊びの補助",
        help="実施した活動内容を入力してください"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        challenges = st.text_area(
            "課題",
            height=80,
            key=f"challenges_{text_area_key}",
            placeholder="例: 集中力の維持、コミュニケーション",
            help="本日の課題を入力してください"
        )
    
    with col2:
        improvements = st.text_area(
            "改善点",
            height=80,
            key=f"improvements_{text_area_key}",
            placeholder="例: 声かけのタイミング、環境設定",
            help="今後の改善点を入力してください"
        )
    
    # 自動適用のチェックボックス
    auto_apply = st.checkbox(
        "生成と同時に自動適用する",
        value=st.session_state.get(f"auto_apply_{text_area_key}", True),
        key=f"auto_apply_checkbox_{text_area_key}",
        help="チェックを入れると、生成されたコメントが自動的に日報コメント欄に反映されます"
    )
    st.session_state[f"auto_apply_{text_area_key}"] = auto_apply

    generate_btn = st.button("✨ 日報コメント生成", key=f"generate_{text_area_key}", use_container_width=True)

    if generate_btn:
        # 入力値の検証
        if not activity_content and not challenges and not improvements:
            st.warning("⚠️ 活動内容、課題、改善点のいずれかを入力してください。")
        else:
            with st.spinner("AIが日報コメントを生成中..."):
                success, result = st.session_state.ai_helper.generate_daily_comment(
                    activity_content=activity_content,
                    challenges=challenges,
                    improvements=improvements
                )
                if success:
                    st.session_state[f"generated_text_{text_area_key}"] = result
                    # 自動適用が有効な場合、直接セッション状態に設定
                    if auto_apply:
                        st.session_state[text_area_key] = result
                        st.success("✅ 日報コメントを生成し、自動的に適用しました！")
                        # 入力フィールドをクリアするためのフラグを設定
                        st.session_state[f"clear_inputs_{text_area_key}"] = True
                        st.rerun()
                    else:
                        st.success("日報コメントを生成しました！")
                else:
                    st.error(result)

    # 生成された文章の表示と適用（自動適用が無効な場合のみ表示）
    if f"generated_text_{text_area_key}" in st.session_state and not auto_apply:
        st.markdown("**生成された日報コメント:**")
        st.text_area(
            "プレビュー",
            value=st.session_state[f"generated_text_{text_area_key}"],
            height=200,
            key=f"preview_{text_area_key}",
            disabled=True
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ このコメントを使用", key=f"apply_{text_area_key}"):
                # 日報コメント入力欄に値を設定
                st.session_state[text_area_key] = st.session_state[f"generated_text_{text_area_key}"]
                # 生成されたテキストをクリア
                del st.session_state[f"generated_text_{text_area_key}"]
                # 入力フィールドをクリアするためのフラグを設定
                st.session_state[f"clear_inputs_{text_area_key}"] = True
                st.rerun()
        with col2:
            if st.button("❌ キャンセル", key=f"cancel_{text_area_key}"):
                del st.session_state[f"generated_text_{text_area_key}"]
                st.rerun()


def render_accident_ai_assistant(text_area_key: str, report_type: str):
    """事故報告書用AI文章生成アシストUI"""
    type_names = {
        "situation": "事故発生の状況",
        "process": "経過",
        "cause": "事故原因",
        "countermeasure": "対策"
    }
    type_name = type_names.get(report_type, report_type)
    st.markdown(f"#### 🤖 AI文章作成アシスト（{type_name}）")
    
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
            
            # 利用者区分選択
            if child_name:
                # 選択された利用者の情報を取得
                user_info = st.session_state.data_manager.get_user_by_name(child_name)
                default_classification = user_info.get("classification", "放課後等デイサービス") if user_info else "放課後等デイサービス"
                
                # 区分の表示名を設定（放デイ/児発の略称付き）
                classification_options = {
                    "放課後等デイサービス": "放課後等デイサービス（放デイ）",
                    "児童発達支援": "児童発達支援（児発）"
                }
                
                # デフォルト値の表示名を取得
                default_display = classification_options.get(default_classification, "放課後等デイサービス（放デイ）")
                
                # 区分選択
                selected_classification_display = st.selectbox(
                    "利用者区分 *",
                    options=list(classification_options.values()),
                    index=list(classification_options.values()).index(default_display) if default_display in classification_options.values() else 0,
                    key=f"classification_{tab_idx}",
                    help="放課後等デイサービス（放デイ）または児童発達支援（児発）を選択してください"
                )
                
                # 表示名から実際の区分値を取得
                selected_classification = [k for k, v in classification_options.items() if v == selected_classification_display][0]
            else:
                selected_classification = None
            
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
                            if child_name and not selected_classification:
                                errors.append("利用者区分を選択してください")
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
                                    "利用者区分": selected_classification,
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

    # 保存先情報の表示
    is_supabase_enabled = st.session_state.data_manager._is_supabase_enabled()
    if is_supabase_enabled:
        st.info("💾 **保存先**: Supabaseデータベース（クラウド保存）")
    else:
        st.info("💾 **保存先**: ローカルファイル（CSV形式）")
    
    # 日報コメントセクション（フォーム外）
    st.markdown("#### 📝 日報コメント（職員の1日の振り返り）")
    
    # AIアシスト機能（フォーム外）
    render_daily_comment_ai_assistant("daily_comment")
    
    st.markdown("---")
    
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
            
            # 基本情報セクション
            st.markdown("##### 📍 基本情報")
            
            # 記入者名
            default_reporter = st.session_state.get("staff_name", "")
            incident_reporter = st.text_input(
                "記入者名 *",
                key="incident_reporter",
                placeholder="記入者名を入力してください",
                value=st.session_state.get("incident_reporter", default_reporter),
                help="事故報告書の記入者名を入力してください"
            )
            
            # 発生日時
            st.markdown("**発生日時 ***")
            
            # 現在の日付を取得してデフォルト値に設定
            now = datetime.now()
            
            # セッション状態から日付を取得、またはデフォルト値を使用
            default_date = st.session_state.get("incident_date", date(now.year, now.month, now.day))
            if isinstance(default_date, str):
                try:
                    default_date = datetime.strptime(default_date, "%Y-%m-%d").date()
                except:
                    default_date = date(now.year, now.month, now.day)
            elif not isinstance(default_date, date):
                default_date = date(now.year, now.month, now.day)
            
            # カレンダーで日付を選択
            col_date1, col_date2 = st.columns([2, 1])
            with col_date1:
                incident_date = st.date_input(
                    "発生日",
                    value=default_date,
                    min_value=date(2019, 1, 1),
                    max_value=date(2100, 12, 31),
                    key="incident_date",
                    help="カレンダーから発生日を選択してください"
                )
                # 年・月・日を個別にセッション状態に保存（後方互換性のため）
                # ウィジェットが自動的にセッション状態を管理するため、手動で保存する必要はない
                st.session_state["incident_year"] = incident_date.year
                st.session_state["incident_month"] = incident_date.month
                st.session_state["incident_day"] = incident_date.day
            
            with col_date2:
                # 曜日を自動計算して表示
                weekday_map = ["月", "火", "水", "木", "金", "土", "日"]
                weekday_name = weekday_map[incident_date.weekday()]
                st.markdown(f"<br><br><strong>（{weekday_name}曜日）</strong>", unsafe_allow_html=True)
            
            # 発生時刻
            col_time1, col_time2, col_time3 = st.columns(3)
            with col_time1:
                # セッション状態から午前/午後を取得（文字列の場合はインデックスに変換）
                am_pm_value = st.session_state.get("incident_am_pm", 1 if now.hour >= 12 else 0)
                if isinstance(am_pm_value, str):
                    # 文字列の場合はインデックスに変換
                    am_pm_index = 0 if am_pm_value == "午前" else 1
                else:
                    # 整数の場合はそのまま使用
                    am_pm_index = int(am_pm_value) if isinstance(am_pm_value, (int, float)) else (1 if now.hour >= 12 else 0)
                
                incident_am_pm = st.selectbox(
                    "午前/午後",
                    options=["午前", "午後"],
                    index=am_pm_index,
                    key="incident_am_pm",
                    help="発生時刻の午前/午後"
                )
            with col_time2:
                hour_max = 12 if incident_am_pm == "午後" else 11
                hour_min = 1 if incident_am_pm == "午後" else 0
                current_hour = now.hour % 12 if now.hour % 12 != 0 else 12
                incident_time_hour = st.number_input(
                    "時",
                    min_value=hour_min,
                    max_value=hour_max,
                    value=st.session_state.get("incident_time_hour", current_hour),
                    key="incident_time_hour",
                    help="発生時刻（時）"
                )
            with col_time3:
                incident_time_min = st.number_input(
                    "分",
                    min_value=0,
                    max_value=59,
                    value=st.session_state.get("incident_time_min", now.minute),
                    key="incident_time_min",
                    help="発生時刻（分）"
                )
            
            # 発生場所
            incident_location = st.text_input(
                "発生場所 *",
                key="incident_location",
                placeholder="例: プレイルーム、送迎車内",
                value=st.session_state.get("incident_location", ""),
                help="事故が発生した場所を入力してください"
            )
            
            # 対象者（事故報告書特有の項目）
            incident_subject = st.multiselect(
                "対象者 *（複数選択可）",
                options=st.session_state.data_manager.get_active_users(),
                key="incident_subject",
                default=st.session_state.get("incident_subject", []),
                help="対象となる児童を複数選択できます。PDF出力時は「、」で区切られます。"
            )
            
            st.markdown("---")
            
            # 詳細情報（AIアシストはフォーム外）
            st.markdown("##### ✍️ 詳細情報（AIアシスト機能）")
            render_accident_ai_assistant("incident_situation", "situation")
            render_accident_ai_assistant("incident_process", "process")
            render_accident_ai_assistant("incident_cause", "cause")
            render_accident_ai_assistant("incident_countermeasure", "countermeasure")
            
        else:
            # ヒヤリハット報告書セクション
            st.markdown("#### 📋 ヒヤリハット報告詳細")
            
            # 基本情報セクション
            st.markdown("##### 📍 基本情報")
            
            # 記入者名
            default_reporter = st.session_state.get("staff_name", "")
            hiyari_reporter = st.text_input(
                "記入者名 *",
                key="hiyari_reporter",
                placeholder="記入者名を入力してください",
                value=st.session_state.get("hiyari_reporter", default_reporter),
                help="ヒヤリハット報告書の記入者名を入力してください"
            )
            
            # 発生日時
            st.markdown("**発生日時 ***")
            
            # 現在の日付を取得してデフォルト値に設定
            now = datetime.now()
            
            # セッション状態から日付を取得、またはデフォルト値を使用
            default_date = st.session_state.get("hiyari_date", date(now.year, now.month, now.day))
            if isinstance(default_date, str):
                try:
                    default_date = datetime.strptime(default_date, "%Y-%m-%d").date()
                except:
                    default_date = date(now.year, now.month, now.day)
            elif not isinstance(default_date, date):
                default_date = date(now.year, now.month, now.day)
            
            # カレンダーで日付を選択
            col_date1, col_date2 = st.columns([2, 1])
            with col_date1:
                hiyari_date = st.date_input(
                    "発生日",
                    value=default_date,
                    min_value=date(2019, 1, 1),
                    max_value=date(2100, 12, 31),
                    key="hiyari_date",
                    help="カレンダーから発生日を選択してください"
                )
                # 年・月・日を個別にセッション状態に保存（後方互換性のため）
                # ウィジェットが自動的にセッション状態を管理するため、手動で保存する必要はない
                st.session_state["hiyari_year"] = hiyari_date.year
                st.session_state["hiyari_month"] = hiyari_date.month
                st.session_state["hiyari_day"] = hiyari_date.day
            
            with col_date2:
                # 曜日を自動計算して表示
                weekday_map = ["月", "火", "水", "木", "金", "土", "日"]
                weekday_name = weekday_map[hiyari_date.weekday()]
                st.markdown(f"<br><br><strong>（{weekday_name}曜日）</strong>", unsafe_allow_html=True)
            
            # 発生時刻
            col_time1, col_time2, col_time3 = st.columns(3)
            with col_time1:
                # セッション状態から午前/午後を取得（文字列の場合はインデックスに変換）
                am_pm_value = st.session_state.get("hiyari_am_pm", 1 if now.hour >= 12 else 0)
                if isinstance(am_pm_value, str):
                    # 文字列の場合はインデックスに変換
                    am_pm_index = 0 if am_pm_value == "午前" else 1
                else:
                    # 整数の場合はそのまま使用
                    am_pm_index = int(am_pm_value) if isinstance(am_pm_value, (int, float)) else (1 if now.hour >= 12 else 0)
                
                hiyari_am_pm = st.selectbox(
                    "午前/午後",
                    options=["午前", "午後"],
                    index=am_pm_index,
                    key="hiyari_am_pm",
                    help="発生時刻の午前/午後"
                )
            with col_time2:
                hour_max = 12 if hiyari_am_pm == "午後" else 11
                hour_min = 1 if hiyari_am_pm == "午後" else 0
                current_hour = now.hour % 12 if now.hour % 12 != 0 else 12
                hiyari_hour = st.number_input(
                    "時",
                    min_value=hour_min,
                    max_value=hour_max,
                    value=st.session_state.get("hiyari_hour", current_hour),
                    key="hiyari_hour",
                    help="発生時刻（時）"
                )
            with col_time3:
                hiyari_minute = st.number_input(
                    "分",
                    min_value=0,
                    max_value=59,
                    value=st.session_state.get("hiyari_minute", now.minute),
                    key="hiyari_minute",
                    help="発生時刻（分）"
                )
            
            # 発生場所
            hiyari_location = st.text_input(
                "発生場所 *",
                key="hiyari_location",
                placeholder="例: プレイルーム、送迎車内",
                value=st.session_state.get("hiyari_location", ""),
                help="ヒヤリハットが発生した場所を入力してください"
            )
            
            # 対象者
            hiyari_subject = st.multiselect(
                "対象者 *（複数選択可）",
                options=st.session_state.data_manager.get_active_users(),
                key="hiyari_subject",
                default=st.session_state.get("hiyari_subject", []),
                help="対象となる児童を複数選択できます。PDF出力時は「、」で区切られます。"
            )
            
            st.markdown("---")
            
            # 原因チェックリストセクション
            st.markdown("##### 🔍 原因チェックリスト *")
            st.caption("該当する項目を1つ以上選択してください")
            
            cause_items = {
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
            
            # 3列レイアウトでチェックボックスを配置（見やすくするため）
            col_cause1, col_cause2, col_cause3 = st.columns(3)
            with col_cause1:
                for i in range(1, 5):
                    st.checkbox(
                        f"{i}. {cause_items[i]}",
                        key=f"cause_{i}",
                        value=st.session_state.get(f"cause_{i}", False)
                    )
            with col_cause2:
                for i in range(5, 9):
                    st.checkbox(
                        f"{i}. {cause_items[i]}",
                        key=f"cause_{i}",
                        value=st.session_state.get(f"cause_{i}", False)
                    )
            with col_cause3:
                for i in range(9, 13):
                    st.checkbox(
                        f"{i}. {cause_items[i]}",
                        key=f"cause_{i}",
                        value=st.session_state.get(f"cause_{i}", False)
                    )
            
            st.markdown("---")
            
            # 原因の説明文セクション
            st.markdown("##### 📝 原因の説明 *")
            st.caption("各カテゴリーに該当する原因の説明文を記入してください")
            
            # 4つのカテゴリーそれぞれに説明文入力欄を追加
            hiyari_cause_environment = st.text_area(
                "環境に問題があった",
                key="hiyari_cause_environment",
                placeholder="例: 床が滑りやすかった、照明が暗かったなど",
                value=st.session_state.get("hiyari_cause_environment", ""),
                help="環境に関する問題の説明を記入してください",
                height=100
            )
            
            hiyari_cause_equipment = st.text_area(
                "設備・機器等に問題があった",
                key="hiyari_cause_equipment",
                placeholder="例: 遊具が壊れていた、機器の操作が複雑だったなど",
                value=st.session_state.get("hiyari_cause_equipment", ""),
                help="設備・機器に関する問題の説明を記入してください",
                height=100
            )
            
            hiyari_cause_guidance = st.text_area(
                "指導方法に問題があった",
                key="hiyari_cause_guidance",
                placeholder="例: 指示が不十分だった、声かけのタイミングが悪かったなど",
                value=st.session_state.get("hiyari_cause_guidance", ""),
                help="指導方法に関する問題の説明を記入してください",
                height=100
            )
            
            hiyari_cause_self = st.text_area(
                "自分自身に問題があった",
                key="hiyari_cause_self",
                placeholder="例: 注意力が散漫だった、体調不良だったなど",
                value=st.session_state.get("hiyari_cause_self", ""),
                help="自分自身に関する問題の説明を記入してください",
                height=100
            )
            
            st.markdown("---")
            
            # 分類セクション
            st.markdown("##### 📂 分類 *")
            st.caption("ヒヤリハットの原因となった分類を選択してください")
            
            category_options = [
                "環境に問題があった",
                "設備・機器等に問題があった",
                "指導方法に問題があった",
                "自分自身に問題があった"
            ]
            
            # ラジオボタンで選択（見やすくするため）
            hiyari_category = st.radio(
                "分類を選択してください",
                options=category_options,
                key="hiyari_category",
                index=category_options.index(st.session_state.get("hiyari_category", "")) if st.session_state.get("hiyari_category", "") in category_options else 0,
                help="ヒヤリハットの原因となった分類を1つ選択してください",
                horizontal=False
            )
            
            st.markdown("---")
            
            # 詳細情報（AIアシストはフォーム外）
            st.markdown("##### ✍️ 詳細情報（AIアシスト機能）")
            render_hiyari_ai_assistant("hiyari_context", "context")
            render_hiyari_ai_assistant("hiyari_details", "details")
            render_hiyari_ai_assistant("hiyari_countermeasure", "countermeasure")
    
    # フォームはここから開始（フォーム外のAIアシストの後）
    
    with st.form("report_form"):
        # フォーム内の入力フィールド（セッション状態から取得）
        form_incident_toggle = st.session_state.get("incident_toggle", False)
        form_report_type = st.session_state.get("report_type", "事故報告書（PDF）")
        
        if form_incident_toggle:
            if form_report_type == "事故報告書（PDF）":
                # タイトル入力フィールド（直接入力可能、報告内容と連携）
                st.markdown("#### 📝 タイトル生成")
                
                # キーワード入力欄
                title_keywords = st.text_area(
                    "キーワードや箇条書きを入力（タイトル生成用）",
                    height=60,
                    key="title_keywords",
                    placeholder="例: 転倒事故、プレイルーム、バランスボール、児童A",
                    help="タイトルを生成するためのキーワードや箇条書きを入力してください。複数のキーワードをカンマや改行で区切って入力できます。"
                )
                
                # タイトル入力と生成ボタン
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    accident_title_input = st.text_input(
                        "タイトル（「○○の件」形式で入力、または空欄で自動生成）",
                        value=st.session_state.get("accident_title", ""),
                        key="accident_title_input",
                        placeholder="例: 転倒事故に関する件",
                        help="タイトルを直接入力するか、キーワードから自動生成してください。「○○の件」形式で入力すると、報告内容の最初の行に自動的に反映されます。"
                    )
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    generate_title_from_keywords = st.form_submit_button("✨ キーワードから生成", key="generate_title_from_keywords", use_container_width=True, help="キーワードからタイトルを自動生成します")
                with col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    auto_generate_accident_title = st.form_submit_button("✨ 内容から生成", key="auto_generate_accident_title", use_container_width=True, help="入力済みの報告内容からタイトルを自動生成します")
                
                # キーワードからタイトル生成
                if generate_title_from_keywords:
                    if title_keywords and title_keywords.strip():
                        with st.spinner("キーワードからタイトルを生成中..."):
                            title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(title_keywords)
                            if title_success and generated_title:
                                # 生成結果をセッション状態に保存（プレビュー用）
                                st.session_state["generated_title_preview"] = generated_title
                                st.success(f"✅ タイトルを生成しました！")
                                st.rerun()
                            else:
                                st.error("❌ タイトルの生成に失敗しました。")
                    else:
                        st.warning("⚠️ キーワードを入力してから生成ボタンを押してください。")
                
                # 報告内容からタイトル自動生成ボタンが押された場合
                if auto_generate_accident_title:
                    report_content = st.session_state.get("report_content", "")
                    incident_situation = st.session_state.get("incident_situation", "")
                    if report_content and report_content.strip():
                        with st.spinner("タイトルを生成中..."):
                            # 報告内容からタイトルを抽出（既にタイトルが含まれている場合はそれを使用）
                            lines = report_content.split('\n')
                            if lines and lines[0].strip().endswith("の件"):
                                generated_title = lines[0].strip()
                                st.session_state["generated_title_preview"] = generated_title
                            else:
                                title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(report_content)
                                if title_success and generated_title:
                                    st.session_state["generated_title_preview"] = generated_title
                            st.rerun()
                    elif incident_situation and incident_situation.strip():
                        with st.spinner("タイトルを生成中..."):
                            title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(incident_situation)
                            if title_success and generated_title:
                                st.session_state["generated_title_preview"] = generated_title
                                st.rerun()
                    else:
                        st.warning("⚠️ 報告内容または事故発生の状況を入力してから自動生成ボタンを押してください。")
                
                # 生成結果のプレビュー表示
                if "generated_title_preview" in st.session_state and st.session_state["generated_title_preview"]:
                    st.markdown("---")
                    st.markdown("### ✨ 生成結果プレビュー")
                    st.info(f"**生成されたタイトル:**\n\n{st.session_state['generated_title_preview']}")
                    
                    col_apply, col_cancel = st.columns([1, 1])
                    with col_apply:
                        if st.form_submit_button("✅ このタイトルを使用", key="apply_generated_title", use_container_width=True):
                            st.session_state["accident_title"] = st.session_state["generated_title_preview"]
                            # プレビューをクリア
                            del st.session_state["generated_title_preview"]
                            st.rerun()
                    with col_cancel:
                        if st.form_submit_button("❌ キャンセル", key="cancel_generated_title", use_container_width=True):
                            # プレビューをクリア
                            del st.session_state["generated_title_preview"]
                            st.rerun()
                    st.markdown("---")
                
                # タイトルが変更された場合、報告内容の最初の行を更新
                if accident_title_input and accident_title_input.strip():
                    current_report_content = st.session_state.get("report_content", "")
                    if current_report_content:
                        lines = current_report_content.split('\n')
                        # 最初の行がタイトル形式の場合、更新
                        if lines and lines[0].strip().endswith("の件"):
                            # タイトルを更新
                            remaining_content = '\n'.join(lines[1:]).strip()
                            if remaining_content:
                                st.session_state["report_content"] = f"{accident_title_input.strip()}\n\n{remaining_content}"
                            else:
                                st.session_state["report_content"] = accident_title_input.strip()
                        else:
                            # タイトルがない場合、先頭に追加
                            st.session_state["report_content"] = f"{accident_title_input.strip()}\n\n{current_report_content}"
                
                # 事業者名（フォーム内）
                facility_name = st.text_input(
                    "事業者名 *",
                    key="facility_name",
                    value=st.session_state.get("facility_name", ""),
                    placeholder="例: 放課後等デイサービス"
                )
                
                
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
                    placeholder="その他の情報があれば記入してください",
                    value=st.session_state.get("incident_others", "")
                )
                
                # フォーム外で入力した基本情報を確認表示
                st.markdown("---")
                st.markdown("#### ✅ 入力確認（フォーム外で入力した値）")
                
                # 発生場所の確認
                incident_location_display = st.session_state.get("incident_location", "")
                if incident_location_display:
                    st.success(f"**✅ 発生場所:** {incident_location_display}")
                else:
                    st.error("❌ **発生場所を入力してください**（フォーム外の「基本情報」セクションで入力してください）")
                
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
                # タイトル入力フィールド（直接入力可能）
                st.markdown("#### 📝 タイトル（直接入力可能）")
                col1, col2 = st.columns([3, 1])
                with col1:
                    hiyari_title_input = st.text_input(
                        "タイトル（「○○の件」形式で入力、または空欄で自動生成）",
                        value=st.session_state.get("hiyari_title", ""),
                        key="hiyari_title_input",
                        placeholder="例: 送迎時の転倒リスクに関する件",
                        help="タイトルを直接入力してください。「○○の件」形式で入力すると自動的に適用されます。空欄の場合はヒヤリとした時のあらましから自動生成されます。"
                    )
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    auto_generate_hiyari_title = st.form_submit_button("✨ 自動生成", key="auto_generate_hiyari_title", use_container_width=True, help="ヒヤリとした時のあらましからタイトルを自動生成します")
                
                # タイトル自動生成ボタンが押された場合
                if auto_generate_hiyari_title:
                    hiyari_details = st.session_state.get("hiyari_details", "")
                    if hiyari_details and hiyari_details.strip():
                        with st.spinner("タイトルを生成中..."):
                            title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(hiyari_details)
                            if title_success and generated_title:
                                st.session_state.hiyari_title = generated_title
                                st.rerun()
                    else:
                        st.warning("⚠️ ヒヤリとした時のあらましを入力してから自動生成ボタンを押してください。")
                
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
        
        # 日報コメント入力（フォーム内）
        # セッション状態から値を確実に取得
        daily_comment_value = st.session_state.get("daily_comment", "")
        daily_comment = st.text_area(
            "日報コメント",
            height=150,
            key="daily_comment",
            placeholder="本日の活動内容、課題、改善点などを記入してください",
            help="AIアシスト機能を使用して文章を作成することもできます",
            value=daily_comment_value
        )
        # フォーム内で入力された値をセッション状態に保存（リアルタイム更新）
        if daily_comment != daily_comment_value:
            st.session_state["daily_comment"] = daily_comment
        
        st.markdown("---")
        
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
            daily_comment_value = st.session_state.get("daily_comment", "")
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
                "日報コメント": daily_comment_value,
                "申し送り事項": handover,
                "備品購入要望": request
            }

            try:
                success = st.session_state.data_manager.save_daily_report(report_data)
                if success:
                    # 保存先情報を含めた成功メッセージ
                    is_supabase_enabled = st.session_state.data_manager._is_supabase_enabled()
                    storage_type = "Supabaseデータベース" if is_supabase_enabled else "ローカルファイル"
                    st.success(f"✅ 業務報告を保存しました！（保存先: {storage_type}）")
                    st.balloons()
                else:
                    # Supabaseが有効かどうかでエラーメッセージを変更
                    is_supabase_enabled = st.session_state.data_manager._is_supabase_enabled()
                    if is_supabase_enabled:
                        st.error("""
                        ❌ **保存に失敗しました**

                        **原因**: Supabaseデータベースへの接続に問題が発生しています。

                        **対処方法**:
                        1. インターネット接続を確認してください
                        2. Supabaseサービスのステータスを確認してください
                        3. 環境変数（SUPABASE_URL, SUPABASE_KEY）が正しく設定されているか確認してください

                        ※ 一時的にローカル保存に切り替えることも可能です。
                        """)
                    else:
                        st.error("""
                        ❌ **保存に失敗しました**

                        **原因**: ローカルファイルへの保存に失敗しました。

                        **対処方法**:
                        1. ファイルシステムの権限を確認してください
                        2. ディスク容量が十分にあるか確認してください
                        3. dataディレクトリの書き込み権限を確認してください

                        ※ 開発者コンソールで詳細なエラーログを確認してください。
                        """)
            except Exception as e:
                st.error(f"""
                ❌ **保存中に予期しないエラーが発生しました**

                **エラー詳細**: {str(e)}

                **対処方法**:
                - このエラーメッセージを開発者に報告してください
                - ブラウザを更新して再度お試しください
                """)
                # エラーログを出力（デバッグ用）
                print(f"業務報告保存エラー: {e}")
                import traceback
                print(traceback.format_exc())
        
        if pdf_generate:
            form_incident_toggle = st.session_state.get("incident_toggle", False)
            form_report_type = st.session_state.get("report_type", "事故報告書（PDF）")
            
            if form_incident_toggle and form_report_type == "事故報告書（PDF）":
                # セッション状態から値を取得（フォーム外で入力した値を使用）
                incident_reporter = st.session_state.get("incident_reporter", "")
                incident_location = st.session_state.get("incident_location", "")
                incident_subject = st.session_state.get("incident_subject", [])
                
                # 発生日時の取得
                now = datetime.now()
                
                # カレンダーから選択した日付を取得（ウィジェットが自動的にセッション状態を管理）
                incident_date_selected = st.session_state.get("incident_date", date(now.year, now.month, now.day))
                if isinstance(incident_date_selected, str):
                    try:
                        incident_date_selected = datetime.strptime(incident_date_selected, "%Y-%m-%d").date()
                    except:
                        incident_date_selected = date(now.year, now.month, now.day)
                elif not isinstance(incident_date_selected, date):
                    incident_date_selected = date(now.year, now.month, now.day)
                
                incident_year = incident_date_selected.year
                incident_month = incident_date_selected.month
                incident_day = incident_date_selected.day
                incident_am_pm = st.session_state.get("incident_am_pm", "午前")
                incident_time_hour_input = st.session_state.get("incident_time_hour", now.hour % 12 if now.hour % 12 != 0 else 12)
                incident_time_min = st.session_state.get("incident_time_min", now.minute)
                
                # 午前/午後の処理（24時間形式に変換）
                if incident_am_pm == "午後":
                    if incident_time_hour_input < 12:
                        incident_time_hour = incident_time_hour_input + 12
                    else:
                        incident_time_hour = incident_time_hour_input
                else:  # 午前
                    if incident_time_hour_input == 12:
                        incident_time_hour = 0
                    else:
                        incident_time_hour = incident_time_hour_input
                
                # デバッグ情報（開発時のみ）
                if st.session_state.get("debug_mode", False):
                    st.info(f"**デバッグ情報:**\n- 発生場所: {incident_location}\n- 対象者: {incident_subject}\n- 原因チェックリスト: {[i for i in range(1, 13) if st.session_state.get(f'accident_cause_{i}', False)]}\n- 分類: {st.session_state.get('accident_category', '')}")
                
                # タイトルの処理（直接入力または自動生成）- 必ず「の件」形式を保証
                accident_title = ""
                accident_title_input = st.session_state.get("accident_title", "")
                # AI生成の報告内容を優先的に使用
                ai_generated_content = st.session_state.get("ai_generated_report_content", "")
                report_content = st.session_state.get("report_content", "")
                incident_situation = st.session_state.get("incident_situation", "")
                
                # タイトルが空欄でAI生成の報告内容がある場合、自動生成
                if not accident_title_input or not accident_title_input.strip():
                    if ai_generated_content and ai_generated_content.strip():
                        # AI生成の報告内容からタイトルを抽出または生成
                        lines = ai_generated_content.split('\n')
                        if lines and lines[0].strip().endswith("の件"):
                            # 既にタイトルが含まれている場合
                            accident_title_input = lines[0].strip()
                            st.session_state["accident_title"] = accident_title_input
                        else:
                            # タイトルを生成
                            title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(ai_generated_content)
                            if title_success and generated_title:
                                accident_title_input = generated_title
                                st.session_state["accident_title"] = accident_title_input
                
                if accident_title_input and accident_title_input.strip():
                    # 直接入力されたタイトルを使用（必ず「の件」形式に変換）
                    accident_title = st.session_state.ai_helper.ensure_title_format(accident_title_input.strip(), ai_generated_content if ai_generated_content else (report_content if report_content else incident_situation))
                elif ai_generated_content and ai_generated_content.strip():
                    # AI生成の報告内容から自動生成
                    title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(ai_generated_content)
                    if title_success and generated_title:
                        accident_title = generated_title
                    else:
                        accident_title = st.session_state.ai_helper.ensure_title_format("", ai_generated_content)
                elif report_content and report_content.strip():
                    # タイトルが入力されていない場合は、報告内容から自動生成
                    title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(report_content)
                    if title_success and generated_title:
                        accident_title = generated_title
                    else:
                        accident_title = st.session_state.ai_helper.ensure_title_format("", report_content)
                elif incident_situation and incident_situation.strip():
                    # 報告内容がない場合は、事故発生の状況から自動生成
                    title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(incident_situation)
                    if title_success and generated_title:
                        accident_title = generated_title
                    else:
                        accident_title = st.session_state.ai_helper.ensure_title_format("", incident_situation)
                else:
                    # フォールバック
                    accident_title = "事故報告の件"
                
                # 最終確認: 必ず「の件」で終わることを確認
                if not accident_title.endswith("の件"):
                    accident_title = accident_title + "の件"
                
                # バリデーション
                errors = []
                error_details = []
                
                # 基本情報のバリデーション
                if not incident_reporter:
                    errors.append("❌ **記入者名**を入力してください")
                    error_details.append("→ フォーム外の「📋 事故報告詳細」セクションの「📍 基本情報」で「記入者名 *」に入力してください")
                
                if not incident_location:
                    errors.append("❌ **発生場所**を入力してください")
                    error_details.append("→ フォーム外の「📋 事故報告詳細」セクションの「📍 基本情報」で「発生場所 *」に入力してください")
                
                if not incident_subject:
                    errors.append("❌ **対象者**を選択してください")
                    error_details.append("→ フォーム外の「📋 事故報告詳細」セクションの「📍 基本情報」で「対象者 *（複数選択可）」から選択してください")
                
                if not incident_situation:
                    errors.append("❌ **事故発生の状況**を入力してください")
                    error_details.append("→ フォーム内の「事故発生の状況 *」に入力するか、AIアシスト機能を使用してください")
                
                if not incident_process:
                    errors.append("❌ **経過**を入力してください")
                    error_details.append("→ フォーム内の「経過 *」に入力するか、AIアシスト機能を使用してください")
                
                if not incident_cause:
                    errors.append("❌ **事故原因**を入力してください")
                    error_details.append("→ フォーム内の「事故原因 *」に入力するか、AIアシスト機能を使用してください")
                
                if not incident_countermeasure:
                    errors.append("❌ **対策**を入力してください")
                    error_details.append("→ フォーム内の「対策 *」に入力するか、AIアシスト機能を使用してください")
                
                if errors:
                    st.error("### ⚠️ 入力エラーが発生しました")
                    for i, error in enumerate(errors):
                        st.error(error)
                        if i < len(error_details):
                            st.caption(error_details[i])
                    st.info("💡 **ヒント:** フォーム外の「📋 事故報告詳細」セクションで基本情報（発生場所、対象者、原因チェックリスト、分類）を入力し、フォーム内で詳細情報を入力してください。")
                else:
                    try:
                        # 日付情報の準備（カレンダーから選択した日付を使用）
                        try:
                            incident_date_obj = datetime.combine(incident_date_selected, time(incident_time_hour, incident_time_min))
                            date_info = AccidentReportGenerator.format_date_for_report(incident_date_selected)
                            incident_date = incident_date_obj
                        except (ValueError, AttributeError):
                            # 無効な日付の場合は現在の日付を使用
                            work_date = st.session_state.work_date
                            date_info = AccidentReportGenerator.format_date_for_report(work_date)
                            incident_date = datetime.combine(work_date, time(incident_time_hour, incident_time_min))
                        
                        # 曜日を計算
                        weekday_map = ["月", "火", "水", "木", "金", "土", "日"]
                        weekday_name = weekday_map[incident_date.weekday()]
                        
                        # セッション状態から事業者名と報告内容を取得
                        facility_name = st.session_state.get("facility_name", "放課後等デイサービス")
                        # AI生成の報告内容を使用（report_content_inputの値は使用しない）
                        report_content = st.session_state.get("ai_generated_report_content", "")
                        
                        # タイトルが入力されている場合、報告内容の先頭に追加
                        if accident_title and accident_title.strip():
                            title_text = accident_title.strip()
                            # 報告内容にタイトルが既に含まれていない場合のみ追加
                            if not report_content.startswith(title_text):
                                if report_content:
                                    report_content = f"{title_text}\n\n{report_content}"
                                else:
                                    report_content = title_text
                        
                        # 対象者名を文字列に変換（複数の場合は「、」で区切る）
                        if isinstance(incident_subject, list):
                            subject_name_str = "、".join(incident_subject) if incident_subject else ""
                        else:
                            subject_name_str = str(incident_subject) if incident_subject else ""
                        
                        # 記入者名を取得（デフォルトはスタッフ名）
                        reporter_name = incident_reporter if incident_reporter else st.session_state.get("staff_name", "")
                        
                        # PDF生成用のデータを準備
                        pdf_data = {
                            "facility_name": facility_name,
                            "report_content": report_content,
                            "date_year": str(incident_year),
                            "date_month": str(incident_month),
                            "date_day": str(incident_day),
                            "date_weekday": weekday_name,
                            "time_hour": str(incident_time_hour).zfill(2),
                            "time_min": str(incident_time_min).zfill(2),
                            "location": incident_location,
                            "subject_name": subject_name_str,
                            "situation": incident_situation,
                            "process": incident_process,
                            "cause": incident_cause,
                            "countermeasure": incident_countermeasure,
                            "others": incident_others,
                            "reporter_name": reporter_name,
                            "record_date": incident_date.strftime("%Y年%m月%d日"),
                            "record_date_year": str(incident_year),
                            "record_date_month": str(incident_month),
                            "record_date_day": str(incident_day)
                        }
                        
                        # ファイル名にタイトルを使用（タイトルから「の件」を除いて使用）
                        title_for_filename = accident_title.replace("の件", "") if accident_title.endswith("の件") else accident_title
                        safe_title = title_for_filename.replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
                        
                        # PDF生成用のデータをセッション状態に保存（フォーム外で処理）
                        st.session_state["pdf_generate_data"] = {
                            "type": "accident",
                            "pdf_data": pdf_data,
                            "title": accident_title,
                            "file_name": f"事故報告書_{incident_date.strftime('%Y%m%d')}_{safe_title}.pdf"
                        }
                        st.success("✅ PDF報告書を生成しました！")
                            
                    except Exception as e:
                        st.error(f"PDF生成エラー: {str(e)}")
                        st.exception(e)
            
            elif form_incident_toggle and form_report_type == "ヒヤリハット報告書（PDF）":
                # セッション状態から値を取得
                hiyari_location = st.session_state.get("hiyari_location", "")
                hiyari_context = st.session_state.get("hiyari_context", "")
                hiyari_details = st.session_state.get("hiyari_details", "")
                hiyari_countermeasure = st.session_state.get("hiyari_countermeasure", "")
                hiyari_time_hour = st.session_state.get("hiyari_time_hour", datetime.now().hour)
                hiyari_time_min = st.session_state.get("hiyari_time_min", datetime.now().minute)
                
                # タイトルの処理（直接入力または自動生成）- 必ず「の件」形式を保証
                hiyari_title = ""
                hiyari_title_input = st.session_state.get("hiyari_title", "")
                
                if hiyari_title_input and hiyari_title_input.strip():
                    # 直接入力されたタイトルを使用（必ず「の件」形式に変換）
                    hiyari_title = st.session_state.ai_helper.ensure_title_format(hiyari_title_input.strip(), hiyari_details if hiyari_details else "")
                elif hiyari_details and hiyari_details.strip():
                    # タイトルが入力されていない場合は、ヒヤリとした時のあらましから自動生成
                    title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(hiyari_details)
                    if title_success and generated_title:
                        hiyari_title = generated_title
                    else:
                        hiyari_title = st.session_state.ai_helper.ensure_title_format("", hiyari_details)
                else:
                    # フォールバック
                    hiyari_title = "ヒヤリハット報告の件"
                
                # 最終確認: 必ず「の件」で終わることを確認
                if not hiyari_title.endswith("の件"):
                    hiyari_title = hiyari_title + "の件"
                # 原因チェックリストの選択状況を確認
                selected_causes = []
                for i in range(1, 13):
                    if st.session_state.get(f"cause_{i}", False):
                        selected_causes.append(i)
                
                # 分類の選択状況を確認
                category_options = [
                    "環境に問題があった",
                    "設備・機器等に問題があった",
                    "指導方法に問題があった",
                    "自分自身に問題があった"
                ]
                selected_category = st.session_state.get("hiyari_category", "")
                category_index = category_options.index(selected_category) if selected_category in category_options else -1
                
                # バリデーション
                errors = []
                error_details = []
                
                # 基本情報の取得
                hiyari_reporter = st.session_state.get("hiyari_reporter", "")
                hiyari_location = st.session_state.get("hiyari_location", "")
                hiyari_subject = st.session_state.get("hiyari_subject", [])
                
                # 基本情報のバリデーション
                if not hiyari_reporter:
                    errors.append("❌ **記入者名**を入力してください")
                    error_details.append("→ フォーム外の「📋 ヒヤリハット報告詳細」セクションの「📍 基本情報」で「記入者名 *」に入力してください")
                
                if not hiyari_location:
                    errors.append("❌ **発生場所**を入力してください")
                    error_details.append("→ フォーム外の「📋 ヒヤリハット報告詳細」セクションの「📍 基本情報」で「発生場所 *」に入力してください")
                
                if not hiyari_subject:
                    errors.append("❌ **対象者**を選択してください")
                    error_details.append("→ フォーム外の「📋 ヒヤリハット報告詳細」セクションの「📍 基本情報」で「対象者 *（複数選択可）」から選択してください")
                
                if not hiyari_context:
                    errors.append("❌ **どうしていた時**を入力してください")
                    error_details.append("→ フォーム内の「どうしていた時 *」に入力するか、AIアシスト機能を使用してください")
                
                if not hiyari_details:
                    errors.append("❌ **ヒヤリとした時のあらまし**を入力してください")
                    error_details.append("→ フォーム内の「ヒヤリとした時のあらまし *」に入力するか、AIアシスト機能を使用してください")
                
                if not selected_causes:
                    errors.append("❌ **原因チェックリスト**から1つ以上選択してください")
                    error_details.append("→ フォーム外の「📋 ヒヤリハット報告詳細」セクションの「🔍 原因チェックリスト *」から該当する項目を選択してください")
                
                if category_index == -1:
                    errors.append("❌ **分類**を選択してください")
                    error_details.append("→ フォーム外の「📋 ヒヤリハット報告詳細」セクションの「📂 分類 *」から選択してください")
                
                # 選択された分類に対応する原因の説明文が入力されているか確認
                hiyari_cause_environment = st.session_state.get("hiyari_cause_environment", "")
                hiyari_cause_equipment = st.session_state.get("hiyari_cause_equipment", "")
                hiyari_cause_guidance = st.session_state.get("hiyari_cause_guidance", "")
                hiyari_cause_self = st.session_state.get("hiyari_cause_self", "")
                
                cause_descriptions = {
                    0: ("環境に問題があった", hiyari_cause_environment),
                    1: ("設備・機器等に問題があった", hiyari_cause_equipment),
                    2: ("指導方法に問題があった", hiyari_cause_guidance),
                    3: ("自分自身に問題があった", hiyari_cause_self)
                }
                
                if category_index != -1:
                    category_name, cause_description = cause_descriptions[category_index]
                    if not cause_description or not cause_description.strip():
                        errors.append(f"❌ **{category_name}**の説明文を入力してください")
                        error_details.append(f"→ フォーム外の「📋 ヒヤリハット報告詳細」セクションの「📝 原因の説明 *」で「{category_name}」の説明文を入力してください")
                
                if not hiyari_countermeasure:
                    errors.append("❌ **教訓・対策**を入力してください")
                    error_details.append("→ フォーム内の「教訓・対策 *」に入力するか、AIアシスト機能を使用してください")
                
                if errors:
                    st.error("### ⚠️ 入力エラーが発生しました")
                    for i, error in enumerate(errors):
                        st.error(error)
                        if i < len(error_details):
                            st.caption(error_details[i])
                    st.info("💡 **ヒント:** フォーム外の「📋 ヒヤリハット報告詳細」セクションで基本情報（発生場所、原因チェックリスト、分類）を入力し、フォーム内で詳細情報を入力してください。")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        # 日時情報の準備（新しく追加した基本情報から取得）
                        # カレンダーから選択した日付を取得
                        now = datetime.now()
                        hiyari_date_selected = st.session_state.get("hiyari_date", date(now.year, now.month, now.day))
                        if isinstance(hiyari_date_selected, str):
                            try:
                                hiyari_date_selected = datetime.strptime(hiyari_date_selected, "%Y-%m-%d").date()
                            except:
                                hiyari_date_selected = date(now.year, now.month, now.day)
                        elif not isinstance(hiyari_date_selected, date):
                            hiyari_date_selected = date(now.year, now.month, now.day)
                        
                        hiyari_year = hiyari_date_selected.year
                        hiyari_month = hiyari_date_selected.month
                        hiyari_day = hiyari_date_selected.day
                        hiyari_am_pm = st.session_state.get("hiyari_am_pm", "午前")
                        hiyari_hour = st.session_state.get("hiyari_hour", 9)
                        hiyari_minute = st.session_state.get("hiyari_minute", 0)
                        
                        # 午前/午後の処理
                        if hiyari_am_pm == "午後":
                            if hiyari_hour < 12:
                                hour_24 = hiyari_hour + 12
                            else:
                                hour_24 = hiyari_hour
                        else:  # 午前
                            if hiyari_hour == 12:
                                hour_24 = 0
                            else:
                                hour_24 = hiyari_hour
                        
                        # datetimeオブジェクトを作成
                        try:
                            incident_datetime = datetime(hiyari_year, hiyari_month, hiyari_day, hour_24, hiyari_minute)
                        except ValueError:
                            # 無効な日付の場合は現在の日時を使用
                            incident_datetime = datetime.now()
                        
                        # 対象者名を文字列に変換（複数の場合は「、」で区切る）
                        if isinstance(hiyari_subject, list):
                            subject_name_str = "、".join(hiyari_subject) if hiyari_subject else ""
                        else:
                            subject_name_str = str(hiyari_subject) if hiyari_subject else ""
                        
                        # PDF生成用のデータを準備
                        pdf_data = {
                            "datetime": incident_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                            "location": hiyari_location,
                            "subject_name": subject_name_str,
                            "context": hiyari_context,
                            "details": hiyari_details,
                            "cause_indices": selected_causes,
                            "category_index": category_index,
                            "cause_environment": hiyari_cause_environment,
                            "cause_equipment": hiyari_cause_equipment,
                            "cause_guidance": hiyari_cause_guidance,
                            "cause_self": hiyari_cause_self,
                            "countermeasure": hiyari_countermeasure
                        }
                        
                        # ファイル名にタイトルを使用（タイトルから「の件」を除いて使用）
                        title_for_filename = hiyari_title.replace("の件", "") if hiyari_title.endswith("の件") else hiyari_title
                        safe_title = title_for_filename.replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
                        
                        # 記入者名を取得
                        hiyari_reporter = st.session_state.get("hiyari_reporter", st.session_state.get("staff_name", ""))
                        
                        # PDF生成用のデータをセッション状態に保存（フォーム外で処理）
                        st.session_state["pdf_generate_data"] = {
                            "type": "hiyari",
                            "pdf_data": pdf_data,
                            "reporter_name": hiyari_reporter,
                            "title": hiyari_title,
                            "file_name": f"ヒヤリハット報告書_{incident_datetime.strftime('%Y%m%d')}_{safe_title}.pdf"
                        }
                        st.success("✅ ヒヤリハット報告書PDFを生成しました！")
                            
                    except Exception as e:
                        st.error(f"PDF生成エラー: {str(e)}")
                        st.exception(e)
    
    # フォーム外でPDFダウンロードボタンを表示
    if "pdf_generate_data" in st.session_state:
        pdf_gen_data = st.session_state["pdf_generate_data"]
        try:
            if pdf_gen_data["type"] == "accident":
                # 事故報告書PDFを生成
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf_filename = tmp_file.name
                    generator = AccidentReportGenerator(pdf_filename)
                    generator.generate(pdf_gen_data["pdf_data"])
                    
                    # PDFファイルを読み込んでダウンロードボタンを表示
                    with open(pdf_filename, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        st.download_button(
                            label="📥 事故報告書PDFをダウンロード",
                            data=pdf_bytes,
                            file_name=pdf_gen_data["file_name"],
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_accident_pdf"
                        )
                    
                    # 一時ファイルを削除
                    os.unlink(pdf_filename)
                    
            elif pdf_gen_data["type"] == "hiyari":
                # ヒヤリハット報告書PDFを生成
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf_filename = tmp_file.name
                    generator = HiyariHattoGenerator(pdf_filename)
                    generator.generate_report(
                        pdf_gen_data["pdf_data"],
                        reporter_name=pdf_gen_data["reporter_name"]
                    )
                    
                    # PDFファイルを読み込んでダウンロードボタンを表示
                    with open(pdf_filename, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        st.download_button(
                            label="📥 ヒヤリハット報告書PDFをダウンロード",
                            data=pdf_bytes,
                            file_name=pdf_gen_data["file_name"],
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_hiyari_pdf"
                        )
                    
                    # 一時ファイルを削除
                    os.unlink(pdf_filename)
            
            # セッション状態からPDF生成データを削除（次回の表示を防ぐ）
            del st.session_state["pdf_generate_data"]
            
        except Exception as e:
            st.error(f"PDF生成エラー: {str(e)}")
            st.exception(e)
            # エラー時もセッション状態をクリア
            if "pdf_generate_data" in st.session_state:
                del st.session_state["pdf_generate_data"]


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
            
            # ソート機能
            with st.expander("🔄 利用者の順番を並び替え"):
                st.info("利用者マスタの表示順を変更できます。上下ボタンで順番を変更してください。")
                
                # セッション状態で順番を管理
                if "user_sort_order" not in st.session_state:
                    st.session_state.user_sort_order = [u["id"] for u in active_users]
                
                # 現在の順番を表示し、上下ボタンを配置
                st.markdown("**現在の順番：**")
                current_order = st.session_state.user_sort_order
                
                # 順番に基づいて利用者を並び替え
                sorted_users_by_order = []
                id_to_user = {u["id"]: u for u in active_users}
                for user_id in current_order:
                    if user_id in id_to_user:
                        sorted_users_by_order.append(id_to_user[user_id])
                
                # 各利用者に上下ボタンを配置
                for idx, user in enumerate(sorted_users_by_order):
                    col1, col2, col3 = st.columns([1, 8, 1])
                    with col1:
                        move_up = st.button("↑", key=f"move_up_{user['id']}", disabled=(idx == 0))
                    with col2:
                        st.text(f"{idx + 1}. {user['name']} ({user.get('classification', '放課後等デイサービス')})")
                    with col3:
                        move_down = st.button("↓", key=f"move_down_{user['id']}", disabled=(idx == len(sorted_users_by_order) - 1))
                    
                    # 上に移動
                    if move_up and idx > 0:
                        current_order[idx], current_order[idx - 1] = current_order[idx - 1], current_order[idx]
                        st.session_state.user_sort_order = current_order
                        st.rerun()
                    
                    # 下に移動
                    if move_down and idx < len(sorted_users_by_order) - 1:
                        current_order[idx], current_order[idx + 1] = current_order[idx + 1], current_order[idx]
                        st.session_state.user_sort_order = current_order
                        st.rerun()
                
                # 順番を保存するボタン
                if st.button("順番を保存", type="primary"):
                    if dm.sort_users(current_order):
                        st.success("✅ 利用者の順番を更新しました")
                        # セッション状態をクリア
                        if "user_sort_order" in st.session_state:
                            del st.session_state.user_sort_order
                        st.rerun()
                    else:
                        st.error("順番の更新に失敗しました")
                
                # リセットボタン
                if st.button("リセット", type="secondary"):
                    if "user_sort_order" in st.session_state:
                        del st.session_state.user_sort_order
                    st.rerun()
            
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
            
            # 完全削除機能
            with st.expander("⚠️ 利用者を完全に削除", expanded=False):
                st.warning("⚠️ この操作は取り消せません。利用者データが完全に削除されます。")
                st.caption("無効化された利用者のみ完全削除できます。")
                
                users_to_permanently_delete = st.multiselect(
                    "完全に削除する利用者を選択",
                    options=[u["name"] for u in inactive_users],
                    key="users_to_permanently_delete"
                )
                
                # 確認用のチェックボックス
                confirm_delete = st.checkbox(
                    "完全削除を実行することを確認しました",
                    key="confirm_permanent_delete"
                )
                
                if st.button("選択した利用者を完全に削除", type="primary", disabled=not confirm_delete):
                    if users_to_permanently_delete:
                        if confirm_delete:
                            deleted_count = dm.permanently_delete_users(users_to_permanently_delete)
                            if deleted_count > 0:
                                st.success(f"✅ {deleted_count}名の利用者を完全に削除しました")
                                st.rerun()
                            else:
                                st.error("完全削除に失敗しました")
                        else:
                            st.warning("確認チェックボックスにチェックを入れてください")
                    else:
                        st.warning("完全削除する利用者を選択してください")


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


def render_daily_comments_viewer():
    """日報コメント確認画面の描画"""
    st.markdown('<div class="main-header">📝 日報コメント確認</div>', unsafe_allow_html=True)

    dm = st.session_state.data_manager

    # 日付フィルター
    st.markdown('<div class="section-header">🔍 検索条件</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        filter_start_date = st.date_input(
            "開始日",
            value=None,
            key="comment_filter_start_date"
        )
    with col2:
        filter_end_date = st.date_input(
            "終了日",
            value=None,
            key="comment_filter_end_date"
        )
    with col3:
        # スタッフ名の選択肢を取得
        all_comments = dm.get_daily_comments()
        staff_names = list(set(comment['記入スタッフ名'] for comment in all_comments if comment['記入スタッフ名']))
        staff_names.sort()

        filter_staff = st.selectbox(
            "スタッフ名フィルター",
            options=["全て"] + staff_names,
            key="comment_filter_staff"
        )

    # フィルタリング適用
    staff_filter = None if filter_staff == "全て" else filter_staff
    comments = dm.get_daily_comments(
        start_date=filter_start_date if filter_start_date else None,
        end_date=filter_end_date if filter_end_date else None,
        staff_name=staff_filter
    )

    if not comments:
        st.info("該当する日報コメントがありません。")
        return

    st.markdown('<div class="section-header">📋 日報コメント一覧</div>', unsafe_allow_html=True)
    st.markdown(f"**{len(comments)}件の日報コメントが見つかりました**")

    # コメント一覧を表示
    for i, comment in enumerate(comments, 1):
        with st.expander(f"#{i} {comment['業務日']} - {comment['記入スタッフ名']}", expanded=(i <= 3)):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("**業務日:**")
                st.write(comment['業務日'])
                st.markdown("**記入者:**")
                st.write(comment['記入スタッフ名'])
                if comment['created_at']:
                    try:
                        created_dt = datetime.fromisoformat(comment['created_at'])
                        st.markdown("**作成日時:**")
                        st.write(created_dt.strftime('%Y年%m月%d日 %H:%M:%S'))
                    except:
                        pass
            with col2:
                st.markdown("**日報コメント:**")
                # コメントを適切に表示（長い場合は折り返し）
                if len(comment['日報コメント']) > 200:
                    st.text_area(
                        "コメント内容",
                        value=comment['日報コメント'],
                        height=150,
                        disabled=True,
                        key=f"comment_{i}"
                    )
                else:
                    st.info(comment['日報コメント'])


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
                
                # 削除ボタン
                st.markdown("---")
                st.markdown("**⚠️ 記録の削除**")
                delete_confirm = st.checkbox(
                    f"{date_obj.strftime('%Y年%m月%d日')}の利用者記録を削除する",
                    key=f"delete_confirm_{date_str}",
                    help="この日の利用者記録を削除する場合はチェックを入れてください"
                )
                if delete_confirm:
                    if st.button("🗑️ 削除を実行", use_container_width=True, type="secondary", key=f"delete_{date_str}"):
                        if dm.delete_daily_users(date_str):
                            st.success(f"✅ {date_obj.strftime('%Y年%m月%d日')}の利用者記録を削除しました")
                            st.rerun()
                        else:
                            st.error("削除に失敗しました")
            else:
                st.info("この日の利用者記録はありません。")
    else:
        st.info(f"{selected_year}年{selected_month}月には利用者記録がありません。")
    
    # 統計情報
    st.markdown("---")
    st.markdown('<div class="section-header">📊 統計情報</div>', unsafe_allow_html=True)
    
    # 選択した月の統計
    if recorded_dates:
        total_users_all_days = sum(len(users) for _, _, users in recorded_dates)
        avg_users_per_day = total_users_all_days / len(recorded_dates) if recorded_dates else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("記録日数", f"{len(recorded_dates)}日")
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

        # システム状態確認とテスト機能
        with st.expander("🔧 システム診断（開発者向け）", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**システム状態**")
                dm = st.session_state.data_manager
                st.write(f"Supabase有効: {dm._is_supabase_enabled()}")
                st.write(f"データディレクトリ: {dm.data_dir}")

                meeting_file = dm.data_dir / "morning_meetings.json"
                st.write(f"議事録ファイル: {meeting_file.name}")
                if meeting_file.exists():
                    st.success(f"✅ 存在 ({meeting_file.stat().st_size} bytes)")
                else:
                    st.error("❌ 存在しません")

            with col2:
                st.write("**クイックテスト**")

                if st.button("📊 現在の議事録件数確認", key="check_meeting_count"):
                    try:
                        meetings = dm.get_morning_meetings()
                        st.info(f"現在の議事録件数: {len(meetings)}件")
                        if meetings:
                            st.write("最新の議事録:")
                            st.json(meetings[0])
                    except Exception as e:
                        st.error(f"確認エラー: {e}")

                if st.button("🧪 テストデータ保存", key="save_test_data"):
                    test_data = {
                        "日付": date.today().isoformat(),
                        "記入スタッフ名": st.session_state.get("staff_name", "テストユーザー"),
                        "タイトル": "システムテストの件",
                        "議題・内容": "システム保存機能のテスト",
                        "決定事項": "テスト正常完了",
                        "共有事項": "テストデータ",
                        "その他メモ": f"テスト実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }

                    with st.spinner("テストデータを保存しています..."):
                        success, error_msg = dm.save_morning_meeting(test_data)

                    if success:
                        st.success("✅ テストデータ保存成功")
                        # 保存後の件数確認
                        meetings_after = dm.get_morning_meetings()
                        st.info(f"保存後の総件数: {len(meetings_after)}件")
                    else:
                        st.error(f"❌ テストデータ保存失敗: {error_msg}")
                        st.code(error_msg)

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

                                # タイトルも設定（「の件」形式で）
                                if "タイトル" in result and result.get("タイトル"):
                                    st.session_state.meeting_title = result.get("タイトル")
                                elif st.session_state.meeting_agenda:
                                    # タイトルが生成されていない場合は自動生成
                                    title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(st.session_state.meeting_agenda)
                                    if title_success and generated_title:
                                        st.session_state.meeting_title = generated_title

                                st.success("✅ 議事録を生成しました！以下の内容を確認・編集して保存してください。")
                                st.rerun()
                            else:
                                error_msg = result if result is not None else "不明なエラー"
                                st.error(f"議事録の生成に失敗しました: {error_msg}")
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
        if "meeting_title" not in st.session_state:
            st.session_state.meeting_title = ""
        
        with st.form("morning_meeting_form"):
            meeting_date = st.date_input(
                "日付 *",
                value=date.today(),
                key="meeting_date"
            )
            
            # タイトル入力フィールド（直接入力可能・目立つ位置に配置）
            st.markdown("#### 📝 タイトル（直接入力可能）")
            col1, col2 = st.columns([3, 1])
            with col1:
                title_input = st.text_input(
                    "タイトル *（「○○の件」形式で入力、または空欄で自動生成）",
                    value=st.session_state.get("meeting_title", ""),
                    key="meeting_title_input",
                    placeholder="例: 利用者送迎に関する件",
                    help="タイトルを直接入力してください。「○○の件」形式で入力すると自動的に適用されます。空欄の場合は議題・内容から自動生成されます。"
                )
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                auto_generate_title = st.form_submit_button("✨ 自動生成", use_container_width=True, help="議題・内容からタイトルを自動生成します")
            
            # タイトル自動生成ボタンが押された場合
            if auto_generate_title:
                if agenda and agenda.strip():
                    with st.spinner("タイトルを生成中..."):
                        title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(agenda)
                        if title_success and generated_title:
                            st.session_state.meeting_title = generated_title
                            st.rerun()
                else:
                    st.warning("⚠️ 議題・内容を入力してから自動生成ボタンを押してください。")
            
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
                    # タイトルの処理（直接入力または自動生成）- 必ず「の件」形式を保証
                    final_title = ""
                    if title_input and title_input.strip():
                        # 直接入力されたタイトルを使用（必ず「の件」形式に変換）
                        final_title = title_input.strip()
                        # ensure_title_formatで処理（必ず「の件」形式に変換）
                        final_title = st.session_state.ai_helper.ensure_title_format(final_title, agenda if agenda else "")
                    elif agenda and agenda.strip():
                        # タイトルが入力されていない場合は、議題・内容から自動生成
                        title_success, generated_title = st.session_state.ai_helper.generate_title_from_text(agenda)
                        if title_success and generated_title:
                            final_title = generated_title
                            # 最終確認: 必ず「の件」で終わることを確認（二重チェック）
                            if not final_title.endswith("の件"):
                                final_title = st.session_state.ai_helper.ensure_title_format(final_title, agenda)
                        else:
                            # フォールバック: 簡易的にタイトルを生成（必ず「の件」形式）
                            final_title = st.session_state.ai_helper.ensure_title_format("", agenda)
                    else:
                        # フォールバック
                        final_title = "議事録の件"
                    
                    # 最終確認: 必ず「の件」で終わることを確認（三重チェック）
                    if not final_title.endswith("の件"):
                        final_title = final_title + "の件"
                        print(f"タイトル修正: '{final_title}'")

                    # 保存前の最終データ検証
                    print(f"最終保存データ検証: タイトル='{final_title}', 長さ={len(final_title)}")
                    if not final_title or not final_title.strip():
                        st.error("❌ タイトルが空です。再度お試しください。")
                        st.stop()
                    if not agenda or not agenda.strip():
                        st.error("❌ 議題・内容が空です。再度お試しください。")
                        st.stop()
                    
                    meeting_data = {
                        "日付": meeting_date.isoformat(),
                        "記入スタッフ名": st.session_state.staff_name,
                        "タイトル": final_title,
                        "議題・内容": agenda,
                        "決定事項": decisions if decisions else "",
                        "共有事項": shared_items if shared_items else "",
                        "その他メモ": notes if notes else ""
                    }

                    # 作成データの詳細ログ出力
                    print(f"作成された議事録データ: {meeting_data}")
                    print(f"データ型チェック:")
                    for key, value in meeting_data.items():
                        print(f"  {key}: {type(value)} = {repr(value)}")

                    with st.spinner("議事録を保存しています..."):
                        # 保存前に詳細ログ出力
                        print(f"=== 議事録保存開始 ===")
                        print(f"保存データ: {meeting_data}")
                        print(f"Supabase有効: {st.session_state.data_manager._is_supabase_enabled()}")

                        success, error_message = st.session_state.data_manager.save_morning_meeting(meeting_data)

                        print(f"保存結果: success={success}, error='{error_message}'")

                    if success:
                        st.success("✅ 朝礼議事録を保存しました！")
                        st.info("📋 **「📚 議事録閲覧」タブに切り替えて保存された議事録を確認してください。**")

                        # 保存されたデータを確認（デバッグ用）
                        saved_meetings = st.session_state.data_manager.get_morning_meetings()
                        if saved_meetings:
                            st.info(f"💾 保存確認: {len(saved_meetings)}件の議事録が保存されています。")
                        else:
                            st.warning("⚠️ 保存確認: 議事録が保存されていません。ファイルを確認してください。")

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
                        st.error(f"💥 保存に失敗しました")
                        st.error(f"❌ エラー内容: {error_message}")

                        # エラーの種類に応じた対処法を表示
                        if "容量" in error_message:
                            st.info("💡 **対処法**: ストレージの空き容量を確保してください。不要なファイルを削除するか、管理者に連絡してください。")
                        elif "権限" in error_message:
                            st.info("💡 **対処法**: ファイルの書き込み権限がありません。管理者にお問い合わせください。")
                        elif "ネットワーク" in error_message:
                            st.info("💡 **対処法**: インターネット接続を確認してください。ネットワークが回復したら再度お試しください。")
                        elif "データベース" in error_message:
                            st.info("💡 **対処法**: データベース接続に問題があります。システム管理者にお問い合わせください。")
                        else:
                            st.info("💡 **対処法**: 一時的な問題の可能性があります。少し時間を置いて再度お試しください。それでも解決しない場合は、管理者にお問い合わせください。")

                        # 常に詳細なエラー情報を表示（トラブルシューティング用）
                        with st.expander("🔍 詳細なエラー情報（トラブルシューティング）", expanded=True):
                            st.write("**エラーメッセージ**:")
                            st.code(error_message)

                            # システム状態の確認
                            dm = st.session_state.data_manager
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write(f"**Supabase有効状態**: {'有効' if dm._is_supabase_enabled() else '無効'}")
                                st.write(f"**データディレクトリ**: {dm.data_dir}")

                            with col2:
                                # ファイル状態確認
                                meeting_file = dm.data_dir / "morning_meetings.json"
                                st.write(f"**議事録ファイル**: {meeting_file.name}")
                                if meeting_file.exists():
                                    file_size = meeting_file.stat().st_size
                                    st.write(f"**ファイルサイズ**: {file_size} bytes")
                                    st.success("✅ ファイルは存在します")
                                else:
                                    st.error("❌ ファイルが存在しません")

                            # 保存しようとしたデータを表示
                            st.write("**保存しようとしたデータ**:")
                            st.json(meeting_data)

                            # 再試行ボタン
                            if st.button("🔄 保存を再試行", key="retry_save_after_error"):
                                with st.spinner("再試行中..."):
                                    retry_success, retry_error = dm.save_morning_meeting(meeting_data)
                                if retry_success:
                                    st.success("✅ 再試行成功しました！")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ 再試行も失敗しました: {retry_error}")
                                    st.code(f"再試行エラー詳細: {retry_error}")
    
    with tab2:
        st.markdown('<div class="section-header">📚 朝礼議事録一覧</div>', unsafe_allow_html=True)

        # デバッグモードトグル
        debug_mode = st.checkbox("🔧 デバッグモード（開発者向け）", key="debug_mode", help="詳細なデバッグ情報とトラブルシューティング情報を表示します")

        # 強制ローカル読み込みオプション
        force_local = st.checkbox("📁 強制ローカル読み込み", key="force_local", help="Supabaseが有効でもローカルファイルからデータを読み込みます")

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
            # デバッグ情報表示
            if debug_mode:
                st.info("🔍 **デバッグ情報**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Supabase有効: {dm._is_supabase_enabled()}")
                    st.write(f"強制ローカル: {force_local}")
                with col2:
                    st.write(f"開始日フィルタ: {start_date_str}")
                    st.write(f"終了日フィルタ: {end_date_str}")

            # データ取得（強制ローカルオプション対応）
            if force_local:
                meetings = dm._load_morning_meetings()
                # 日付フィルタリングを手動適用
                if start_date_str or end_date_str:
                    from datetime import datetime
                    filtered_meetings = []
                    for meeting in meetings:
                        meeting_date = meeting.get("日付", "")
                        if isinstance(meeting_date, str):
                            try:
                                meeting_date_obj = datetime.fromisoformat(meeting_date).date()
                                if start_date_str:
                                    start_date_obj = datetime.fromisoformat(start_date_str).date()
                                    if meeting_date_obj < start_date_obj:
                                        continue
                                if end_date_str:
                                    end_date_obj = datetime.fromisoformat(end_date_str).date()
                                    if meeting_date_obj > end_date_obj:
                                        continue
                                filtered_meetings.append(meeting)
                            except:
                                continue
                    meetings = filtered_meetings
            else:
                meetings = dm.get_morning_meetings(start_date_str, end_date_str)

            # データ取得結果のデバッグ
            if st.session_state.get("debug_mode", False):
                st.write(f"取得した議事録件数: {len(meetings)}")
                if meetings:
                    st.write("最初の議事録のサンプル:")
                    st.json(meetings[0])

        except AttributeError as e:
            st.error(f"エラー: get_morning_meetings メソッドの呼び出しに失敗しました: {str(e)}")
            st.info("DataManagerクラスにget_morning_meetingsメソッドが存在するか確認してください。")
            st.stop()
        except Exception as e:
            st.error(f"エラー: 朝礼議事録の取得に失敗しました: {str(e)}")
            # 詳細なエラー情報表示
            if st.session_state.get("debug_mode", False):
                import traceback
                st.code(traceback.format_exc())
            st.stop()
        
        if not meetings:
            st.info("朝礼議事録が登録されていません。")

            # デバッグ情報とトラブルシューティング
            if st.session_state.get("debug_mode", False):
                st.warning("🔧 **トラブルシューティング情報**")

                # Supabase状態確認
                is_supabase_enabled = dm._is_supabase_enabled()
                st.write(f"**Supabase有効状態**: {'有効' if is_supabase_enabled else '無効'}")

                if is_supabase_enabled:
                    st.info("💡 **Supabaseが有効な場合**: Supabaseデータベースからデータを取得しています。Supabaseにデータが存在するか確認してください。")
                else:
                    st.info("💡 **ローカル保存の場合**: morning_meetings.jsonファイルからデータを読み込んでいます。")

                    # ローカルファイル確認
                    try:
                        meeting_file = dm.data_dir / "morning_meetings.json"
                        st.write(f"**ファイルパス**: {meeting_file}")

                        if meeting_file.exists():
                            st.success(f"✅ ファイルは存在します")

                            # ファイルサイズ確認
                            file_size = meeting_file.stat().st_size
                            st.write(f"**ファイルサイズ**: {file_size} bytes")

                            # ファイル内容確認
                            with open(meeting_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                st.write("**ファイル内容**:")
                                st.code(content, language='json')

                                # JSONとして読み込みテスト
                                try:
                                    data = json.loads(content)
                                    st.success(f"✅ JSON形式は正しい（{len(data)}件のデータ）")
                                except json.JSONDecodeError as e:
                                    st.error(f"❌ JSON形式エラー: {e}")

                        else:
                            st.error(f"❌ ファイルが存在しません: {meeting_file}")
                            st.info("💡 **対処法**: ファイルが存在しない場合は、議事録入力でデータを保存してください。")

                    except Exception as e:
                        st.error(f"❌ ファイル確認エラー: {e}")

                # 強制ローカル読み込みテスト
                st.markdown("---")
                if st.button("🔄 ローカルファイルから強制読み込みテスト", key="force_local_test"):
                    try:
                        local_meetings = dm._load_morning_meetings()
                        st.write(f"**直接読み込み結果**: {len(local_meetings)}件")
                        if local_meetings:
                            st.success("✅ ローカルファイルからの読み込みは成功しています")
                            st.json(local_meetings[0])
                        else:
                            st.warning("⚠️ ローカルファイルは空です")
                    except Exception as e:
                        st.error(f"❌ 直接読み込みエラー: {e}")
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
                agenda_content = selected_meeting.get("議題・内容", "")
                if agenda_content:
                    # 改行を保持して表示
                    st.markdown(f'<div style="white-space: pre-wrap;">{agenda_content}</div>', unsafe_allow_html=True)
                else:
                    st.markdown("")
                
                if selected_meeting.get("決定事項"):
                    st.markdown("---")
                    st.markdown("#### 決定事項")
                    decisions_content = selected_meeting.get("決定事項", "")
                    if decisions_content:
                        # 改行を保持して表示
                        st.markdown(f'<div style="white-space: pre-wrap;">{decisions_content}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("")
                
                if selected_meeting.get("共有事項"):
                    st.markdown("---")
                    st.markdown("#### 共有事項")
                    shared_content = selected_meeting.get("共有事項", "")
                    if shared_content:
                        # 改行を保持して表示
                        st.markdown(f'<div style="white-space: pre-wrap;">{shared_content}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("")
                
                if selected_meeting.get("その他メモ"):
                    st.markdown("---")
                    st.markdown("#### その他メモ")
                    notes_content = selected_meeting.get("その他メモ", "")
                    if notes_content:
                        # 改行を保持して表示
                        st.markdown(f'<div style="white-space: pre-wrap;">{notes_content}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("")
                
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

    # Supabase接続テスト
    st.markdown('<div class="section-header">🔗 Supabase接続テスト</div>', unsafe_allow_html=True)

    # 接続テストボタン（常に表示）
    if st.button("🔍 接続テスト", help="Supabaseへの接続をテストします", key="supabase_test_button"):
        try:
            test_result = st.session_state.data_manager.supabase_manager.test_connection()
            if test_result["connected"] and test_result["table_accessible"]:
                st.success(f"✅ 接続成功！データベース内のアカウント数: {test_result['account_count']}")
            elif not test_result["enabled"]:
                st.info("""
                ℹ️ **Supabaseが設定されていません**

                現在、ローカルファイルストレージを使用しています。Supabaseを使用するには:

                1. [Supabase](https://supabase.com/)でプロジェクトを作成
                2. 環境変数 `SUPABASE_URL` と `SUPABASE_KEY` を設定
                3. `supabase_schema.sql` をSQL Editorで実行

                詳細: `SUPABASE_SETUP.md` を参照してください。
                """)
            else:
                error_detail = test_result.get("error", "不明なエラー")
                st.error(f"❌ 接続エラー: {error_detail}")
                if "Row Level Security" in error_detail or "permission denied" in error_detail.lower():
                    st.warning("""
                    ⚠️ **Row Level Security (RLS) が有効になっている可能性があります**

                    **解決方法:**
                    1. Supabase Dashboard → SQL Editor を開く
                    2. 以下のSQLを実行してください:

                    ```sql
                    ALTER TABLE staff_accounts DISABLE ROW LEVEL SECURITY;
                    ALTER TABLE users_master DISABLE ROW LEVEL SECURITY;
                    ALTER TABLE daily_reports DISABLE ROW LEVEL SECURITY;
                    ALTER TABLE morning_meetings DISABLE ROW LEVEL SECURITY;
                    ALTER TABLE tags_master DISABLE ROW LEVEL SECURITY;
                    ALTER TABLE daily_users DISABLE ROW LEVEL SECURITY;
                    ```

                    または、`supabase_schema.sql` ファイルのRLS無効化コマンドを実行してください。
                    """)
                elif "nodename nor servname provided" in error_detail or "Name resolution failure" in error_detail:
                    st.warning("""
                    ⚠️ **Supabase URLが無効です**

                    **考えられる原因:**
                    - SUPABASE_URLが正しく設定されていない
                    - Supabaseプロジェクトが存在しない

                    **解決方法:**
                    1. Supabaseプロジェクトを作成してください
                    2. Settings → API から正しいURLを取得してください
                    """)
        except Exception as e:
            st.error(f"❌ テスト実行中にエラーが発生しました: {str(e)}")
            st.exception(e)

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
    
    # 全データのエクスポート/インポート
    st.markdown("#### 📦 全データのエクスポート・インポート")
    st.info("💡 アプリを更新・リブートする前に、全データをエクスポートしてバックアップを取ることをお勧めします。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📤 データのエクスポート")
        st.markdown("すべてのデータ（利用者マスタ、日報、設定など）をZIPファイルにエクスポートします。")
        
        if st.button("📥 全データをエクスポート", use_container_width=True, type="primary"):
            with st.spinner("データをエクスポート中..."):
                export_path = st.session_state.data_manager.export_all_data()
                if export_path:
                    export_file = Path(export_path)
                    if export_file.exists():
                        with open(export_file, 'rb') as f:
                            st.download_button(
                                label="💾 ZIPファイルをダウンロード",
                                data=f.read(),
                                file_name=export_file.name,
                                mime="application/zip",
                                use_container_width=True
                            )
                        st.success(f"✅ エクスポート完了: {export_file.name}")
                    else:
                        st.error("エクスポートファイルが見つかりません")
                else:
                    st.error("エクスポートに失敗しました")
    
    with col2:
        st.markdown("##### 📥 データのインポート")
        st.markdown("エクスポートしたZIPファイルからデータを復元します。")
        st.warning("⚠️ インポートすると既存のデータが上書きされる可能性があります。")
        
        uploaded_file = st.file_uploader(
            "ZIPファイルを選択",
            type=['zip'],
            key="import_zip_file",
            help="エクスポートしたZIPファイルを選択してください"
        )
        
        if uploaded_file is not None:
            col_a, col_b = st.columns(2)
            with col_a:
                overwrite = st.checkbox("既存データを上書き", value=False, key="import_overwrite")
            
            if st.button("📤 データをインポート", use_container_width=True, type="primary"):
                # アップロードされたファイルを一時ファイルに保存
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    with st.spinner("データをインポート中..."):
                        success = st.session_state.data_manager.import_all_data(tmp_path, overwrite=overwrite)
                        if success:
                            st.success("✅ インポートが完了しました。ページをリロードしてください。")
                            st.info("ページをリロードするには、ブラウザの更新ボタンを押すか、サイドバーの「設定」を再度選択してください。")
                        else:
                            st.error("インポートに失敗しました")
                finally:
                    # 一時ファイルを削除
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    st.markdown("---")
    
    # 日報データのCSVエクスポート（既存機能）
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 日報データのエクスポート（CSV形式）")
        if st.button("CSV形式でダウンロード", use_container_width=True):
            df = st.session_state.data_manager.get_reports()
            if not df.empty:
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 CSVをダウンロード",
                    data=csv,
                    file_name=f"daily_reports_{date.today().isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("エクスポートするデータがありません")
    
    with col2:
        st.markdown("#### 📊 データの確認")
        if st.button("日報データを表示", use_container_width=True):
            df = st.session_state.data_manager.get_reports()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("データがありません")


def main():
    """メイン関数"""
    # セッション状態の初期化（初回のみ）
    # 注意: data_managerとlogged_inはファイルのトップレベルで初期化されている
    
    # data_managerの初期化確認（念のため）
    if 'data_manager' not in st.session_state:
        try:
            st.session_state.data_manager = DataManager()
        except Exception as e:
            st.error(f"❌ データマネージャーの初期化に失敗しました: {str(e)}")
            st.exception(e)
            return
    
    # logged_inの初期化確認（念のため）
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'logged_in_user' not in st.session_state:
        st.session_state.logged_in_user = None
    
    # その他のセッション状態の初期化
    if 'work_date' not in st.session_state:
        st.session_state.work_date = date.today()
    if 'staff_name' not in st.session_state:
        st.session_state.staff_name = ""
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time(9, 0)
    if 'end_time' not in st.session_state:
        st.session_state.end_time = time(17, 0)
    
    # ログイン状態をチェック
    if not st.session_state.get('logged_in', False):
        # ログインしていない場合はログインページを表示
        render_login_page()
        return
    
    # デバッグ情報（開発時のみ）
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "日報入力"
    
    # ログイン済みの場合は通常のアプリケーションを表示
    # サイドバーの描画（ウィジェットが自動的にセッション状態を更新）
    render_sidebar()
    
    # ページに応じたコンテンツを表示
    try:
        if st.session_state.current_page == "日報入力":
            render_daily_report_form()
        elif st.session_state.current_page == "保存済み日報閲覧":
            render_saved_reports_viewer()
        elif st.session_state.current_page == "利用者記録閲覧":
            render_daily_users_calendar()
        elif st.session_state.current_page == "日報コメント確認":
            render_daily_comments_viewer()
        elif st.session_state.current_page == "利用者マスタ管理":
            render_user_master()
        elif st.session_state.current_page == "朝礼議事録":
            render_morning_meeting()
        elif st.session_state.current_page == "設定":
            render_settings()
        else:
            st.warning(f"不明なページ: {st.session_state.current_page}")
    except Exception as e:
        st.error(f"ページの表示中にエラーが発生しました: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.exception(e)

