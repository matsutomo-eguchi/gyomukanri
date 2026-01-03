#!/bin/bash
# Google Cloud デプロイセットアップスクリプト
# GOOGLE_CLOUD_DEPLOY.md の手順を自動化

set -e

# gcloudのPython環境を設定（パーミッションエラーを回避）
if [ -f "/opt/homebrew/bin/python3" ]; then
    export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3
elif [ -f "/usr/local/bin/python3" ]; then
    export CLOUDSDK_PYTHON=/usr/local/bin/python3
elif command -v python3 &> /dev/null; then
    export CLOUDSDK_PYTHON=$(which python3)
fi

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# プロジェクト設定（変更してください）
PROJECT_ID="${GCP_PROJECT_ID:-YOUR_PROJECT_ID}"
REGION="asia-northeast1"
SERVICE_NAME="business-management"
REPO_NAME="business-management"
SERVICE_ACCOUNT_NAME="github-actions-sa"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Google Cloud デプロイセットアップ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. Google Cloud認証の確認
echo -e "${YELLOW}[1/6] Google Cloud認証の確認${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}エラー: Google Cloudにログインしていません${NC}"
    echo "以下のコマンドを実行してください:"
    echo "  gcloud auth login"
    exit 1
fi
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
echo -e "${GREEN}✓ 認証済み: ${ACTIVE_ACCOUNT}${NC}"
echo ""

# 2. プロジェクトの設定
echo -e "${YELLOW}[2/6] Google Cloudプロジェクトの設定${NC}"
if [ "$PROJECT_ID" = "YOUR_PROJECT_ID" ]; then
    echo -e "${RED}エラー: PROJECT_IDが設定されていません${NC}"
    echo "環境変数を設定するか、スクリプト内のPROJECT_IDを変更してください:"
    echo "  export GCP_PROJECT_ID=your-project-id"
    echo "  または"
    echo "  このスクリプトのPROJECT_ID変数を編集してください"
    exit 1
fi

# プロジェクトが存在するか確認
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
    echo -e "${YELLOW}プロジェクトが存在しません。作成しますか？ (y/n)${NC}"
    read -r response
    if [ "$response" = "y" ]; then
        gcloud projects create "$PROJECT_ID" --name="Business Management"
        echo "プロジェクトを作成しました。請求先アカウントをリンクしてください。"
        echo "Google Cloud Console: https://console.cloud.google.com/billing"
        exit 0
    else
        echo "プロジェクト作成をスキップしました。"
        exit 1
    fi
fi

gcloud config set project "$PROJECT_ID"
echo -e "${GREEN}✓ プロジェクト設定完了: ${PROJECT_ID}${NC}"
echo ""

# 3. 必要なAPIの有効化
echo -e "${YELLOW}[3/6] 必要なAPIの有効化${NC}"
APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
    "containerregistry.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "  - $api を有効化中..."
    gcloud services enable "$api" --quiet || echo "  ⚠ $api の有効化に失敗（既に有効かもしれません）"
done
echo -e "${GREEN}✓ API有効化完了${NC}"
echo ""

# 4. Artifact Registryリポジトリの作成
echo -e "${YELLOW}[4/6] Artifact Registryリポジトリの作成${NC}"
REPO_PATH="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"
if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &>/dev/null; then
    echo -e "${GREEN}✓ リポジトリは既に存在します${NC}"
else
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Business Management Application Docker Images"
    echo -e "${GREEN}✓ リポジトリを作成しました${NC}"
fi
echo ""

# 5. サービスアカウントの作成と権限設定
echo -e "${YELLOW}[5/6] サービスアカウントの作成と権限設定${NC}"
SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
    echo -e "${GREEN}✓ サービスアカウントは既に存在します${NC}"
else
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="GitHub Actions Service Account"
    echo -e "${GREEN}✓ サービスアカウントを作成しました${NC}"
fi

# 権限の付与
echo "  権限を付与中..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.admin" \
    --quiet || echo "  ⚠ roles/run.admin の付与に失敗（既に付与されているかもしれません）"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/iam.serviceAccountUser" \
    --quiet || echo "  ⚠ roles/iam.serviceAccountUser の付与に失敗（既に付与されているかもしれません）"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/artifactregistry.writer" \
    --quiet || echo "  ⚠ roles/artifactregistry.writer の付与に失敗（既に付与されているかもしれません）"

echo -e "${GREEN}✓ 権限設定完了${NC}"
echo ""

# 6. サービスアカウントキーの生成
echo -e "${YELLOW}[6/6] サービスアカウントキーの生成${NC}"
KEY_FILE="github-actions-key.json"
if [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}⚠ ${KEY_FILE} は既に存在します。上書きしますか？ (y/n)${NC}"
    read -r response
    if [ "$response" != "y" ]; then
        echo "キー生成をスキップしました。"
    else
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SA_EMAIL"
        echo -e "${GREEN}✓ サービスアカウントキーを生成しました: ${KEY_FILE}${NC}"
        echo -e "${RED}⚠ 重要: このファイルは機密情報です。GitHub Secretsに追加してください。${NC}"
    fi
else
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL"
    echo -e "${GREEN}✓ サービスアカウントキーを生成しました: ${KEY_FILE}${NC}"
    echo -e "${RED}⚠ 重要: このファイルは機密情報です。GitHub Secretsに追加してください。${NC}"
fi
echo ""

# 完了メッセージ
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}セットアップが完了しました！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "次のステップ:"
echo ""
echo "1. GitHub Secretsの設定:"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - GCP_SA_KEY: $KEY_FILE の内容全体をコピー"
echo "   - SUPABASE_URL: Supabase Settings → API → Project URL"
echo "   - SUPABASE_KEY: Supabase Settings → API → anon public key"
echo "   - GROK_API_KEY: （オプション）"
echo "   - GEMINI_API_KEY: （オプション）"
echo ""
echo "2. Supabaseのセットアップ:"
echo "   - GOOGLE_CLOUD_DEPLOY.md の「Supabaseのセットアップ」セクションを参照"
echo "   - SQL Editorでテーブルを作成"
echo ""
echo "3. デプロイ:"
echo "   - GitHubにコードをプッシュすると自動デプロイされます"
echo "   - または、手動でデプロイする場合:"
echo "     gcloud builds submit --config cloudbuild.yaml"
echo ""

