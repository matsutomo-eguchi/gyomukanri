#!/bin/bash

# M3 MacBook Pro (Apple Silicon) 最適化版
# 放課後等デイサービス 業務管理フォーム起動スクリプト

set -e  # エラー時に終了

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}放課後等デイサービス 業務管理フォーム${NC}"
echo -e "${BLUE}M3 MacBook Pro 最適化版${NC}"
echo -e "${BLUE}========================================${NC}"

# Python3のパスを検出（Apple Silicon対応）
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${YELLOW}エラー: Python3が見つかりません${NC}"
    echo "Homebrewを使用してインストールしてください:"
    echo "  brew install python3"
    exit 1
fi

# Pythonバージョンを確認
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python バージョン: ${PYTHON_VERSION}${NC}"

# アーキテクチャを確認
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    echo -e "${GREEN}✓ Apple Silicon (ARM64) を検出しました${NC}"
else
    echo -e "${YELLOW}⚠ Intel Mac を検出しました（M3 MacBook Proではありません）${NC}"
fi

# 仮想環境の確認と作成
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}仮想環境が見つかりません。作成します...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ 仮想環境を作成しました${NC}"
fi

# 仮想環境の有効化
echo -e "${BLUE}仮想環境を有効化しています...${NC}"
source venv/bin/activate

# pipのアップグレード
echo -e "${BLUE}pipをアップグレードしています...${NC}"
pip install --upgrade pip --quiet

# 依存パッケージのインストール確認
if [ ! -f "venv/.installed" ] || [ "requirements.txt" -nt "venv/.installed" ]; then
    echo -e "${BLUE}依存パッケージをインストールしています...${NC}"
    pip install -r requirements.txt --quiet
    touch venv/.installed
    echo -e "${GREEN}✓ 依存パッケージのインストールが完了しました${NC}"
else
    echo -e "${GREEN}✓ 依存パッケージは最新です${NC}"
fi

# Streamlitの起動
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}アプリケーションを起動しています...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}ブラウザが自動的に開きます${NC}"
echo -e "${YELLOW}終了する場合は Ctrl+C を押してください${NC}"
echo ""

streamlit run app.py --server.headless=false

