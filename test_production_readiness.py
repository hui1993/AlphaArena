#!/usr/bin/env python3
"""
生产环境就绪性测试 - V3.5
全面测试浮盈滚仓和移动止盈止损功能
"""

import sys
from rolling_position_manager import RollingPositionManager
import time

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_test(name, passed, details=""):
    """打印测试结果"""
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"     {Colors.YELLOW}{details}{Colors.RESET}")

def test_rolling_manager_initialization():
    """测试1: 滚仓管理器初始化"""
    print_header("测试1: 滚仓管理器初始化")

    try:
        # 测试默认参数
        manager1 = RollingPositionManager()
        test1 = (manager1.profit_threshold_pct == 3.0 and
                manager1.roll_ratio == 0.5 and
                manager1.max_rolls == 2)
        print_test("默认参数初始化", test1,
                  f"阈值:{manager1.profit_threshold_pct}%, 比例:{manager1.roll_ratio}, 最大次数:{manager1.max_rolls}")

        # 测试自定义参数
        manager2 = RollingPositionManager(
            profit_threshold_pct=1.5,
            roll_ratio=0.6,
            max_rolls=3,
            min_roll_interval_minutes=3
        )
        test2 = (manager2.profit_threshold_pct == 1.5 and
                manager2.roll_ratio == 0.6 and
                manager2.max_rolls == 3 and
                manager2.min_roll_interval_minutes == 3)
        print_test("自定义参数初始化", test2,
                  f"阈值:{manager2.profit_threshold_pct}%, 比例:{manager2.roll_ratio}, 最大次数:{manager2.max_rolls}")

        # 测试历史记录初始化
        test3 = len(manager1.roll_history) == 0
        print_test("滚仓历史初始化为空", test3)

        return test1 and test2 and test3
    except Exception as e:
        print_test("初始化测试", False, f"异常: {e}")
        return False

def test_profit_threshold_logic():
    """测试2: 盈利阈值逻辑"""
    print_header("测试2: 盈利阈值逻辑")

    manager = RollingPositionManager(profit_threshold_pct=1.5)

    # 场景1: 盈利低于阈值
    pos1 = {'symbol': 'BTCUSDT', 'pnl_pct': 1.0, 'quantity': 0.1, 'entry_price': 50000, 'side': 'LONG'}
    should_roll1, reason1, qty1 = manager.should_roll_position(pos1)
    test1 = (not should_roll1 and "未达到" in reason1)
    print_test("盈利1.0% < 1.5%阈值 → 不触发", test1, reason1)

    # 场景2: 盈利刚好达到阈值
    pos2 = {'symbol': 'BTCUSDT', 'pnl_pct': 1.5, 'quantity': 0.1, 'entry_price': 50000, 'side': 'LONG'}
    should_roll2, reason2, qty2 = manager.should_roll_position(pos2)
    test2 = should_roll2
    print_test("盈利1.5% = 1.5%阈值 → 触发", test2, reason2)

    # 场景3: 盈利远超阈值
    pos3 = {'symbol': 'ETHUSDT', 'pnl_pct': 5.0, 'quantity': 1.0, 'entry_price': 3000, 'side': 'LONG'}
    should_roll3, reason3, qty3 = manager.should_roll_position(pos3)
    test3 = should_roll3
    print_test("盈利5.0% > 1.5%阈值 → 触发", test3, reason3)

    # 场景4: 亏损
    pos4 = {'symbol': 'BTCUSDT', 'pnl_pct': -1.0, 'quantity': 0.1, 'entry_price': 50000, 'side': 'LONG'}
    should_roll4, reason4, qty4 = manager.should_roll_position(pos4)
    test4 = (not should_roll4 and "未达到" in reason4)
    print_test("盈利-1.0% < 1.5%阈值 (亏损) → 不触发", test4, reason4)

    return test1 and test2 and test3 and test4

