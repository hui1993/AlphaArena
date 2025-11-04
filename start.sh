#!/bin/bash

# ============================================================================
# Alpha Arena - DeepSeek-V3 Trading Bot 启动脚本
# ============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 打印分隔线
print_separator() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 打印标题
print_title() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${WHITE}🏆 Alpha Arena - DeepSeek-V3 Trading Bot${NC}         ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 打印步骤
print_step() {
    echo -e "${BLUE}[步骤]${NC} $1"
}

# 打印成功
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 打印警告
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 打印错误
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# ============================================================================
# 主程序
# ============================================================================

print_title

# 步骤1: 检查 Python
print_step "检查 Python 环境..."
if ! command -v python &> /dev/null; then
    print_error "Python 未安装，请先安装 Python 3"
    exit 1
fi
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_success "Python 已安装 (版本: $PYTHON_VERSION)"

# 步骤2: 检查依赖 (已跳过)
# print_step "检查并安装依赖..."
# if pip install -r requirements.txt -q; then
#     print_success "依赖检查完成"
# else
#     print_warning "依赖安装可能有问题，但继续启动..."
# fi

# 步骤3: 检查配置文件
print_step "检查配置文件..."
if [ ! -f ".env" ]; then
    print_error "配置文件 .env 不存在"
    exit 1
fi
print_success "配置文件存在"

# 步骤4: 创建日志目录
print_step "准备日志目录..."
mkdir -p logs
print_success "日志目录已准备"

# 步骤5: 检查并终止已运行的进程
print_step "检查运行中的进程..."

# 检查并终止 Bot 进程
RUNNING_BOT_PIDS=$(pgrep -f "python.*alpha_arena_bot.py" 2>/dev/null)
if [ -n "$RUNNING_BOT_PIDS" ]; then
    print_warning "检测到运行中的 Bot 进程 (PIDs: $RUNNING_BOT_PIDS)"
    echo "  正在终止旧进程..."
    
    # 优雅终止（SIGTERM）
    pkill -f "python.*alpha_arena_bot.py" 2>/dev/null
    sleep 2
    
    # 检查是否还有残留进程
    if pgrep -f "python.*alpha_arena_bot.py" > /dev/null; then
        print_warning "仍有进程残留，强制终止..."
        pkill -9 -f "python.*alpha_arena_bot.py" 2>/dev/null
        sleep 1
    fi
    
    # 最终验证
    if pgrep -f "python.*alpha_arena_bot.py" > /dev/null; then
        print_error "无法终止 Bot 进程，请手动检查"
        exit 1
    else
        print_success "Bot 旧进程已终止"
    fi
else
    print_success "没有运行中的 Bot 进程"
fi

# 检查并终止 Web Dashboard 进程
RUNNING_DASHBOARD_PIDS=$(pgrep -f "python.*web_dashboard.py" 2>/dev/null)
if [ -n "$RUNNING_DASHBOARD_PIDS" ]; then
    print_warning "检测到运行中的 Web Dashboard 进程 (PIDs: $RUNNING_DASHBOARD_PIDS)"
    echo "  正在终止旧进程..."
    
    # 优雅终止（SIGTERM）
    pkill -f "python.*web_dashboard.py" 2>/dev/null
    sleep 2
    
    # 检查是否还有残留进程
    if pgrep -f "python.*web_dashboard.py" > /dev/null; then
        print_warning "仍有进程残留，强制终止..."
        pkill -9 -f "python.*web_dashboard.py" 2>/dev/null
        sleep 1
    fi
    
    # 最终验证
    if pgrep -f "python.*web_dashboard.py" > /dev/null; then
        print_warning "无法完全终止 Web Dashboard 进程，但继续启动..."
    else
        print_success "Web Dashboard 旧进程已终止"
    fi
else
    print_success "没有运行中的 Web Dashboard 进程"
fi

echo ""

# 步骤6: 启动机器人
print_step "启动 Alpha Arena Bot..."

# 生成日志文件名（按日期，和主日志命名规则一致）
LOG_DATE=$(date +%Y%m%d)
LOG_TIMESTAMP=$(date +%Y-%m-%d\ %H:%M:%S)
LAUNCH_LOG="logs/alpha_arena_launch_${LOG_DATE}.log"
TRADE_LOG="logs/alpha_arena_${LOG_DATE}.log"

