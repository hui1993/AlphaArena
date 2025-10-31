#!/usr/bin/env python3
"""
更新交易对配置
自动检测账户支持的所有交易对，并添加到配置中
"""

import os
from binance_client import BinanceClient
from dotenv import load_dotenv

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def get_all_trading_symbols(client, min_volume=0, limit=30):
    """获取所有可交易对，按交易量排序"""
    print_info("正在获取交易所信息...")
    
    # 获取交易所信息
    exchange_info = client.get_futures_exchange_info()
    symbols_data = exchange_info.get('symbols', [])
    
    # 过滤出活跃且可交易的USDT永续合约
    active_symbols = []
    for symbol_info in symbols_data:
        if symbol_info.get('status') == 'TRADING':
            symbol = symbol_info.get('symbol')
            quote_asset = symbol_info.get('quoteAsset')
            
            # 只获取USDT计价的永续合约
            if quote_asset == 'USDT' and symbol_info.get('contractType') == 'PERPETUAL':
                active_symbols.append({
                    'symbol': symbol,
                    'base': symbol_info.get('baseAsset'),
                    'margin_asset': symbol_info.get('marginAsset'),
                    'price_precision': symbol_info.get('pricePrecision'),
                    'quantity_precision': symbol_info.get('quantityPrecision')
                })
    
    print_success(f"找到 {len(active_symbols)} 个USDT永续合约交易对")
    
    # 获取交易量数据并排序
    print_info("正在获取24小时交易量数据...")
    tickers = {}
    
    for symbol_info in active_symbols[:100]:  # 限制数量以提高速度
        try:
            ticker = client.get_futures_24h_ticker(symbol_info['symbol'])
            volume = float(ticker.get('quoteVolume', 0))
            if volume >= min_volume:
                tickers[symbol_info['symbol']] = {
                    'volume': volume,
                    'data': symbol_info
                }
        except Exception as e:
            continue
    
    # 按交易量排序
    sorted_symbols = sorted(
        tickers.items(),
        key=lambda x: x[1]['volume'],
        reverse=True
    )[:limit]
    
    return [s[0] for s in sorted_symbols], tickers

def update_config_file(symbols):
    """更新 .env 文件中的交易对配置"""
    env_file = '.env'
    
    # 读取现有配置
    lines = []
    trading_symbols_line = None
    
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找现有的 TRADING_SYMBOLS 行
        for i, line in enumerate(lines):
            if line.strip().startswith('TRADING_SYMBOLS='):
                trading_symbols_line = i
                break
    
    # 创建新的交易对配置
    symbols_str = ','.join(symbols)
    new_line = f"TRADING_SYMBOLS={symbols_str}\n"
    
    # 更新或添加配置
    if trading_symbols_line is not None:
        lines[trading_symbols_line] = new_line
        print_success(f"已更新 .env 文件中的交易对配置")
    else:
        lines.append(new_line)
        print_success(f"已添加交易对配置到 .env 文件")
    
    # 写入文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def main():
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("=" * 60)
    print("🔄 更新交易对配置")
    print("=" * 60)
    print(f"{Colors.END}")
    
    # 加载配置
    load_dotenv()
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    
    if not api_key or not api_secret:
        print("❌ 错误: API密钥未配置")
        return
    
    print_info(f"环境: {'测试网' if testnet else '主网'}")
    print_info(f"API Key: {api_key[:8]}...")
    print()
    
    try:
        # 初始化客户端
        client = BinanceClient(api_key, api_secret, testnet=testnet)
        
        # 获取热门交易对（前30个，交易量>1000万）
        symbols, tickers = get_all_trading_symbols(
            client,
            min_volume=10_000_000,  # 最低1000万美元交易量
            limit=30
        )
        
        print()
        print_info(f"选择前 {len(symbols)} 个热门交易对:")
        print("-" * 60)
        
        for i, symbol in enumerate(symbols, 1):
            volume = tickers[symbol]['volume']
            base = tickers[symbol]['data']['base']
            volume_str = f'${volume/1e9:.2f}B' if volume > 1e9 else f'${volume/1e6:.2f}M'
            print(f"{i:2d}. {symbol:12s} ({base:8s}) - 24h交易量: {volume_str}")
        
        print()
        
        # 获取当前配置
        current_symbols_str = os.getenv('TRADING_SYMBOLS', '')
        current_symbols = [s.strip() for s in current_symbols_str.split(',') if s.strip()]
        
        if current_symbols:
            print_info(f"当前配置的交易对 ({len(current_symbols)} 个):")
            print(f"  {', '.join(current_symbols)}")
            print()
        
        # 更新配置
        print_info("正在更新配置文件...")
        update_config_file(symbols)
        
        print()
        print_success("配置更新完成！")
        print()
        print(f"{Colors.BOLD}更新后的交易对列表:{Colors.END}")
        print(f"  {', '.join(symbols)}")
        print()
        print("📝 下一步:")
        print("  1. 检查 .env 文件确认配置已更新")
        print("  2. 重启交易机器人使配置生效")
        print("  3. 运行 python3 alpha_arena_bot.py")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