def test_max_rolls_limit():
    """测试3: 最大滚仓次数限制"""
    print_header("测试3: 最大滚仓次数限制")

    manager = RollingPositionManager(
        profit_threshold_pct=1.5,
        max_rolls=2,
        min_roll_interval_minutes=0.01  # 0.6秒间隔,方便测试
    )
    position = {'symbol': 'BTCUSDT', 'pnl_pct': 3.0, 'quantity': 0.1, 'entry_price': 50000, 'side': 'LONG'}

    # 第1次滚仓
    should_roll1, reason1, _ = manager.should_roll_position(position)
    if should_roll1:
        manager.record_roll('BTCUSDT')
    test1 = should_roll1
    print_test("第1次滚仓 (0/2) → 允许", test1, reason1)

    # 等待时间间隔
    time.sleep(1)

    # 第2次滚仓
    should_roll2, reason2, _ = manager.should_roll_position(position)
    if should_roll2:
        manager.record_roll('BTCUSDT')
    test2 = should_roll2
    print_test("第2次滚仓 (1/2) → 允许", test2, reason2)

    # 等待时间间隔
    time.sleep(1)

    # 第3次滚仓 (应该被拒绝)
    should_roll3, reason3, _ = manager.should_roll_position(position)
    test3 = (not should_roll3 and "最大滚仓次数" in reason3)
    print_test("第3次滚仓 (2/2) → 拒绝", test3, reason3)

    # 验证滚仓记录
    roll_info = manager.get_roll_info('BTCUSDT')
    test4 = roll_info['roll_count'] == 2 and roll_info['remaining_rolls'] == 0
    print_test("滚仓记录准确性", test4,
              f"已滚:{roll_info['roll_count']}, 剩余:{roll_info['remaining_rolls']}")

    return test1 and test2 and test3 and test4

def test_time_interval_check():
    """测试4: 时间间隔检查"""
    print_header("测试4: 滚仓时间间隔检查")

    manager = RollingPositionManager(
        profit_threshold_pct=1.5,
        max_rolls=3,
        min_roll_interval_minutes=0.05  # 3秒 (测试用)
    )
    position = {'symbol': 'ETHUSDT', 'pnl_pct': 3.0, 'quantity': 1.0, 'entry_price': 3000, 'side': 'LONG'}

    # 第1次滚仓
    should_roll1, reason1, _ = manager.should_roll_position(position)
    if should_roll1:
        manager.record_roll('ETHUSDT')
        roll_time1 = time.time()
    test1 = should_roll1
    print_test("第1次滚仓 → 允许", test1)

    # 立即尝试第2次滚仓 (应该被时间间隔拒绝)
    should_roll2, reason2, _ = manager.should_roll_position(position)
    test2 = (not should_roll2 and "时间过短" in reason2)
    print_test("立即第2次滚仓 (间隔<3秒) → 拒绝", test2, reason2)

    # 等待时间间隔
    print(f"     {Colors.BLUE}⏳ 等待3秒时间间隔...{Colors.RESET}")
    time.sleep(3.5)

    # 再次尝试第2次滚仓 (应该允许)
    should_roll3, reason3, _ = manager.should_roll_position(position)
    if should_roll3:
        manager.record_roll('ETHUSDT')
    test3 = should_roll3
    print_test("等待后第2次滚仓 (间隔>3秒) → 允许", test3, reason3)

    return test1 and test2 and test3

def test_roll_quantity_calculation():
    """测试5: 加仓数量计算"""
    print_header("测试5: 加仓数量计算准确性")

    manager = RollingPositionManager(profit_threshold_pct=1.5, roll_ratio=0.5)

    # 多头仓位
    pos_long = {'symbol': 'BTCUSDT', 'pnl_pct': 3.0, 'quantity': 0.1, 'entry_price': 50000, 'side': 'LONG'}
    should_roll1, reason1, qty1 = manager.should_roll_position(pos_long)
    expected_qty1 = 0.1 * 0.5
    test1 = abs(qty1 - expected_qty1) < 0.0001
    print_test("多头加仓数量 (0.1 * 50%)", test1,
              f"预期:{expected_qty1:.4f}, 实际:{qty1:.4f}")

    # 空头仓位 (负数)
    pos_short = {'symbol': 'ETHUSDT', 'pnl_pct': 3.0, 'quantity': -2.5, 'entry_price': 3000, 'side': 'SHORT'}
    should_roll2, reason2, qty2 = manager.should_roll_position(pos_short)
    expected_qty2 = 2.5 * 0.5  # 应该返回正数
    test2 = abs(qty2 - expected_qty2) < 0.0001
    print_test("空头加仓数量 (2.5 * 50%)", test2,
              f"预期:{expected_qty2:.4f}, 实际:{qty2:.4f}")

    # 不同加仓比例
    manager2 = RollingPositionManager(profit_threshold_pct=1.5, roll_ratio=0.3)
    should_roll3, reason3, qty3 = manager2.should_roll_position(pos_long)
    expected_qty3 = 0.1 * 0.3
    test3 = abs(qty3 - expected_qty3) < 0.0001
    print_test("30%加仓比例 (0.1 * 30%)", test3,
              f"预期:{expected_qty3:.4f}, 实际:{qty3:.4f}")

    return test1 and test2 and test3

