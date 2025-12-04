#!/bin/bash

# ============================================================================
# Alpha Arena - DeepSeek-V3 Trading Bot 停止脚本
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
    echo -e "${CYAN}║${NC}  ${WHITE}🛑 Alpha Arena - 停止所有进程${NC}                    ${CYAN}║${NC}"
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

# 打印信息
print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# 停止进程函数
stop_process() {
    local pattern=$1
    local name=$2
    
    print_step "检查 $name 进程..."
    
    # 查找进程
    local pids=$(pgrep -f "$pattern" 2>/dev/null)
    
    if [ -z "$pids" ]; then
        print_success "没有运行中的 $name 进程"
        return 0
    fi
    
    # 显示找到的进程
    print_info "找到 $name 进程 (PIDs: $pids)"
    
    # 优雅终止（SIGTERM）
    print_info "正在优雅终止 $name 进程..."
    pkill -f "$pattern" 2>/dev/null
    
    # 等待进程退出
    local wait_count=0
    local max_wait=5
    
    while [ $wait_count -lt $max_wait ]; do
        if ! pgrep -f "$pattern" > /dev/null 2>&1; then
            print_success "$name 进程已优雅终止"
            return 0
        fi
        sleep 1
        wait_count=$((wait_count + 1))
    done
    
    # 如果还有残留进程，强制终止
    if pgrep -f "$pattern" > /dev/null 2>&1; then
        print_warning "$name 进程未响应，强制终止..."
        pkill -9 -f "$pattern" 2>/dev/null
        sleep 1
        
        # 最终验证
        if pgrep -f "$pattern" > /dev/null 2>&1; then
            print_error "无法终止 $name 进程，请手动检查"
            return 1
        else
            print_success "$name 进程已强制终止"
            return 0
        fi
    fi
    
    return 0
}

# ============================================================================
# 主程序
# ============================================================================

print_title

# 检查并停止 Bot 进程
stop_process "python.*alpha_arena_bot.py" "Alpha Arena Bot"

echo ""

# 检查并停止 Web Dashboard 进程
stop_process "python.*web_dashboard.py" "Web Dashboard"

echo ""

# 最终检查
print_step "最终检查所有相关进程..."

BOT_PIDS=$(pgrep -f "python.*alpha_arena_bot.py" 2>/dev/null)
DASHBOARD_PIDS=$(pgrep -f "python.*web_dashboard.py" 2>/dev/null)

if [ -z "$BOT_PIDS" ] && [ -z "$DASHBOARD_PIDS" ]; then
    print_separator
    echo -e "${GREEN}✓ 所有进程已成功停止${NC}"
    echo ""
    print_success "Alpha Arena Bot: 已停止"
    print_success "Web Dashboard: 已停止"
    echo ""
    print_separator
    exit 0
else
    print_separator
    echo -e "${YELLOW}⚠ 仍有进程在运行:${NC}"
    echo ""
    if [ -n "$BOT_PIDS" ]; then
        print_warning "Alpha Arena Bot 进程仍在运行 (PIDs: $BOT_PIDS)"
    fi
    if [ -n "$DASHBOARD_PIDS" ]; then
        print_warning "Web Dashboard 进程仍在运行 (PIDs: $DASHBOARD_PIDS)"
    fi
    echo ""
    echo -e "${YELLOW}可以手动终止:${NC}"
    if [ -n "$BOT_PIDS" ]; then
        echo -e "  ${CYAN}pkill -9 -f 'python.*alpha_arena_bot.py'${NC}"
    fi
    if [ -n "$DASHBOARD_PIDS" ]; then
        echo -e "  ${CYAN}pkill -9 -f 'python.*web_dashboard.py'${NC}"
    fi
    echo ""
    print_separator
    exit 1
fi

