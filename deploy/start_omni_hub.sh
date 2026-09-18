#!/usr/bin/env bash
# =============================================================================
# OMNI-HUB v12.0 — OS Runtime Activation Script
# =============================================================================
# 用途: 启动 OMNI-HUB v12.0 运行场
# 用法: chmod +x start_omni_hub.sh && ./start_omni_hub.sh [options]
# =============================================================================

set -euo pipefail

# --- 配置 -------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OMNI_HOME="$(cd "${SCRIPT_DIR}/.." && pwd)"
OMNI_CORE="${OMNI_HOME}/core"
OMNI_HUB="${OMNI_HOME}/hub"
OMNI_LOG_DIR="${OMNI_LOG_DIR:-${OMNI_HOME}/logs}"
OMNI_STATE_DIR="${OMNI_STATE_DIR:-${OMNI_HOME}/state}"
OMNI_PID_FILE="${OMNI_STATE_DIR}/omni-hub.pid"
OMNI_MODE="${OMNI_MODE:-production}"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $(date '+%Y-%m-%d %H:%M:%S') $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $(date '+%Y-%m-%d %H:%M:%S') $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $(date '+%Y-%m-%d %H:%M:%S') $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }
log_banner(){ echo -e "${CYAN}$*${NC}"; }

# --- 用法 -------------------------------------------------------------------
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

OMNI-HUB v12.0 OS Runtime Activation Script

OPTIONS:
    -m, --mode MODE       运行模式: development|production|debug (默认: production)
    -d, --daemon          后台运行
    -s, --stop            停止运行
    -r, --restart         重启
    -l, --logs            查看日志
    -c, --check           健康检查
    -h, --help            显示此帮助

EXAMPLES:
    $(basename "$0")                    # 前台运行
    $(basename "$0") -d                 # 后台运行
    $(basename "$0") -m debug           # Debug模式
    $(basename "$0") -s                 # 停止
    $(basename "$0") -r                 # 重启
EOF
}

# --- 参数解析 ---------------------------------------------------------------
DAEMON=false
STOP=false
RESTART=false
LOGS=false
CHECK=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--mode)     OMNI_MODE="$2"; shift 2 ;;
        -d|--daemon)   DAEMON=true; shift ;;
        -s|--stop)     STOP=true; shift ;;
        -r|--restart)  RESTART=true; shift ;;
        -l|--logs)     LOGS=true; shift ;;
        -c|--check)    CHECK=true; shift ;;
        -h|--help)     usage; exit 0 ;;
        *)             log_err "未知参数: $1"; usage; exit 1 ;;
    esac
done

