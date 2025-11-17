#!/usr/bin/env python3
"""
清理过大的数据文件，防止OOM
- 限制trades数组最多保留10000条
- 限制portfolio_values数组最多保留10000条
"""

import json
import os
import shutil
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_performance_data(data_file='performance_data.json', max_trades=10000, max_portfolio_values=10000):
    """清理performance_data.json文件"""
    if not os.path.exists(data_file):
        logger.warning(f"文件不存在: {data_file}")
        return False
    
    try:
        # 备份原文件
        backup_file = f"{data_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(data_file, backup_file)
        logger.info(f"已备份原文件到: {backup_file}")
        
        # 加载数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_trades = len(data.get('trades', []))
        original_portfolio = len(data.get('portfolio_values', []))
        
        # 清理trades
        if original_trades > max_trades:
            data['trades'] = data['trades'][-max_trades:]
            logger.info(f"清理trades: {original_trades} -> {len(data['trades'])} 条")
        
        # 清理portfolio_values
        if original_portfolio > max_portfolio_values:
            data['portfolio_values'] = data['portfolio_values'][-max_portfolio_values:]
            logger.info(f"清理portfolio_values: {original_portfolio} -> {len(data['portfolio_values'])} 条")
        
        # 保存清理后的数据
        temp_file = data_file + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 原子性替换
        shutil.move(temp_file, data_file)
        
        # 检查文件大小
        new_size = os.path.getsize(data_file) / 1024 / 1024  # MB
        logger.info(f"清理完成，新文件大小: {new_size:.2f} MB")
        
        return True
        
    except Exception as e:
        logger.error(f"清理失败: {e}")
        return False

def cleanup_ai_decisions(data_file='ai_decisions.json', max_decisions=200):
    """清理ai_decisions.json文件"""
    if not os.path.exists(data_file):
        logger.warning(f"文件不存在: {data_file}")
        return False
    
    try:
        # 备份原文件
        backup_file = f"{data_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(data_file, backup_file)
        logger.info(f"已备份原文件到: {backup_file}")
        
        # 加载数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_count = len(data)
        
        # 清理decisions（只保留最近的）
        if original_count > max_decisions:
            data = data[-max_decisions:]
            logger.info(f"清理decisions: {original_count} -> {len(data)} 条")
        
        # 保存清理后的数据
        temp_file = data_file + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 原子性替换
        shutil.move(temp_file, data_file)
        
        # 检查文件大小
        new_size = os.path.getsize(data_file) / 1024  # KB
        logger.info(f"清理完成，新文件大小: {new_size:.2f} KB")
        
        return True
        
    except Exception as e:
        logger.error(f"清理失败: {e}")
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("清理过大的数据文件，防止OOM")
    print("=" * 70)
    print()
    
    # 清理performance_data.json
    print("1. 清理 performance_data.json...")
    cleanup_performance_data()
    print()
    
    # 清理ai_decisions.json
    print("2. 清理 ai_decisions.json...")
    cleanup_ai_decisions()
    print()
    
    print("=" * 70)
    print("清理完成！")
    print("=" * 70)

