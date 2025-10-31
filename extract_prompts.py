#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取AI交易提示词到txt文件
"""

# 读取文件
with open('deepseek_client.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取第一个prompt (analyze_market_and_decide)
start1 = content.find('"""💬 **【CRITICAL】回复格式要求：**')
if start1 > 0:
    # 找到对应的结束位置
    end1 = content.find('💬 **关键**: narrative要写得像一个真实交易员的内心独白，展现你的分析、判断和情绪！"""', start1)
    if end1 > 0:
        end1 += len('💬 **关键**: narrative要写得像一个真实交易员的内心独白，展现你的分析、判断和情绪！"""')
        prompt1 = content[start1+3:end1-3]  # 去掉开始的"""和结束的"""

# 提取第二个prompt (analyze_with_reasoning)
start2 = content.find('"""你是华尔街顶级交易员，使用DeepSeek Chat V3.1进行多步骤深度分析。')
if start2 > 0:
    end2 = content.find('[IDEA] 参数完全由你根据市场实时调整！"""', start2)
    if end2 > 0:
        end2 += len('[IDEA] 参数完全由你根据市场实时调整！"""')
        prompt2 = content[start2+3:end2-3]

# 提取reasoning_guidance
start3 = content.find('[AI-THINK] **DeepSeek Chat V3.1 深度分析模式**')
if start3 > 0:
    end3 = content.find('表格或列表\n"""', start3)
    if end3 > 0:
        end3 += len('表格或列表\n"""')
        reasoning = content[start3:end3-3]

# 写入文件
with open('ai_trading_prompts.txt', 'w', encoding='utf-8') as f:
    f.write('=' * 80 + '\n')
    f.write('Alpha Arena AI 交易提示词完整版\n')
    f.write('文件来源: deepseek_client.py\n')
    f.write('提取时间: 2025-10-29\n')
    f.write('=' * 80 + '\n\n')
    
    f.write('=' * 80 + '\n')
    f.write('提示词 1: analyze_market_and_decide() - 标准分析模式\n')
    f.write('方法位置: deepseek_client.py 第224行\n')
    f.write('=' * 80 + '\n\n')
    if 'prompt1' in locals():
        f.write(prompt1 + '\n\n\n')
    
    f.write('=' * 80 + '\n')
    f.write('提示词 2: analyze_with_reasoning() - 深度推理模式\n')
    f.write('方法位置: deepseek_client.py 第1826行\n')
    f.write('=' * 80 + '\n\n')
    if 'prompt2' in locals():
        f.write(prompt2 + '\n\n\n')
    
    f.write('=' * 80 + '\n')
    f.write('推理指导 (reasoning_guidance)\n')
    f.write('=' * 80 + '\n\n')
    if 'reasoning' in locals():
        f.write(reasoning + '\n\n')

print('✅ 提示词已提取并保存到 ai_trading_prompts.txt')