# --- 停止 -------------------------------------------------------------------
if [ "$STOP" = true ] || [ "$RESTART" = true ]; then
    if [ -f "$OMNI_PID_FILE" ]; then
        PID=$(cat "$OMNI_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_info "停止 OMNI-HUB (PID: $PID)..."
            kill "$PID" || true
            sleep 2
            if kill -0 "$PID" 2>/dev/null; then
                log_warn "强制终止..."
                kill -9 "$PID" || true
            fi
            rm -f "$OMNI_PID_FILE"
            log_ok "OMNI-HUB 已停止"
        else
            log_warn "进程不存在，清理 PID 文件"
            rm -f "$OMNI_PID_FILE"
        fi
    else
        log_warn "未找到 PID 文件"
    fi
    [ "$STOP" = true ] && exit 0
fi

# --- 查看日志 ---------------------------------------------------------------
if [ "$LOGS" = true ]; then
    LOG_FILE="${OMNI_LOG_DIR}/omni_hub_$(date +%Y%m%d).log"
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        log_err "日志文件不存在: $LOG_FILE"
        exit 1
    fi
    exit 0
fi

# --- 健康检查 ---------------------------------------------------------------
if [ "$CHECK" = true ]; then
    if [ -f "$OMNI_PID_FILE" ]; then
        PID=$(cat "$OMNI_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_ok "OMNI-HUB 运行中 (PID: $PID)"
            # 尝试检查Python进程
            ps -p "$PID" -o pid,ppid,cmd | tail -n +2
            exit 0
        else
            log_err "OMNI-HUB 未运行 (PID文件存在但进程不存在)"
            rm -f "$OMNI_PID_FILE"
            exit 1
        fi
    else
        log_err "OMNI-HUB 未运行"
        exit 1
    fi
fi

# --- 前置检查 ---------------------------------------------------------------
log_banner "========================================"
log_banner "  OMNI-HUB v12.0 — OS Runtime Activation"
log_banner "  UNITY E=7641.82 | 11-line SI | 92 Modules"
log_banner "========================================"

# Python检查
if ! command -v python3 &>/dev/null; then
    log_err "python3 未安装"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log_ok "Python: $PYTHON_VERSION"

# 目录检查
mkdir -p "$OMNI_LOG_DIR" "$OMNI_STATE_DIR"
log_ok "日志目录: $OMNI_LOG_DIR"
log_ok "状态目录: $OMNI_STATE_DIR"

# core目录检查
if [ ! -d "$OMNI_CORE" ]; then
    log_err "core 目录不存在: $OMNI_CORE"
    exit 1
fi
MODULE_COUNT=$(find "$OMNI_CORE" -name "*.py" -not -path "*/__pycache__/*" | wc -l)
log_ok "核心模块: $MODULE_COUNT Python files"

# 环境文件
if [ -f "${SCRIPT_DIR}/.env" ]; then
    log_ok "环境配置: ${SCRIPT_DIR}/.env"
    set -a
    # shellcheck source=/dev/null
    source "${SCRIPT_DIR}/.env"
    set +a
else
    log_warn "未找到 .env 文件，使用默认配置"
fi

# --- 依赖检查 ---------------------------------------------------------------
log_info "检查 Python 依赖..."
python3 -c "import numpy" 2>/dev/null && log_ok "numpy" || log_warn "numpy 未安装"
python3 -c "import scipy" 2>/dev/null && log_ok "scipy" || log_warn "scipy 未安装"
python3 -c "import sympy" 2>/dev/null && log_ok "sympy" || log_warn "sympy 未安装"
python3 -c "import matplotlib" 2>/dev/null && log_ok "matplotlib" || log_warn "matplotlib 未安装"

# --- 启动 -------------------------------------------------------------------
export PYTHONPATH="${OMNI_CORE}:${PYTHONPATH:-}"
export OMNI_HUB_HOME="$OMNI_HOME"
export OMNI_HUB_LOG_DIR="$OMNI_LOG_DIR"
export OMNI_HUB_STATE_DIR="$OMNI_STATE_DIR"
export OMNI_HUB_MODE="$OMNI_MODE"

RUN_CMD="python3 ${OMNI_HOME}/run_omni_hub.py --mode ${OMNI_MODE}"
log_info "启动命令: $RUN_CMD"
log_info "运行模式: $OMNI_MODE"

if [ "$DAEMON" = true ]; then
    log_info "后台运行模式..."
    nohup $RUN_CMD > "${OMNI_LOG_DIR}/omni_hub_$(date +%Y%m%d).log" 2>&1 &
    PID=$!
    echo $PID > "$OMNI_PID_FILE"
    sleep 2
    if kill -0 "$PID" 2>/dev/null; then
        log_ok "OMNI-HUB 已启动 (PID: $PID)"
        log_info "日志: tail -f ${OMNI_LOG_DIR}/omni_hub_$(date +%Y%m%d).log"
        log_info "停止: $(basename "$0") -s"
    else
        log_err "启动失败，请检查日志"
        rm -f "$OMNI_PID_FILE"
        exit 1
    fi
else
    log_info "前台运行模式 (Ctrl+C 停止)..."
    log_info "========================================"
    $RUN_CMD
fi