def test_dynamic_stop_loss():
    """测试6: 动态止损计算"""
    print_header("测试6: 动态止损逻辑")

    manager = RollingPositionManager()

    # 场景1: 多头盈利 - 移动止损
    pos1 = {
        'symbol': 'BTCUSDT',
        'entry_price': 50000,
        'side': 'LONG',
        'pnl_pct': 4.0  # 盈利4%
    }
    atr1 = 500
    stop_loss1 = manager.calculate_dynamic_stop_loss(pos1, atr1)
    # 应该保护50%盈利,即2%: 50000 * (1 + 0.02) = 51000
    expected_stop1 = 50000 * 1.02
    test1 = abs(stop_loss1 - expected_stop1) < 10
    print_test("多头盈利4% → 移动止损保护2%", test1,
              f"入场:50000, 止损:{stop_loss1:.2f}, 预期:{expected_stop1:.2f}")

    # 场景2: 空头盈利 - 移动止损
    pos2 = {
        'symbol': 'ETHUSDT',
        'entry_price': 3000,
        'side': 'SHORT',
        'pnl_pct': 6.0  # 盈利6%
    }
    atr2 = 30
    stop_loss2 = manager.calculate_dynamic_stop_loss(pos2, atr2)
    # 应该保护50%盈利,即3%: 3000 * (1 - 0.03) = 2910
    expected_stop2 = 3000 * 0.97
    test2 = abs(stop_loss2 - expected_stop2) < 10
    print_test("空头盈利6% → 移动止损保护3%", test2,
              f"入场:3000, 止损:{stop_loss2:.2f}, 预期:{expected_stop2:.2f}")

    # 场景3: 多头亏损 - ATR止损
    pos3 = {
        'symbol': 'BTCUSDT',
        'entry_price': 50000,
        'side': 'LONG',
        'pnl_pct': -1.0  # 亏损1%
    }
    atr3 = 500
    stop_loss3 = manager.calculate_dynamic_stop_loss(pos3, atr3, base_stop_loss_pct=2.0)
    # ATR止损: 2倍ATR = (500/50000)*200 = 2%, 基础止损2%, 取最大值2%
    # 50000 * (1 - 0.02) = 49000
    expected_stop3 = 50000 * 0.98
    test3 = abs(stop_loss3 - expected_stop3) < 10
    print_test("多头亏损 → ATR止损2%", test3,
              f"入场:50000, 止损:{stop_loss3:.2f}, 预期:{expected_stop3:.2f}")

    # 场景4: 空头亏损 - ATR止损
    pos4 = {
        'symbol': 'ETHUSDT',
        'entry_price': 3000,
        'side': 'SHORT',
        'pnl_pct': -0.5
    }
    atr4 = 30
    stop_loss4 = manager.calculate_dynamic_stop_loss(pos4, atr4, base_stop_loss_pct=2.0)
    # ATR止损: 2倍ATR = (30/3000)*200 = 2%, 基础止损2%, 取最大值2%
    # 3000 * (1 + 0.02) = 3060
    expected_stop4 = 3000 * 1.02
    test4 = abs(stop_loss4 - expected_stop4) < 10
    print_test("空头亏损 → ATR止损2%", test4,
              f"入场:3000, 止损:{stop_loss4:.2f}, 预期:{expected_stop4:.2f}")

    return test1 and test2 and test3 and test4

