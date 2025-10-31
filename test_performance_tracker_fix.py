#!/usr/bin/env python3
"""
测试 performance_tracker.py 的 None 值修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from performance_tracker import PerformanceTracker
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_none_value_handling():
    """测试 None 值处理"""
    print("🧪 测试 performance_tracker.py 的 None 值修复...")
    
    # 创建性能跟踪器
    tracker = PerformanceTracker(initial_capital=1000)
    
    # 测试1: 记录包含 None 值的交易
    print("\n📝 测试1: 记录包含 None 值的交易...")
    problematic_trade = {
        'symbol': 'BTCUSDT',
        'action': 'BUY',
        'quantity': None,  # None 值
        'price': 50000,
        'leverage': 10
    }
    
    try:
        tracker.record_trade(problematic_trade)
        print("✅ 成功记录包含 None 值的交易")
    except Exception as e:
        print(f"❌ 记录交易失败: {e}")
    
    # 测试2: 记录正常的交易
    print("\n📝 测试2: 记录正常交易...")
    normal_trade = {
        'symbol': 'ETHUSDT',
        'action': 'OPEN_LONG',
        'quantity': 0.1,
        'price': 3000,
        'leverage': 5
    }
    
    try:
        tracker.record_trade(normal_trade)
        print("✅ 成功记录正常交易")
    except Exception as e:
        print(f"❌ 记录正常交易失败: {e}")
    
    # 测试3: 测试手续费计算（包含 None 值）
    print("\n💰 测试3: 测试手续费计算...")
    try:
        total_fees = tracker._calculate_total_fees()
        print(f"✅ 手续费计算成功: ${total_fees:.2f}")
    except Exception as e:
        print(f"❌ 手续费计算失败: {e}")
    
    # 测试4: 测试平仓记录（包含 None 值）
    print("\n📊 测试4: 测试平仓记录...")
    try:
        # 尝试平仓一个不存在的交易
        pnl = tracker.record_trade_close('BTCUSDT', 51000, {})
        print(f"✅ 平仓记录成功: ${pnl:.2f}")
    except Exception as e:
        print(f"❌ 平仓记录失败: {e}")
    
    # 测试5: 测试性能指标计算
    print("\n📈 测试5: 测试性能指标计算...")
    try:
        metrics = tracker.calculate_metrics()
        print(f"✅ 性能指标计算成功:")
        print(f"   - 总收益: ${metrics.get('total_return', 0):.2f}")
        print(f"   - 收益率: {metrics.get('return_pct', 0):.2f}%")
        print(f"   - 交易次数: {metrics.get('total_trades', 0)}")
        print(f"   - 手续费: ${metrics.get('total_fees', 0):.2f}")
    except Exception as e:
        print(f"❌ 性能指标计算失败: {e}")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    test_none_value_handling()