# 在启动日志中写入启动分隔符（追加模式，不会覆盖之前的日志）
{
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "🚀 启动 Alpha Arena Bot - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
} >> "$LAUNCH_LOG"

# 使用后台运行，输出追加到日志文件（不会覆盖之前的日志）
# 注意：日志文件中的ANSI颜色代码会在查看时自动过滤（通过less -R或去除）
python alpha_arena_bot.py >> "$LAUNCH_LOG" 2>&1 &
BOT_PID=$!

# 等待3秒让进程启动
sleep 3

# 验证进程是否成功启动
if ps -p $BOT_PID > /dev/null 2>&1; then
    print_separator
    echo -e "${GREEN}✓ Alpha Arena Bot 启动成功${NC}"
    echo ""
    echo -e "  ${CYAN}进程ID:${NC}   $BOT_PID"
    echo -e "  ${CYAN}启动时间:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "  ${CYAN}启动日志:${NC} $LAUNCH_LOG ${YELLOW}(追加模式，不会覆盖)${NC}"
    echo -e "  ${CYAN}交易日志:${NC} $TRADE_LOG"
    echo ""
    print_separator
    echo ""
    echo -e "${BLUE}常用命令:${NC}"
    echo ""
    echo -e "  ${WHITE}查看启动日志 (无颜色码):${NC}"
    echo -e "    ${CYAN}tail -f $LAUNCH_LOG | sed 's/\x1b\[[0-9;]*m//g'${NC}"
    echo ""
    echo -e "  ${WHITE}查看交易日志 (无颜色码):${NC}"
    echo -e "    ${CYAN}tail -f $TRADE_LOG | sed 's/\x1b\[[0-9;]*m//g'${NC}"
    echo ""
    echo -e "  ${WHITE}查看进程状态:${NC}"
    echo -e "    ${CYAN}ps aux | grep alpha_arena_bot${NC}"
    echo ""
    echo -e "  ${WHITE}停止机器人:${NC}"
    echo -e "    ${CYAN}pkill -f 'python.*alpha_arena_bot.py'${NC}"
    echo ""
else
    print_error "启动失败，请检查日志: $LAUNCH_LOG"
    if [ -f "$LAUNCH_LOG" ]; then
        echo ""
        echo "最近的错误信息:"
        tail -n 20 "$LAUNCH_LOG"
    fi
    exit 1
fi

echo ""

# 步骤7: 启动 Web Dashboard
print_step "启动 Web Dashboard..."

# 生成 Dashboard 日志文件名
DASHBOARD_LOG="logs/web_dashboard_${LOG_DATE}.log"

# 在启动日志中写入启动分隔符
{
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "🌐 启动 Web Dashboard - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
} >> "$DASHBOARD_LOG"

# 使用 nohup 后台运行 Web Dashboard
nohup python web_dashboard.py >> "$DASHBOARD_LOG" 2>&1 &
DASHBOARD_PID=$!

# 等待3秒让进程启动
sleep 3

# 验证进程是否成功启动
if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    print_separator
    echo -e "${GREEN}✓ Web Dashboard 启动成功${NC}"
    echo ""
    echo -e "  ${CYAN}进程ID:${NC}   $DASHBOARD_PID"
    echo -e "  ${CYAN}启动时间:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "  ${CYAN}访问地址:${NC} ${YELLOW}http://localhost:5002${NC}"
    echo -e "  ${CYAN}日志文件:${NC} $DASHBOARD_LOG"
    echo ""
    print_separator
    echo ""
    echo -e "${BLUE}常用命令:${NC}"
    echo ""
    echo -e "  ${WHITE}查看 Dashboard 日志:${NC}"
    echo -e "    ${CYAN}tail -f $DASHBOARD_LOG${NC}"
    echo ""
    echo -e "  ${WHITE}停止 Dashboard:${NC}"
    echo -e "    ${CYAN}pkill -f 'python.*web_dashboard.py'${NC}"
    echo ""
else
    print_warning "Web Dashboard 启动可能失败，请检查日志: $DASHBOARD_LOG"
    if [ -f "$DASHBOARD_LOG" ]; then
        echo ""
        echo "最近的错误信息:"
        tail -n 20 "$DASHBOARD_LOG"
    fi
    echo ""
    echo -e "${YELLOW}⚠️  Bot 已启动，但 Dashboard 启动失败，可以稍后手动启动:${NC}"
    echo -e "    ${CYAN}python web_dashboard.py${NC}"
fi
