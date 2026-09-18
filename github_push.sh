#!/usr/bin/env bash
# =============================================================================
# OMNI-HUB v12.0 — GitHub Push Script
# =============================================================================
# 用途: 初始化git仓库并推送OMNI-HUB v12.0到GitHub
# 用法: chmod +x github_push.sh && ./github_push.sh [GITHUB_TOKEN]
# =============================================================================

set -euo pipefail

# --- 配置 -------------------------------------------------------------------
REPO_NAME="omni-hub"
REPO_OWNER="omni-hub"
REMOTE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
BRANCH="main"
COMMIT_MSG='OMNI-HUB v12.0-final: UNITY E=7641.82, 24 modules, 11-line SI'

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- 参数解析 ---------------------------------------------------------------
GITHUB_TOKEN="${1:-${GITHUB_TOKEN:-}}"

# --- 前置检查 ---------------------------------------------------------------
log_info "OMNI-HUB v12.0 GitHub Push Script"
log_info "===================================="

if ! command -v git &>/dev/null; then
    log_err "git 未安装，请先安装 git"
    exit 1
fi

log_ok "git 版本: $(git --version)"

# --- 仓库初始化 -------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [ -d ".git" ]; then
    log_warn "已存在 .git 目录，将使用现有仓库"
else
    log_info "初始化 git 仓库..."
    git init
    git branch -M "${BRANCH}"
    log_ok "git 仓库已初始化"
fi

# --- Git 配置 ---------------------------------------------------------------
if [ -z "$(git config user.name 2>/dev/null)" ]; then
    git config user.name "OMNI-HUB Deploy Bot"
    log_info "已设置 git user.name"
fi
if [ -z "$(git config user.email 2>/dev/null)" ]; then
    git config user.email "deploy@omni-hub.dev"
    log_info "已设置 git user.email"
fi

# --- 生成 .gitignore --------------------------------------------------------
log_info "生成 .gitignore..."
cat > .gitignore << 'GITIGNORE_EOF'
# =============================================================================
# OMNI-HUB v12.0 — .gitignore
# =============================================================================

# --- Python ------------------------------------------------------------------
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# --- Virtual Environments ----------------------------------------------------
venv/
env/
ENV/
.venv/

# --- IDE & Editors -----------------------------------------------------------
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# --- Jupyter Notebook --------------------------------------------------------
.ipynb_checkpoints

# --- Testing -----------------------------------------------------------------
.pytest_cache/
.coverage
htmlcov/
tox/

# --- Logs & Runtime ----------------------------------------------------------
*.log
logs/
run/
tmp/
temp/
*.pid
*.sock

# --- Secrets & Environment ---------------------------------------------------
.env
.env.local
.env.*.local
secrets.yaml
secrets.json
*.key
*.pem

# --- OS Deployment (generated locally) ---------------------------------------
deploy/.env

# --- Large Data & Artifacts --------------------------------------------------
*.tar.gz
*.zip
*.rar
snapshots/
pipeline_state/
test_state/

# --- Node (if any frontend) --------------------------------------------------
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# --- OMNI-HUB Specific -------------------------------------------------------
.sync/snapshots/
.sync/logs/
hub/pipeline_state/checkpoints/
hub/test_state/
hub/snapshots/
*.png
*.jpg
*.jpeg
*.gif
GITIGNORE_EOF
log_ok ".gitignore 已生成"

# --- 添加文件 ---------------------------------------------------------------
log_info "添加所有文件到 git..."
git add -A

# --- 检查变更 ---------------------------------------------------------------
if git diff --cached --quiet; then
    log_warn "没有变更需要提交"
else
    log_info "创建提交..."
    git commit -m "${COMMIT_MSG}"
    log_ok "提交已创建: ${COMMIT_MSG}"
fi

# --- 远程仓库配置 -----------------------------------------------------------
log_info "配置远程仓库..."
if git remote get-url origin &>/dev/null; then
    CURRENT_URL=$(git remote get-url origin)
    if [ "${CURRENT_URL}" != "${REMOTE_URL}" ]; then
        git remote set-url origin "${REMOTE_URL}"
        log_info "远程仓库 URL 已更新为 ${REMOTE_URL}"
    else
        log_info "远程仓库已配置: ${REMOTE_URL}"
    fi
else
    git remote add origin "${REMOTE_URL}"
    log_ok "远程仓库已添加: ${REMOTE_URL}"
fi

# --- 推送 -------------------------------------------------------------------
log_info "推送到 GitHub..."

if [ -n "${GITHUB_TOKEN}" ]; then
    AUTH_URL="https://${GITHUB_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"
    git remote set-url origin "${AUTH_URL}"
    log_info "使用 GITHUB_TOKEN 认证推送"
fi

# 尝试推送
if git push -u origin "${BRANCH}" --force-with-lease; then
    log_ok "成功推送到 ${REMOTE_URL} (分支: ${BRANCH})"
else
    log_err "推送失败，尝试使用 SSH..."
    SSH_URL="git@github.com:${REPO_OWNER}/${REPO_NAME}.git"
    git remote set-url origin "${SSH_URL}"
    if git push -u origin "${BRANCH}" --force-with-lease; then
        log_ok "成功推送到 ${SSH_URL} (分支: ${BRANCH})"
    else
        log_err "推送失败，请检查:"
        log_err "  1. GitHub 仓库是否存在: ${REMOTE_URL}"
        log_err "  2. 是否有推送权限"
        log_err "  3. SSH 密钥或 Token 是否配置正确"
        exit 1
    fi
fi

# --- 验证 -------------------------------------------------------------------
log_info "验证推送结果..."
git log --oneline -5
log_ok "GitHub 推送完成!"

# --- 摘要 -------------------------------------------------------------------
echo ""
echo "========================================"
echo "  OMNI-HUB v12.0 推送摘要"
echo "========================================"
echo "  仓库:    ${REMOTE_URL}"
echo "  分支:    ${BRANCH}"
echo "  提交:    ${COMMIT_MSG}"
echo "  状态:    ✅ 成功"
echo "========================================"
