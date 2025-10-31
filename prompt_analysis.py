#!/usr/bin/env python3
"""
分析AI提示词是否过于保守
"""
import re

print("=" * 80)
print("📝 AI提示词保守性分析报告")
print("=" * 80)
print()
print("提示词位置: deepseek_client.py")
print()
print("=" * 80)
print("🔍 关键保守性特征统计")
print("=" * 80)
print()

# 读取提示词文件
with open('deepseek_client.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 分析方法1: analyze_market_and_decide
method1_start = content.find('def analyze_market_and_decide')
method1_end = content.find('def analyze_with_reasoning')
method1 = content[method1_start:method1_end]

# 分析方法2: analyze_with_reasoning  
method2_start = content.find('def analyze_with_reasoning')
method2 = content[method2_start:method2_start+3000]

# 统计保守性关键词
conservative_keywords = {
    '绝对禁止': 0,
    'ERROR': 0,
    '严格禁止': 0,
    '必须': 0,
    '仅': 0,
    '等待': 0,
    'HOLD': 0,
    '不符合': 0,
    '禁止': 0,
    '只': 0,  # "只在这3种情况"
    '和': 0,  # "价格>SMA20>SMA50 + MACD>0 + RSI..."
}

action_keywords = {
    'OPEN_LONG': 0,
    'OPEN_SHORT': 0,
    'HOLD': 0,
}

# 分析方法1
for keyword in conservative_keywords:
    conservative_keywords[keyword] += len(re.findall(keyword, method1, re.I))

for keyword in action_keywords:
    action_keywords[keyword] += len(re.findall(keyword, method1, re.I))

# 分析方法2
for keyword in conservative_keywords:
    conservative_keywords[keyword] += len(re.findall(keyword, method2, re.I))

for keyword in action_keywords:
    action_keywords[keyword] += len(re.findall(keyword, method2, re.I))

print("📊 保守性关键词统计:")
for keyword, count in sorted(conservative_keywords.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"   {keyword}: {count}次")
print()

print("📊 行动指令统计:")
for keyword, count in sorted(action_keywords.items(), key=lambda x: x[1], reverse=True):
    print(f"   {keyword}: {count}次")
print()

# 分析开仓条件严格程度
print("=" * 80)
print("🚨 开仓条件严格程度分析")
print("=" * 80)
print()

# 提取开仓条件
long_conditions = re.findall(r'做多.*?条件|OPEN_LONG.*?条件', content, re.I | re.DOTALL)
short_conditions = re.findall(r'做空.*?条件|OPEN_SHORT.*?条件', content, re.I | re.DOTALL)

print("🔹 做多条件 (从prompt中提取):")
lines = content.split('\n')
for i, line in enumerate(lines):
    if '做多' in line or 'OPEN_LONG' in line:
        if '条件' in line or i < len(lines) - 1 and ('满足' in lines[i+1] or '核心条件' in lines[i+1]):
            print(f"   {line.strip()}")
            # 打印后续几行
            for j in range(1, 10):
                if i+j < len(lines):
                    next_line = lines[i+j].strip()
                    if next_line and not next_line.startswith('#'):
                        if '禁止' in next_line or 'ERROR' in next_line or next_line.startswith('🚫'):
                            break
                        if any(x in next_line for x in ['价格', 'SMA', 'MACD', 'RSI', '突破', '条件']):
                            print(f"      {next_line}")
                    if j > 15:  # 最多打印10行
                        break
print()

print("🔹 做空条件 (从prompt中提取):")
for i, line in enumerate(lines):
    if '做空' in line or 'OPEN_SHORT' in line:
        if '条件' in line or i < len(lines) - 1 and ('满足' in lines[i+1] or '核心条件' in lines[i+1]):
            print(f"   {line.strip()}")
            # 打印后续几行
            for j in range(1, 10):
                if i+j < len(lines):
                    next_line = lines[i+j].strip()
                    if next_line and not next_line.startswith('#'):
                        if '禁止' in next_line or 'ERROR' in next_line or next_line.startswith('🚫'):
                            break
                        if any(x in next_line for x in ['价格', 'SMA', 'MACD', 'RSI', '跌破', '条件']):
                            print(f"      {next_line}")
                    if j > 15:
                        break
print()

# 分析禁止条件数量
print("=" * 80)
print("🚫 禁止条件统计")
print("=" * 80)
print()

error_patterns = re.findall(r'\[ERROR\][^\n]+', content)
print(f"找到 {len(error_patterns)} 个 ERROR 禁止条件:")
for pattern in error_patterns[:10]:  # 显示前10个
    print(f"   {pattern.strip()}")
if len(error_patterns) > 10:
    print(f"   ... 还有 {len(error_patterns) - 10} 个")
print()

# 分析条件组合要求
print("=" * 80)
print("🔗 条件组合要求分析")
print("=" * 80)
print()

# 查找"必须同时满足"或"满足任意X个"的表达
must_all = len(re.findall(r'同时满足|全部满足|都满足|AND|\+', content, re.I))
any_some = len(re.findall(r'任意.*?个|满足.*?个即可|或.*?即可', content, re.I))

print(f"   '必须同时满足' 类表达: {must_all}次")
print(f"   '满足任意X个即可' 类表达: {any_some}次")
print()
print("   ⚠️  问题: '必须同时满足'的表述更多，说明条件过于严格")
print()

# 总结
print("=" * 80)
print("📋 总结分析")
print("=" * 80)
print()

print("1. 保守性特征:")
print("   ✅ 大量使用'绝对禁止'、'严格禁止'等强硬措辞")
print("   ✅ 设置了6个明确的ERROR禁止条件")
print("   ✅ '只在这3种情况'的表述限制了交易机会")
print()

print("2. 开仓条件严格程度:")
print("   做多需要同时满足:")
print("      - 价格 > SMA20 > SMA50 (多头排列)")
print("      - MACD > 0")
print("      - RSI在45-65区间")
print("      - 突破近10根K线高点")
print("   ⚠️  在真实市场中，这4个条件很难同时满足")
print()

print("3. 禁止条件过多:")
print(f"   - 找到 {len(error_patterns)} 个ERROR禁止条件")
print("   - 几乎覆盖了所有可能的逆势情况")
print("   - 这导致AI在任何不完美的情况下都选择HOLD")
print()

print("4. 矛盾之处:")
print("   - 目标：'20U两天翻10倍'(激进)")
print("   - 规则：'只在明确趋势时开仓'(保守)")
print("   - 结果：极度的保守与激进目标不匹配")
print()

print("=" * 80)
print("💡 建议")
print("=" * 80)
print()

print("1. 放宽条件组合要求:")
print("   - 将'必须同时满足所有条件'改为'满足70%条件即可'")
print("   - 允许'满足任意3-4个条件'而非'全部满足'")
print()

print("2. 减少绝对禁止:")
print("   - 将部分'绝对禁止'改为'谨慎考虑'")
print("   - 增加'特殊情况允许'的例外条款")
print()

print("3. 增加市场环境识别:")
print("   - 明确趋势市场: 严格执行规则")
print("   - 震荡市场: 允许区间交易")
print("   - 趋势转换: 允许捕捉反转机会")
print()

print("4. 调整目标与策略的一致性:")
print("   - 如果目标是激进翻倍，规则应该允许适度的风险承担")
print("   - 或者降低目标，与保守规则匹配")
print()

