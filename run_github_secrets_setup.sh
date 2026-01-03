#!/bin/bash
# GitHub CLIを使用してSecretsを設定するスクリプト
# ユーザーが指定したコマンドを実行します

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Secrets設定${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# GitHub CLIの確認
if ! command -v gh &> /dev/null; then
    echo -e "${RED}エラー: GitHub CLIがインストールされていません${NC}"
    echo ""
    echo "GitHub CLIをインストールしてください:"
    echo ""
    echo "  # macOS (Homebrew)"
    echo "  brew install gh"
    echo ""
    echo "  # または、公式サイトからダウンロード"
    echo "  https://cli.github.com/"
    echo ""
    exit 1
fi

# GitHub CLIの認証確認
echo -e "${YELLOW}[1/5] GitHub CLI認証の確認${NC}"
if ! gh auth status &>/dev/null; then
    echo -e "${YELLOW}GitHub CLIにログインしていません。ログインを開始します...${NC}"
    echo ""
    gh auth login
else
    echo -e "${GREEN}✓ GitHub CLIにログイン済み${NC}"
    gh auth status
fi
echo ""

# プロジェクト情報の確認
PROJECT_ID="gemini-gijiroku-py"
KEY_FILE="github-actions-key.json"

if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}エラー: $KEY_FILE が見つかりません${NC}"
    exit 1
fi

# Secretsの設定
echo -e "${YELLOW}[2/5] GCP_PROJECT_IDを設定${NC}"
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID"
echo -e "${GREEN}✓ GCP_PROJECT_IDを設定しました: $PROJECT_ID${NC}"
echo ""

echo -e "${YELLOW}[3/5] GCP_SA_KEYを設定${NC}"
gh secret set GCP_SA_KEY < "$KEY_FILE"
echo -e "${GREEN}✓ GCP_SA_KEYを設定しました${NC}"
echo ""

echo -e "${YELLOW}[4/5] SUPABASE_URLを設定${NC}"
echo -e "${YELLOW}Supabase Dashboard → Settings → API → Project URL を入力してください:${NC}"
read -r SUPABASE_URL
if [ -n "$SUPABASE_URL" ]; then
    gh secret set SUPABASE_URL --body "$SUPABASE_URL"
    echo -e "${GREEN}✓ SUPABASE_URLを設定しました${NC}"
else
    echo -e "${YELLOW}⚠ SUPABASE_URLの設定をスキップしました${NC}"
fi
echo ""

echo -e "${YELLOW}[5/5] SUPABASE_KEYを設定${NC}"
echo -e "${YELLOW}Supabase Dashboard → Settings → API → anon public key を入力してください:${NC}"
read -r SUPABASE_KEY
if [ -n "$SUPABASE_KEY" ]; then
    gh secret set SUPABASE_KEY --body "$SUPABASE_KEY"
    echo -e "${GREEN}✓ SUPABASE_KEYを設定しました${NC}"
else
    echo -e "${YELLOW}⚠ SUPABASE_KEYの設定をスキップしました${NC}"
fi
echo ""

# 設定の確認
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}設定完了！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "設定されたSecretsを確認:"
gh secret list
echo ""

