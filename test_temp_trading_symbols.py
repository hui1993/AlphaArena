#!/usr/bin/env python3
"""
测试临时交易对管理功能
测试场景：
1. 启动时检测不在TRADING_SYMBOLS中的持仓并添加到临时列表
2. 临时交易对正常被管理
3. 平仓后从临时列表中移除
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alpha_arena_bot import AlphaArenaBot


class TestTempTradingSymbols(unittest.TestCase):
    """测试临时交易对管理"""

    def setUp(self):
        """设置测试环境"""
        # Mock环境变量
        self.env_patcher = patch.dict(os.environ, {
            'TRADING_SYMBOLS': 'BTCUSDT,ETHUSDT,BNBUSDT',
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'DEEPSEEK_API_KEY': 'test_deepseek_key',
            'BINANCE_TESTNET': 'true',
            'INITIAL_CAPITAL': '100',
            'MAX_POSITION_PCT': '10',
            'DEFAULT_LEVERAGE': '3',
            'TRADING_INTERVAL_SECONDS': '120'
        })
        self.env_patcher.start()

    def tearDown(self):
        """清理测试环境"""
        self.env_patcher.stop()

    @patch('alpha_arena_bot.BinanceClient')
    @patch('alpha_arena_bot.MarketAnalyzer')
    @patch('alpha_arena_bot.RiskManager')
    @patch('alpha_arena_bot.AITradingEngine')
    @patch('alpha_arena_bot.PerformanceTracker')
    @patch('alpha_arena_bot.RollTracker')
    @patch('alpha_arena_bot.AdvancedPositionManager')
    @patch('alpha_arena_bot.RollingPositionManager')
    def test_untracked_positions_auto_add(self, *mocks):
        """测试1: 启动时自动添加不在TRADING_SYMBOLS中的持仓"""
        # 创建bot实例
        bot = AlphaArenaBot()
        
        # 验证初始状态
        self.assertEqual(len(bot.trading_symbols), 3)
        self.assertEqual(bot.trading_symbols, ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'])
        self.assertEqual(len(bot.temp_trading_symbols), 0)
        
        # Mock持仓数据（包含一个不在列表中的持仓）
        mock_positions = [
            {
                'symbol': 'BTCUSDT',
                'positionAmt': '0.001',
                'unRealizedProfit': '1.5',
                'entryPrice': '50000',
                'markPrice': '50150'
            },
            {
                'symbol': 'MATICUSDT',  # 不在TRADING_SYMBOLS中
                'positionAmt': '0.5',
                'unRealizedProfit': '2.3',
                'entryPrice': '0.8',
                'markPrice': '0.82'
            },
            {
                'symbol': 'AVAXUSDT',  # 不在TRADING_SYMBOLS中
                'positionAmt': '-0.1',  # SHORT
                'unRealizedProfit': '-0.5',
                'entryPrice': '20.0',
                'markPrice': '19.5'
            }
        ]
        
        # Mock get_active_positions方法
        bot.binance.get_active_positions = Mock(return_value=mock_positions)
        
        # 执行检查
        untracked = bot._check_untracked_positions()
        
        # 验证检测结果
        self.assertEqual(len(untracked), 2)
        self.assertEqual(untracked[0]['symbol'], 'MATICUSDT')
        self.assertEqual(untracked[1]['symbol'], 'AVAXUSDT')
        
        # 验证MATICUSDT的详细信息
        matic_pos = [p for p in untracked if p['symbol'] == 'MATICUSDT'][0]
        self.assertEqual(matic_pos['position_amt'], 0.5)
        self.assertEqual(matic_pos['unrealized_pnl'], 2.3)
        self.assertAlmostEqual(matic_pos['pnl_pct'], 2.5, places=1)  # (0.82-0.8)/0.8*100
        
        # 验证AVAXUSDT的详细信息（SHORT）
        avax_pos = [p for p in untracked if p['symbol'] == 'AVAXUSDT'][0]
        self.assertEqual(avax_pos['position_amt'], -0.1)
        self.assertEqual(avax_pos['unrealized_pnl'], -0.5)

    @patch('alpha_arena_bot.BinanceClient')
    @patch('alpha_arena_bot.MarketAnalyzer')
    @patch('alpha_arena_bot.RiskManager')
    @patch('alpha_arena_bot.AITradingEngine')
    @patch('alpha_arena_bot.PerformanceTracker')
    @patch('alpha_arena_bot.RollTracker')
    @patch('alpha_arena_bot.AdvancedPositionManager')
    @patch('alpha_arena_bot.RollingPositionManager')
    def test_add_temp_symbols_to_list(self, *mocks):
        """测试2: 临时交易对添加到列表并合并遍历"""
        bot = AlphaArenaBot()
        
        # 初始状态
        self.assertEqual(len(bot.trading_symbols), 3)
        self.assertEqual(len(bot.temp_trading_symbols), 0)
        
        # 添加临时交易对
        bot.temp_trading_symbols.append('MATICUSDT')
        bot.temp_trading_symbols.append('AVAXUSDT')
        
        # 验证临时列表
        self.assertEqual(len(bot.temp_trading_symbols), 2)
        self.assertEqual(bot.temp_trading_symbols, ['MATICUSDT', 'AVAXUSDT'])
        
        # 验证合并后的列表
        all_symbols = bot.trading_symbols + bot.temp_trading_symbols
        self.assertEqual(len(all_symbols), 5)
        self.assertIn('BTCUSDT', all_symbols)
        self.assertIn('ETHUSDT', all_symbols)
        self.assertIn('BNBUSDT', all_symbols)
        self.assertIn('MATICUSDT', all_symbols)
        self.assertIn('AVAXUSDT', all_symbols)

    @patch('alpha_arena_bot.BinanceClient')
    @patch('alpha_arena_bot.MarketAnalyzer')
    @patch('alpha_arena_bot.RiskManager')
    @patch('alpha_arena_bot.AITradingEngine')
    @patch('alpha_arena_bot.PerformanceTracker')
    @patch('alpha_arena_bot.RollTracker')
    @patch('alpha_arena_bot.AdvancedPositionManager')
    @patch('alpha_arena_bot.RollingPositionManager')
    def test_remove_temp_symbol_on_close(self, *mocks):
        """测试3: 平仓后从临时列表中移除"""
        bot = AlphaArenaBot()
        
        # 设置临时交易对
        bot.temp_trading_symbols = ['MATICUSDT', 'AVAXUSDT']
        self.assertEqual(len(bot.temp_trading_symbols), 2)
        
        # 模拟平仓MATICUSDT
        symbol = 'MATICUSDT'
        
        # 验证平仓前在列表中
        self.assertIn(symbol, bot.temp_trading_symbols)
        
        # 执行移除逻辑（模拟平仓后的操作）
        if symbol in bot.temp_trading_symbols:
            bot.temp_trading_symbols.remove(symbol)
        
        # 验证移除后不在列表中
        self.assertNotIn(symbol, bot.temp_trading_symbols)
        self.assertEqual(len(bot.temp_trading_symbols), 1)
        self.assertEqual(bot.temp_trading_symbols, ['AVAXUSDT'])
        
        # 验证配置交易对不受影响
        self.assertEqual(len(bot.trading_symbols), 3)
        self.assertIn('BTCUSDT', bot.trading_symbols)

    @patch('alpha_arena_bot.BinanceClient')
    @patch('alpha_arena_bot.MarketAnalyzer')
    @patch('alpha_arena_bot.RiskManager')
    @patch('alpha_arena_bot.AITradingEngine')
    @patch('alpha_arena_bot.PerformanceTracker')
    @patch('alpha_arena_bot.RollTracker')
    @patch('alpha_arena_bot.AdvancedPositionManager')
    @patch('alpha_arena_bot.RollingPositionManager')
    def test_config_symbols_not_removed(self, *mocks):
        """测试4: 配置的交易对不应被移除"""
        bot = AlphaArenaBot()
        
        # 设置临时交易对
        bot.temp_trading_symbols = ['MATICUSDT']
        
        # 尝试"平仓"配置的交易对（不应该从任何列表中移除）
        config_symbol = 'BTCUSDT'
        
        # 验证在配置列表中
        self.assertIn(config_symbol, bot.trading_symbols)
        self.assertNotIn(config_symbol, bot.temp_trading_symbols)
        
        # 模拟"平仓"操作（配置交易对不应从temp列表中移除，因为它不在那里）
        # 实际上，配置交易对永远不会在temp列表中，所以这个测试验证逻辑正确性
        if config_symbol in bot.temp_trading_symbols:
            bot.temp_trading_symbols.remove(config_symbol)
        
        # 验证配置列表不受影响
        self.assertEqual(len(bot.trading_symbols), 3)
        self.assertIn(config_symbol, bot.trading_symbols)
        self.assertEqual(len(bot.temp_trading_symbols), 1)  # MATICUSDT仍在临时列表中

    @patch('alpha_arena_bot.BinanceClient')
    @patch('alpha_arena_bot.MarketAnalyzer')
    @patch('alpha_arena_bot.RiskManager')
    @patch('alpha_arena_bot.AITradingEngine')
    @patch('alpha_arena_bot.PerformanceTracker')
    @patch('alpha_arena_bot.RollTracker')
    @patch('alpha_arena_bot.AdvancedPositionManager')
    @patch('alpha_arena_bot.RollingPositionManager')
    def test_no_duplicate_symbols(self, *mocks):
        """测试5: 确保不会重复添加相同的交易对"""
        bot = AlphaArenaBot()
        
        # 初始状态
        self.assertEqual(len(bot.trading_symbols), 3)
        self.assertEqual(len(bot.temp_trading_symbols), 0)
        
        # 第一次添加
        if 'MATICUSDT' not in bot.trading_symbols and 'MATICUSDT' not in bot.temp_trading_symbols:
            bot.temp_trading_symbols.append('MATICUSDT')
        
        self.assertEqual(len(bot.temp_trading_symbols), 1)
        
        # 尝试再次添加（应该被阻止）
        if 'MATICUSDT' not in bot.trading_symbols and 'MATICUSDT' not in bot.temp_trading_symbols:
            bot.temp_trading_symbols.append('MATICUSDT')
        
        # 验证没有重复
        self.assertEqual(len(bot.temp_trading_symbols), 1)
        self.assertEqual(bot.temp_trading_symbols.count('MATICUSDT'), 1)

    @patch('alpha_arena_bot.BinanceClient')
    @patch('alpha_arena_bot.MarketAnalyzer')
    @patch('alpha_arena_bot.RiskManager')
    @patch('alpha_arena_bot.AITradingEngine')
    @patch('alpha_arena_bot.PerformanceTracker')
    @patch('alpha_arena_bot.RollTracker')
    @patch('alpha_arena_bot.AdvancedPositionManager')
    @patch('alpha_arena_bot.RollingPositionManager')
    def test_empty_positions_handling(self, *mocks):
        """测试6: 处理空持仓的情况"""
        bot = AlphaArenaBot()
        
        # Mock空持仓
        bot.binance.get_active_positions = Mock(return_value=[])
        
        # 执行检查
        untracked = bot._check_untracked_positions()
        
        # 验证没有未跟踪的持仓
        self.assertEqual(len(untracked), 0)
        self.assertEqual(untracked, [])

    @patch('alpha_arena_bot.BinanceClient')
    @patch('alpha_arena_bot.MarketAnalyzer')
    @patch('alpha_arena_bot.RiskManager')
    @patch('alpha_arena_bot.AITradingEngine')
    @patch('alpha_arena_bot.PerformanceTracker')
    @patch('alpha_arena_bot.RollTracker')
    @patch('alpha_arena_bot.AdvancedPositionManager')
    @patch('alpha_arena_bot.RollingPositionManager')
    def test_all_positions_tracked(self, *mocks):
        """测试7: 所有持仓都在配置列表中"""
        bot = AlphaArenaBot()
        
        # Mock所有持仓都在配置列表中
        mock_positions = [
            {
                'symbol': 'BTCUSDT',
                'positionAmt': '0.001',
                'unRealizedProfit': '1.5',
                'entryPrice': '50000',
                'markPrice': '50150'
            },
            {
                'symbol': 'ETHUSDT',
                'positionAmt': '0.01',
                'unRealizedProfit': '2.0',
                'entryPrice': '3000',
                'markPrice': '3020'
            }
        ]
        
        bot.binance.get_active_positions = Mock(return_value=mock_positions)
        
        # 执行检查
        untracked = bot._check_untracked_positions()
        
        # 验证没有未跟踪的持仓
        self.assertEqual(len(untracked), 0)


def run_tests():
    """运行所有测试"""
    print("=" * 80)
    print("测试临时交易对管理功能")
    print("=" * 80)
    print()
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTempTradingSymbols)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印摘要
    print()
    print("=" * 80)
    if result.wasSuccessful():
        print("✓ 所有测试通过!")
    else:
        print(f"✗ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