def test_dynamic_take_profit():
    """测试7: 动态止盈计算"""
    print_header("测试7: 动态止盈逻辑")

    manager = RollingPositionManager(profit_threshold_pct=1.5, max_rolls=2)

    # 场景1: 未滚仓 - 基础止盈5%
    pos1 = {
        'symbol': 'BTCUSDT',
        'entry_price': 50000,
        'side': 'LONG'
    }
    atr1 = 500
    take_profit1 = manager.calculate_dynamic_take_profit(pos1, atr1, base_take_profit_pct=5.0)
    # ATR止盈: 3倍ATR = (500/50000)*300 = 3%, 基础5%, 取最大值5%
    # 50000 * (1 + 0.05) = 52500
    expected_tp1 = 50000 * 1.05
    test1 = abs(take_profit1 - expected_tp1) < 10
    print_test("未滚仓 → 基础止盈5%", test1,
              f"入场:50000, 止盈:{take_profit1:.2f}, 预期:{expected_tp1:.2f}")

    # 场景2: 滚仓1次 - 止盈提高到7%
    manager.record_roll('BTCUSDT')
    take_profit2 = manager.calculate_dynamic_take_profit(pos1, atr1, base_take_profit_pct=5.0)
    # 5% + 2% = 7%
    expected_tp2 = 50000 * 1.07
    test2 = abs(take_profit2 - expected_tp2) < 10
    print_test("滚仓1次 → 止盈提高到7%", test2,
              f"止盈:{take_profit2:.2f}, 预期:{expected_tp2:.2f}")

    # 场景3: 滚仓2次 - 止盈提高到9%
    manager.record_roll('BTCUSDT')
    take_profit3 = manager.calculate_dynamic_take_profit(pos1, atr1, base_take_profit_pct=5.0)
    # 5% + 4% = 9%
    expected_tp3 = 50000 * 1.09
    test3 = abs(take_profit3 - expected_tp3) < 10
    print_test("滚仓2次 → 止盈提高到9%", test3,
              f"止盈:{take_profit3:.2f}, 预期:{expected_tp3:.2f}")

    # 场景4: 空头未滚仓
    pos2 = {
        'symbol': 'ETHUSDT',
        'entry_price': 3000,
        'side': 'SHORT'
    }
    manager2 = RollingPositionManager()
    atr2 = 30
    take_profit4 = manager2.calculate_dynamic_take_profit(pos2, atr2, base_take_profit_pct=5.0)
    # 3000 * (1 - 0.05) = 2850
    expected_tp4 = 3000 * 0.95
    test4 = abs(take_profit4 - expected_tp4) < 10
    print_test("空头未滚仓 → 止盈5%", test4,
              f"入场:3000, 止盈:{take_profit4:.2f}, 预期:{expected_tp4:.2f}")

    return test1 and test2 and test3 and test4

def test_roll_history_management():
    """测试8: 滚仓历史管理"""
    print_header("测试8: 滚仓历史记录管理")

    manager = RollingPositionManager()

    # 测试记录滚仓
    manager.record_roll('BTCUSDT')
    manager.record_roll('BTCUSDT')
    manager.record_roll('ETHUSDT')

    test1 = len(manager.roll_history['BTCUSDT']) == 2
    test2 = len(manager.roll_history['ETHUSDT']) == 1
    print_test("记录多次滚仓", test1 and test2,
              f"BTCUSDT:{len(manager.roll_history['BTCUSDT'])}次, ETHUSDT:{len(manager.roll_history['ETHUSDT'])}次")

    # 测试获取滚仓信息
    info = manager.get_roll_info('BTCUSDT')
    test3 = (info['roll_count'] == 2 and
            info['remaining_rolls'] == 0 and
            not info['can_roll_more'])
    print_test("获取滚仓信息", test3,
              f"已滚:{info['roll_count']}, 剩余:{info['remaining_rolls']}, 可继续:{info['can_roll_more']}")

    # 测试清除历史
    manager.clear_roll_history('BTCUSDT')
    test4 = 'BTCUSDT' not in manager.roll_history
    print_test("清除滚仓历史", test4)

    # 测试未滚仓的交易对
    info2 = manager.get_roll_info('SOLUSDT')
    test5 = (info2['roll_count'] == 0 and
            info2['remaining_rolls'] == 2 and
            info2['can_roll_more'])
    print_test("未滚仓交易对信息", test5,
              f"已滚:{info2['roll_count']}, 剩余:{info2['remaining_rolls']}")

    return test1 and test2 and test3 and test4 and test5

