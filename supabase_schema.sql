-- Supabaseデータベーススキーマ
-- このSQLをSupabaseのSQL Editorで実行してください

-- 利用者マスタテーブル
CREATE TABLE IF NOT EXISTS users_master (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    classification TEXT NOT NULL DEFAULT '放課後等デイサービス',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 日報データテーブル
CREATE TABLE IF NOT EXISTS daily_reports (
    id SERIAL PRIMARY KEY,
    業務日 DATE,
    記入スタッフ名 TEXT,
    担当利用者名 TEXT,
    利用者区分 TEXT,
    始業時間 TEXT,
    終業時間 TEXT,
    体温 TEXT,
    バイタルその他 TEXT,
    気分顔色 TEXT,
    学習内容タグ TEXT,
    学習内容詳細 TEXT,
    自由遊びタグ TEXT,
    自由遊び詳細 TEXT,
    集団遊びタグ TEXT,
    集団遊び詳細 TEXT,
    食事状態 TEXT,
    食事詳細 TEXT,
    水分補給量 INTEGER,
    排泄記録 TEXT,
    特記事項 TEXT,
    送迎区分 TEXT,
    使用車両 TEXT,
    送迎児童名 TEXT,
    送迎人数 INTEGER,
    到着時刻 TEXT,
    退所時間 TEXT,
    ヒヤリハット事故 TEXT,
    ヒヤリハット詳細 TEXT,
    発生場所 TEXT,
    対象者 TEXT,
    事故発生の状況 TEXT,
    経過 TEXT,
    事故原因 TEXT,
    対策 TEXT,
    その他 TEXT,
    申し送り事項 TEXT,
    備品購入要望 TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- スタッフアカウントテーブル
CREATE TABLE IF NOT EXISTS staff_accounts (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE
);

-- 朝礼議事録テーブル
CREATE TABLE IF NOT EXISTS morning_meetings (
    id SERIAL PRIMARY KEY,
    日付 DATE NOT NULL,
    記入スタッフ名 TEXT,
    議題・内容 TEXT,
    決定事項 TEXT,
    共有事項 TEXT,
    その他メモ TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- タグマスタテーブル
CREATE TABLE IF NOT EXISTS tags_master (
    id SERIAL PRIMARY KEY,
    tag_type TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tag_type, tag_name)
);

-- インデックスの作成（パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_daily_reports_業務日 ON daily_reports(業務日);
CREATE INDEX IF NOT EXISTS idx_morning_meetings_日付 ON morning_meetings(日付);
CREATE INDEX IF NOT EXISTS idx_users_master_active ON users_master(active);
CREATE INDEX IF NOT EXISTS idx_staff_accounts_user_id ON staff_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_tags_master_tag_type ON tags_master(tag_type);

-- Row Level Security (RLS) の設定（必要に応じて）
-- デフォルトではRLSを無効化していますが、セキュリティが必要な場合は有効化してください

-- RLSを有効化する場合の例（認証済みユーザーのみアクセス可能）
-- ALTER TABLE users_master ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow authenticated users" ON users_master FOR ALL USING (auth.role() = 'authenticated');

-- 初期データの投入（オプション）
-- デフォルトタグの追加
INSERT INTO tags_master (tag_type, tag_name) VALUES
    ('learning', 'プリント学習'),
    ('learning', '宿題'),
    ('learning', 'SST（ソーシャルスキルトレーニング）'),
    ('learning', '読み書き練習'),
    ('learning', '計算練習'),
    ('learning', '工作'),
    ('learning', '絵本の読み聞かせ'),
    ('free_play', 'ブロック遊び'),
    ('free_play', 'お絵描き'),
    ('free_play', '読書'),
    ('free_play', 'パズル'),
    ('free_play', 'カードゲーム'),
    ('free_play', 'ままごと'),
    ('free_play', '積み木'),
    ('free_play', '折り紙'),
    ('free_play', 'ぬりえ'),
    ('free_play', '音楽鑑賞'),
    ('group_play', 'リトミック'),
    ('group_play', '体操'),
    ('group_play', '公園遊び'),
    ('group_play', 'ボール遊び'),
    ('group_play', '鬼ごっこ'),
    ('group_play', 'ダンス'),
    ('group_play', '集団ゲーム'),
    ('group_play', '散歩'),
    ('group_play', '運動遊び'),
    ('group_play', '歌')
ON CONFLICT (tag_type, tag_name) DO NOTHING;

