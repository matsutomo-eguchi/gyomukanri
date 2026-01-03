#!/bin/bash
# GitHub Secrets設定ヘルパースクリプト
# このスクリプトは必要な情報を表示し、GitHub CLIまたは手動で設定できるようにします

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Secrets設定ヘルパー${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# プロジェクト情報の取得
PROJECT_ID="gemini-gijiroku-py"
KEY_FILE="github-actions-key.json"

# Gitリポジトリ情報の取得
if git remote get-url origin &>/dev/null; then
    REPO_URL=$(git remote get-url origin)
    # HTTPS形式に変換
    if [[ $REPO_URL == git@* ]]; then
        REPO_URL=$(echo $REPO_URL | sed 's/git@github.com:/https:\/\/github.com\//' | sed 's/\.git$//')
    fi
    REPO_OWNER=$(echo $REPO_URL | sed 's|https://github.com/||' | cut -d'/' -f1)
    REPO_NAME=$(echo $REPO_URL | sed 's|https://github.com/||' | cut -d'/' -f2 | sed 's/\.git$//')
else
    echo -e "${RED}エラー: Gitリポジトリが見つかりません${NC}"
    exit 1
fi

echo -e "${BLUE}リポジトリ情報:${NC}"
echo "  Owner: $REPO_OWNER"
echo "  Repository: $REPO_NAME"
echo ""

# キーファイルの確認
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}エラー: $KEY_FILE が見つかりません${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}設定するGitHub Secrets${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# GCP_PROJECT_ID
echo -e "${YELLOW}1. GCP_PROJECT_ID${NC}"
echo -e "${GREEN}値: ${PROJECT_ID}${NC}"
echo ""

# GCP_SA_KEY
echo -e "${YELLOW}2. GCP_SA_KEY${NC}"
echo -e "${GREEN}値（JSON形式）:${NC}"
cat "$KEY_FILE"
echo ""
echo -e "${RED}⚠ 重要: このJSON全体をコピーしてください（{ から } まで）${NC}"
echo ""

# その他のSecrets
echo -e "${YELLOW}3. SUPABASE_URL${NC}"
echo -e "${BLUE}説明: Supabase Settings → API → Project URL${NC}"
echo -e "${GREEN}値: https://xfjzdzpidfdndjjekshz.supabase.co${NC}"
echo ""

echo -e "${YELLOW}4. SUPABASE_KEY${NC}"
echo -e "${BLUE}説明: Supabase Settings → API → anon public key${NC}"
echo -e "${GREEN}値: sb_publishable_38ezeN9ahUqpUtn2UXcMGw_MIqSxAzD${NC}"
echo ""

echo -e "${YELLOW}5. GROK_API_KEY（オプション）${NC}"
echo -e "${BLUE}説明: Grok APIキー（AI文章生成機能を使用する場合）${NC}"
echo ""

echo -e "${YELLOW}6. GEMINI_API_KEY（オプション）${NC}"
echo -e "${BLUE}説明: Gemini APIキー（音声認識機能を使用する場合）${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}設定方法${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# GitHub CLIが利用可能か確認
if command -v gh &> /dev/null; then
    echo -e "${BLUE}方法1: GitHub CLIを使用（推奨）${NC}"
    echo ""
    echo "以下のコマンドを実行してください:"
    echo ""
    echo "  # GitHub CLIにログイン（初回のみ）"
    echo "  gh auth login"
    echo ""
    echo "  # Secretsを設定"
    echo "  gh secret set GCP_PROJECT_ID --body \"${PROJECT_ID}\""
    echo "  gh secret set GCP_SA_KEY < ${KEY_FILE}"
    echo "  gh secret set SUPABASE_URL --body \"https://xfjzdzpidfdndjjekshz.supabase.co\""
    echo "  gh secret set SUPABASE_KEY --body \"sb_publishable_38ezeN9ahUqpUtn2UXcMGw_MIqSxAzD\""
    echo "  gh secret set GROK_API_KEY  # オプション"
    echo "  gh secret set GEMINI_API_KEY  # オプション"
    echo ""
    echo -e "${BLUE}方法2: Web UIを使用${NC}"
else
    echo -e "${BLUE}Web UIを使用して設定してください:${NC}"
fi

echo ""
echo "1. GitHubリポジトリにアクセス:"
echo "   https://github.com/${REPO_OWNER}/${REPO_NAME}"
echo ""
echo "2. 「Settings」タブをクリック"
echo ""
echo "3. 左メニューから「Secrets and variables」→「Actions」を選択"
echo ""
echo "4. 「New repository secret」をクリック"
echo ""
echo "5. 以下のSecretsを追加:"
echo ""
echo "   Name: GCP_PROJECT_ID"
echo "   Value: ${PROJECT_ID}"
echo ""
echo "   Name: GCP_SA_KEY"
echo "   Value: （上記のJSON全体をコピー＆ペースト）"
echo ""
echo "   Name: SUPABASE_URL"
echo "   Value: （Supabaseから取得したURL）"
echo ""
echo "   Name: SUPABASE_KEY"
echo "   Value: （Supabaseから取得したキー）"
echo ""
echo "   Name: GROK_API_KEY（オプション）"
echo "   Value: （Grok APIキー）"
echo ""
echo "   Name: GEMINI_API_KEY（オプション）"
echo "   Value: （Gemini APIキー）"
echo ""

# GitHub CLIで自動設定を試みる
if command -v gh &> /dev/null; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}自動設定を試みますか？${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}GitHub CLIが利用可能です。自動設定を実行しますか？ (y/n)${NC}"
    read -r response
    if [ "$response" = "y" ]; then
        echo ""
        echo "GitHub CLIにログインしているか確認中..."
        if gh auth status &>/dev/null; then
            echo -e "${GREEN}✓ GitHub CLIにログイン済み${NC}"
            echo ""
            echo "GCP_PROJECT_IDを設定中..."
            echo "${PROJECT_ID}" | gh secret set GCP_PROJECT_ID
            echo ""
            echo "GCP_SA_KEYを設定中..."
            gh secret set GCP_SA_KEY < "${KEY_FILE}"
            echo ""
            echo ""
            echo "SUPABASE_URLを設定中..."
            echo "https://xfjzdzpidfdndjjekshz.supabase.co" | gh secret set SUPABASE_URL
            echo ""
            echo "SUPABASE_KEYを設定中..."
            echo "sb_publishable_38ezeN9ahUqpUtn2UXcMGw_MIqSxAzD" | gh secret set SUPABASE_KEY
            echo ""
            echo -e "${GREEN}✓ すべてのSupabase Secretsを設定しました${NC}"
            echo ""
            echo -e "${YELLOW}オプションのSecrets（AI APIキー等）は必要に応じて設定してください:${NC}"
            echo "  gh secret set GROK_API_KEY  # オプション"
            echo "  gh secret set GEMINI_API_KEY  # オプション"
        else
            echo -e "${YELLOW}GitHub CLIにログインしていません。以下のコマンドでログインしてください:${NC}"
            echo "  gh auth login"
        fi
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}設定完了後の確認${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "設定が完了したら、以下のコマンドで確認できます:"
echo ""
if command -v gh &> /dev/null; then
    echo "  gh secret list"
else
    echo "  GitHubリポジトリの Settings → Secrets and variables → Actions で確認"
fi
echo ""