def test_edge_cases():
    """测试9: 边界条件和异常处理"""
    print_header("测试9: 边界条件和异常情况")

    manager = RollingPositionManager(profit_threshold_pct=1.5)

    # 测试1: 零持仓量
    pos1 = {'symbol': 'BTCUSDT', 'pnl_pct': 3.0, 'quantity': 0, 'entry_price': 50000, 'side': 'LONG'}
    should_roll1, reason1, qty1 = manager.should_roll_position(pos1)
    test1 = qty1 == 0
    print_test("零持仓量 → 加仓量为0", test1, f"加仓量:{qty1}")

    # 测试2: 极小持仓量
    pos2 = {'symbol': 'BTCUSDT', 'pnl_pct': 3.0, 'quantity': 0.001, 'entry_price': 50000, 'side': 'LONG'}
    should_roll2, reason2, qty2 = manager.should_roll_position(pos2)
    expected_qty2 = 0.001 * 0.5
    test2 = abs(qty2 - expected_qty2) < 0.00001
    print_test("极小持仓量 (0.001)", test2, f"加仓量:{qty2:.6f}")

    # 测试3: 极大持仓量
    pos3 = {'symbol': 'BTCUSDT', 'pnl_pct': 3.0, 'quantity': 1000.0, 'entry_price': 50000, 'side': 'LONG'}
    should_roll3, reason3, qty3 = manager.should_roll_position(pos3)
    expected_qty3 = 1000.0 * 0.5
    test3 = abs(qty3 - expected_qty3) < 0.01
    print_test("极大持仓量 (1000.0)", test3, f"加仓量:{qty3:.2f}")

    # 测试4: 盈利刚好等于阈值
    pos4 = {'symbol': 'BTCUSDT', 'pnl_pct': 1.5, 'quantity': 0.1, 'entry_price': 50000, 'side': 'LONG'}
    should_roll4, reason4, qty4 = manager.should_roll_position(pos4)
    test4 = should_roll4
    print_test("盈利刚好等于阈值 (1.5%)", test4, "应该触发滚仓")

    # 测试5: 盈利略低于阈值
    pos5 = {'symbol': 'BTCUSDT', 'pnl_pct': 1.49, 'quantity': 0.1, 'entry_price': 50000, 'side': 'LONG'}
    should_roll5, reason5, qty5 = manager.should_roll_position(pos5)
    test5 = not should_roll5
    print_test("盈利略低于阈值 (1.49%)", test5, "不应该触发滚仓")

    # 测试6: 极高盈利
    pos6 = {'symbol': 'BTCUSDT', 'pnl_pct': 50.0, 'quantity': 0.1, 'entry_price': 50000, 'side': 'LONG'}
    should_roll6, reason6, qty6 = manager.should_roll_position(pos6)
    test6 = should_roll6 and qty6 > 0
    print_test("极高盈利 (50%)", test6, f"触发滚仓,加仓量:{qty6:.4f}")

    # 测试7: 负数持仓量(空头)
    pos7 = {'symbol': 'ETHUSDT', 'pnl_pct': 3.0, 'quantity': -5.0, 'entry_price': 3000, 'side': 'SHORT'}
    should_roll7, reason7, qty7 = manager.should_roll_position(pos7)
    test7 = qty7 > 0  # 应该返回正数
    print_test("空头仓位 (-5.0) → 返回正数加仓量", test7, f"加仓量:{qty7:.2f}")

    return test1 and test2 and test3 and test4 and test5 and test6 and test7

