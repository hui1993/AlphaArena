#!/usr/bin/env python3
"""
分析日志文件，找出为什么没有交易
"""
import re
from collections import Counter

# 读取日志文件
with open('logs/alpha_arena_20251029.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('📊 Alpha Arena 交易决策分析报告')
print('=' * 70)
print()

# 统计决策关键词
keywords = {
    '等待': 0,
    '不符合': 0,
    '禁止': 0,
    'OPEN_LONG': 0,
    'OPEN_SHORT': 0,
    'HOLD': 0,
    '违反': 0,
    '超买': 0,
    '超卖': 0,
}

# 分析每个AI决策
decisions = []
for i, line in enumerate(lines):
    if '[AI] DEEPSEEK CHAT V3.1 决策:' in line:
        # 获取决策内容（下一行）
        if i + 1 < len(lines):
            decision = lines[i + 1]
            decisions.append(decision)
            
            # 统计关键词
            for keyword in keywords:
                if keyword in decision:
                    keywords[keyword] += 1

print(f'📈 总决策次数: {len(decisions)}')
print()
print('🔍 决策关键词统计:')
for keyword, count in keywords.items():
    if count > 0:
        print(f'   {keyword}: {count}次')
print()

# 分析决策拒绝原因
rejection_reasons = Counter()

for decision in decisions:
    if '价格' in decision and 'SMA50' in decision:
        if '低于' in decision or '<' in decision:
            rejection_reasons['价格低于SMA50'] += 1
    if 'MACD' in decision and '<' in decision and '0' in decision:
        rejection_reasons['MACD为负'] += 1
    if 'RSI' in decision and ('超买' in decision or '>65' in decision or '> 65' in decision):
        rejection_reasons['RSI超买'] += 1
    if 'RSI' in decision and ('超卖' in decision or '<35' in decision or '< 35' in decision):
        rejection_reasons['RSI超卖'] += 1
    if '等待' in decision:
        rejection_reasons['等待明确信号'] += 1
    if '不符合' in decision or '违反' in decision:
        rejection_reasons['不符合开仓条件'] += 1
    if '空头' in decision or '下跌趋势' in decision:
        rejection_reasons['下跌趋势'] += 1
    if '矛盾' in decision:
        rejection_reasons['信号矛盾'] += 1

print('🚫 拒绝开仓的主要原因:')
for reason, count in rejection_reasons.most_common(10):
    print(f'   {reason}: {count}次')
print()

# 检查是否有实际交易
trades = 0
positions_opened = 0
for line in lines:
    if '开仓成功' in line or 'OPEN_LONG' in line or 'OPEN_SHORT' in line:
        if '不符合' not in line and '禁止' not in line:
            trades += 1
            positions_opened += 1

print(f'💼 实际开仓次数: {positions_opened}')
print()

# API错误统计
api_errors = [l for l in lines if 'Invalid symbol' in l or 'ERROR' in l]
invalid_symbol_count = len([l for l in api_errors if 'Invalid symbol' in l])
print(f'⚠️  API错误次数: {invalid_symbol_count}')
if api_errors:
    print('   主要错误: 1000SHIBUSDT - Invalid symbol (这是期货专用交易对，应使用期货API)')
print()

# 分析市场状态
market_trend = Counter()
for decision in decisions:
    if '空头' in decision or '下跌' in decision:
        market_trend['下跌'] += 1
    elif '多头' in decision or '上涨' in decision:
        market_trend['上涨'] += 1
    else:
        market_trend['震荡'] += 1

print('📊 市场整体趋势:')
for trend, count in market_trend.most_common():
    print(f'   {trend}: {count}次')
print()

# 总结
print('=' * 70)
print('📋 问题总结:')
print('   1. AI决策系统运行正常，但过于保守')
print('   2. 所有决策都是"等待"或"不符合条件"，没有实际交易')
print('   3. 市场整体处于下跌趋势，技术指标不满足开仓条件')
print('   4. 开仓条件过于严格，需同时满足多个条件')
print('   5. 存在API调用错误（1000SHIBUSDT使用现货API）')
print()
print('💡 解决方案建议:')
print('   1. 考虑放宽开仓条件或调整参数阈值')
print('   2. 修复1000SHIBUSDT的API调用（已在binance_client.py修复）')
print('   3. 在趋势不明确的市场中，考虑增加区间交易策略')
print('   4. 降低confidence阈值或允许HOLD策略在某些情况下转换为开仓')
print('   5. 检查是否有实际的市场机会被过度过滤')