def test_production_scenario():
    """测试10: 生产环境模拟场景"""
    print_header("测试10: 生产环境完整场景模拟")

    manager = RollingPositionManager(
        profit_threshold_pct=1.5,
        roll_ratio=0.5,
        max_rolls=2,
        min_roll_interval_minutes=0.05  # 3秒用于测试 (生产环境是3分钟)
    )

    print(f"{Colors.BLUE}模拟场景: SOL多单从开仓到平仓的完整生命周期{Colors.RESET}\n")

    # 阶段1: 开仓
    print(f"  {Colors.CYAN}阶段1: 开仓 SOLUSDT @ 190.00{Colors.RESET}")
    position = {
        'symbol': 'SOLUSDT',
        'pnl_pct': 0.0,
        'quantity': 2.0,
        'entry_price': 190.0,
        'side': 'LONG'
    }

    # 阶段2: 盈利0.8% (未达阈值)
    print(f"  {Colors.CYAN}阶段2: 价格上涨到191.52, 盈利0.8%{Colors.RESET}")
    position['pnl_pct'] = 0.8
    should_roll1, reason1, _ = manager.should_roll_position(position)
    test1 = not should_roll1
    print_test("  盈利0.8% < 1.5% → 不触发", test1)

    # 阶段3: 盈利1.6% (达到阈值,第1次滚仓)
    print(f"  {Colors.CYAN}阶段3: 价格上涨到193.04, 盈利1.6%{Colors.RESET}")
    position['pnl_pct'] = 1.6
    should_roll2, reason2, qty2 = manager.should_roll_position(position)
    test2 = should_roll2 and qty2 == 1.0
    print_test("  盈利1.6% > 1.5% → 第1次滚仓", test2, f"加仓1.0个SOL")
    if should_roll2:
        manager.record_roll('SOLUSDT')
        position['quantity'] = 3.0  # 更新持仓量

    # 等待时间间隔
    print(f"     {Colors.BLUE}⏳ 等待3秒时间间隔...{Colors.RESET}")
    time.sleep(3.5)

    # 阶段4: 继续上涨,盈利2.5% (第2次滚仓)
    print(f"  {Colors.CYAN}阶段4: 价格继续上涨到194.75, 盈利2.5%{Colors.RESET}")
    position['pnl_pct'] = 2.5
    should_roll3, reason3, qty3 = manager.should_roll_position(position)
    test3 = should_roll3 and qty3 == 1.5
    print_test("  盈利2.5% > 1.5% → 第2次滚仓", test3, f"加仓1.5个SOL")
    if should_roll3:
        manager.record_roll('SOLUSDT')
        position['quantity'] = 4.5  # 更新持仓量

    # 阶段5: 到达止盈点 (平仓前检查)
    print(f"  {Colors.CYAN}阶段5: 价格到达199.50, 盈利5.0% (接近止盈){Colors.RESET}")
    position['pnl_pct'] = 5.0
    should_roll4, reason4, _ = manager.should_roll_position(position)
    test4 = not should_roll4 and "最大滚仓次数" in reason4
    print_test("  已滚仓2次,不能再滚 → 准备平仓", test4, reason4)

    # 阶段6: 平仓并清除历史
    print(f"  {Colors.CYAN}阶段6: 平仓 SOLUSDT @ 199.50{Colors.RESET}")
    manager.clear_roll_history('SOLUSDT')
    info = manager.get_roll_info('SOLUSDT')
    test5 = info['roll_count'] == 0
    print_test("  平仓后清除滚仓历史", test5)

    # 计算最终收益
    initial_value = 2.0 * 190.0  # 初始价值: 380 USDT
    after_roll1 = 3.0 * 193.04  # 第1次滚仓后: 579.12 USDT (投入579.12)
    after_roll2 = 4.5 * 194.75  # 第2次滚仓后: 876.375 USDT (投入876.375)
    final_value = 4.5 * 199.50  # 最终价值: 897.75 USDT

    total_invested = 380 + (1.0 * 193.04) + (1.5 * 194.75)  # 总投入: 665.165 USDT
    profit = final_value - total_invested  # 盈利: 232.585 USDT
    roi = (profit / total_invested) * 100  # ROI: 34.97%

    print(f"\n  {Colors.GREEN}📊 最终结果:{Colors.RESET}")
    print(f"     总投入: {total_invested:.2f} USDT")
    print(f"     最终价值: {final_value:.2f} USDT")
    print(f"     盈利: {profit:.2f} USDT")
    print(f"     ROI: {roi:.2f}%")
    print(f"     滚仓放大倍数: {(4.5/2.0):.2f}x")

    return test1 and test2 and test3 and test4 and test5

def main():
    """运行所有测试"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║          Alpha Arena V3.5 - 生产环境就绪性测试套件              ║")
    print("║                                                                  ║")
    print("║              浮盈滚仓 + 移动止盈止损功能验证                     ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)

    test_results = []

    # 运行所有测试
    test_results.append(("滚仓管理器初始化", test_rolling_manager_initialization()))
    test_results.append(("盈利阈值逻辑", test_profit_threshold_logic()))
    test_results.append(("最大滚仓次数限制", test_max_rolls_limit()))
    test_results.append(("时间间隔检查", test_time_interval_check()))
    test_results.append(("加仓数量计算", test_roll_quantity_calculation()))
    test_results.append(("动态止损逻辑", test_dynamic_stop_loss()))
    test_results.append(("动态止盈逻辑", test_dynamic_take_profit()))
    test_results.append(("滚仓历史管理", test_roll_history_management()))
    test_results.append(("边界条件处理", test_edge_cases()))
    test_results.append(("生产环境模拟", test_production_scenario()))

    # 统计结果
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    # 打印总结
    print_header("测试总结")
    for name, result in test_results:
        status = f"{Colors.GREEN}✅{Colors.RESET}" if result else f"{Colors.RED}❌{Colors.RESET}"
        print(f"{status} {name}")

    print(f"\n{Colors.BOLD}总体结果: {passed}/{total} 通过{Colors.RESET}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过! 系统已准备好用于生产环境!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  有 {total-passed} 个测试失败,请修复后再部署到生产环境{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
