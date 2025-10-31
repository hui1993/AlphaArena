#!/usr/bin/env python3
"""
币安API连接测试脚本
测试现货和合约API的连接状态、权限和功能
"""

import os
import time
import requests
import hmac
import hashlib
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv
from binance_client import BinanceClient

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """打印测试标题"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("🔗 币安API连接测试脚本")
    print("=" * 60)
    print(f"{Colors.END}")

def print_section(title):
    """打印测试章节标题"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}📋 {title}{Colors.END}")
    print("-" * 40)

def print_success(message):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """打印信息消息"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

def test_environment():
    """测试环境变量配置"""
    print_section("环境变量检查")
    
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    
    if not api_key:
        print_error("BINANCE_API_KEY 未设置")
        return False, None, None, None
    
    if not api_secret:
        print_error("BINANCE_API_SECRET 未设置")
        return False, None, None, None
    
    print_success(f"API Key: {api_key[:8]}...")
    print_success(f"API Secret: {'*' * 8}...")
    print_success(f"测试网模式: {'是' if testnet else '否'}")
    
    return True, api_key, api_secret, testnet

def test_public_api():
    """测试公共API（无需认证）"""
    print_section("公共API测试")
    
    try:
        # 测试服务器时间
        response = requests.get('https://api.binance.com/api/v3/time', timeout=10)
        if response.status_code == 200:
            server_time = response.json()['serverTime']
            local_time = int(time.time() * 1000)
            time_diff = abs(server_time - local_time)
            print_success(f"服务器时间同步正常 (差异: {time_diff}ms)")
            
            if time_diff > 5000:
                print_warning("时间差异超过5秒，可能影响签名验证")
        else:
            print_error(f"服务器时间获取失败: {response.status_code}")
            return False
            
        # 测试价格数据
        response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
        if response.status_code == 200:
            price_data = response.json()
            btc_price = float(price_data['price'])
            print_success(f"BTC价格: ${btc_price:,.2f}")
        else:
            print_error(f"价格数据获取失败: {response.status_code}")
            return False
            
        # 测试24小时统计
        response = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=10)
        if response.status_code == 200:
            ticker_data = response.json()
            change_pct = float(ticker_data['priceChangePercent'])
            volume = float(ticker_data['volume'])
            print_success(f"24h涨跌: {change_pct:+.2f}%")
            print_success(f"24h成交量: {volume:,.0f} BTC")
        else:
            print_error(f"24小时统计获取失败: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print_error(f"公共API测试失败: {e}")
        return False

def test_spot_api(api_key, api_secret):
    """测试现货API（需要认证）"""
    print_section("现货API测试")
    
    try:
        # 手动构建请求测试签名
        params = {'timestamp': int(time.time() * 1000)}
        query_string = urlencode(params)
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        headers = {'X-MBX-APIKEY': api_key}
        
        # 测试账户信息
        response = requests.get(
            'https://api.binance.com/api/v3/account',
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            account = response.json()
            print_success("现货账户信息获取成功")
            print_info(f"账户类型: {account.get('accountType', 'Unknown')}")
            print_info(f"权限: {', '.join(account.get('permissions', []))}")
            
            # 显示USDT余额
            balances = account.get('balances', [])
            usdt_balance = next((b for b in balances if b['asset'] == 'USDT'), None)
            if usdt_balance:
                free_balance = float(usdt_balance['free'])
                locked_balance = float(usdt_balance['locked'])
                total_balance = free_balance + locked_balance
                print_success(f"USDT余额: {total_balance:,.2f} (可用: {free_balance:,.2f})")
            else:
                print_warning("未找到USDT余额")
                
            return True
        else:
            print_error(f"现货账户信息获取失败: {response.status_code}")
            try:
                error = response.json()
                print_error(f"错误代码: {error.get('code', 'Unknown')}")
                print_error(f"错误信息: {error.get('msg', 'Unknown')}")
            except:
                print_error(f"原始响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"现货API测试失败: {e}")
        return False

def test_futures_api(api_key, api_secret):
    """测试合约API（需要认证）"""
    print_section("合约API测试")
    
    try:
        # 手动构建请求测试签名
        params = {'timestamp': int(time.time() * 1000)}
        query_string = urlencode(params)
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        headers = {'X-MBX-APIKEY': api_key}
        
        # 测试合约账户信息
        response = requests.get(
            'https://fapi.binance.com/fapi/v2/account',
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            account = response.json()
            print_success("合约账户信息获取成功")
            
            total_balance = float(account.get('totalWalletBalance', 0))
            available_balance = float(account.get('availableBalance', 0))
            unrealized_pnl = float(account.get('totalUnrealizedPnl', 0))
            
            print_success(f"总钱包余额: ${total_balance:,.2f}")
            print_success(f"可用余额: ${available_balance:,.2f}")
            print_success(f"未实现盈亏: ${unrealized_pnl:,.2f}")
            
            # 测试持仓信息
            response = requests.get(
                'https://fapi.binance.com/fapi/v2/positionRisk',
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                positions = response.json()
                active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
                print_success(f"持仓信息获取成功，活跃持仓: {len(active_positions)}个")
                
                if active_positions:
                    print_info("活跃持仓详情:")
                    for pos in active_positions:
                        symbol = pos['symbol']
                        amt = float(pos['positionAmt'])
                        side = '多头' if amt > 0 else '空头'
                        entry_price = float(pos['entryPrice'])
                        mark_price = float(pos['markPrice'])
                        pnl = float(pos['unRealizedPnl'])
                        print_info(f"  {symbol}: {abs(amt):.3f} ({side}) 入场价: {entry_price:.2f} 标记价: {mark_price:.2f} 盈亏: ${pnl:.2f}")
                else:
                    print_info("当前无活跃持仓")
                    
            return True
        else:
            print_error(f"合约账户信息获取失败: {response.status_code}")
            try:
                error = response.json()
                error_code = error.get('code', 'Unknown')
                error_msg = error.get('msg', 'Unknown')
                print_error(f"错误代码: {error_code}")
                print_error(f"错误信息: {error_msg}")
                
                if error_code == -2015:
                    print_warning("这通常表示API密钥缺少合约交易权限")
                    print_info("解决方案: 在币安API管理中启用'Enable Futures'权限")
                elif error_code == -1021:
                    print_warning("时间戳超出接收窗口")
                    print_info("解决方案: 检查系统时间同步")
                    
            except:
                print_error(f"原始响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"合约API测试失败: {e}")
        return False

def test_binance_client():
    """测试BinanceClient类"""
    print_section("BinanceClient类测试")
    
    try:
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
        
        client = BinanceClient(api_key, api_secret, testnet=testnet)
        
        # 测试公共方法
        print_info("测试公共API方法...")
        ticker = client.get_ticker_price('BTCUSDT')
        print_success(f"BTC价格: ${float(ticker['price']):,.2f}")
        
        # 测试现货方法
        print_info("测试现货API方法...")
        try:
            account = client.get_account_info()
            print_success("现货账户信息获取成功")
        except Exception as e:
            print_error(f"现货账户信息获取失败: {e}")
        
        # 测试合约方法
        print_info("测试合约API方法...")
        try:
            futures_account = client.get_futures_account_info()
            print_success("合约账户信息获取成功")
        except Exception as e:
            print_error(f"合约账户信息获取失败: {e}")
            
        return True
        
    except Exception as e:
        print_error(f"BinanceClient测试失败: {e}")
        return False

def test_trading_api(api_key, api_secret):
    """测试交易相关API（只读操作，不会实际执行交易）"""
    print_section("交易API测试")
    
    try:
        load_dotenv()
        testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
        client = BinanceClient(api_key, api_secret, testnet=testnet)
        
        # 测试1: 查询交易对信息
        print_info("测试1: 查询交易对信息...")
        try:
            exchange_info = client.get_futures_exchange_info('BTCUSDT')
            if exchange_info:
                symbols = exchange_info.get('symbols', [])
                if symbols:
                    symbol_info = symbols[0]
                    print_success(f"交易对信息获取成功: {symbol_info.get('symbol')}")
                    print_info(f"  合约类型: {symbol_info.get('contractType')}")
                    print_info(f"  价格精度: {symbol_info.get('pricePrecision')}")
                    print_info(f"  数量精度: {symbol_info.get('quantityPrecision')}")
            else:
                print_success("交易对信息获取成功")
        except Exception as e:
            print_error(f"交易对信息获取失败: {e}")
        
        # 测试2: 查询当前挂单
        print_info("测试2: 查询当前挂单...")
        try:
            open_orders = client.get_futures_open_orders()
            if isinstance(open_orders, list):
                print_success(f"挂单查询成功，当前挂单数: {len(open_orders)}")
                if len(open_orders) > 0:
                    print_info("前3个挂单:")
                    for order in open_orders[:3]:
                        symbol = order.get('symbol', 'N/A')
                        side = order.get('side', 'N/A')
                        order_type = order.get('type', 'N/A')
                        price = order.get('price', 'N/A')
                        orig_qty = order.get('origQty', 'N/A')
                        print_info(f"  {symbol}: {side} {order_type} {price} x {orig_qty}")
            else:
                print_success("挂单查询成功（无挂单）")
        except Exception as e:
            print_error(f"挂单查询失败: {e}")
        
        # 测试3: 查询持仓模式
        print_info("测试3: 查询持仓模式...")
        try:
            position_mode = client.get_position_mode()
            dual_side = position_mode.get('dualSidePosition', False)
            mode_str = "双向持仓" if dual_side else "单向持仓"
            print_success(f"持仓模式查询成功: {mode_str}")
        except Exception as e:
            print_error(f"持仓模式查询失败: {e}")
        
        # 测试4: 查询当前杠杆设置（通过查询持仓信息推断）
        print_info("测试4: 查询杠杆设置...")
        try:
            positions = client.get_futures_positions()
            if positions:
                btc_position = next((p for p in positions if p['symbol'] == 'BTCUSDT'), None)
                if btc_position:
                    leverage = btc_position.get('leverage', 'N/A')
                    margin_type = btc_position.get('marginType', 'N/A')
                    print_success(f"BTCUSDT杠杆查询成功")
                    print_info(f"  杠杆倍数: {leverage}x")
                    print_info(f"  保证金类型: {margin_type}")
                else:
                    print_info("未找到BTCUSDT持仓，无法查询杠杆设置")
        except Exception as e:
            print_error(f"杠杆设置查询失败: {e}")
        
        # 测试5: 查询资金费率
        print_info("测试5: 查询资金费率...")
        try:
            funding_rate = client.get_current_funding_rate('BTCUSDT')
            if funding_rate:
                rate = float(funding_rate.get('lastFundingRate', 0)) * 100
                next_funding_time = funding_rate.get('nextFundingTime', 0)
                print_success(f"资金费率查询成功")
                print_info(f"  当前费率: {rate:.4f}%")
                if next_funding_time:
                    next_time = datetime.fromtimestamp(next_funding_time / 1000)
                    print_info(f"  下次结算: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print_error(f"资金费率查询失败: {e}")
        
        # 测试6: 查询持仓量（Open Interest）
        print_info("测试6: 查询持仓量...")
        try:
            oi_data = client.get_open_interest('BTCUSDT')
            if oi_data:
                open_interest = float(oi_data.get('openInterest', 0))
                print_success(f"持仓量查询成功")
                oi_btc = open_interest / 1e8  # 转换为BTC单位
                print_info(f"  BTCUSDT持仓量: {oi_btc:,.0f} BTC (${open_interest:,.0f})")
        except Exception as e:
            print_error(f"持仓量查询失败: {e}")
        
        # 测试7: 查询交易历史（最近10笔，如果有）
        print_info("测试7: 查询交易历史...")
        try:
            trades = client.get_futures_trade_history('BTCUSDT', limit=10)
            if isinstance(trades, list):
                print_success(f"交易历史查询成功，最近交易数: {len(trades)}")
                if len(trades) > 0:
                    print_info("最近3笔交易:")
                    for trade in trades[:3]:
                        price = float(trade.get('price', 0))
                        qty = float(trade.get('qty', 0))
                        side = trade.get('buyer', False) and '买入' or '卖出'
                        trade_time_ms = trade.get('time', 0)
                        trade_time = datetime.fromtimestamp(trade_time_ms / 1000)
                        print_info(f"  {trade_time.strftime('%H:%M:%S')}: {side} {qty:.4f} @ ${price:,.2f}")
            else:
                print_success("交易历史查询成功（无历史记录）")
        except Exception as e:
            print_error(f"交易历史查询失败: {e}")
        
        # 测试8: 查询订单历史（最近10笔，如果有）
        print_info("测试8: 查询订单历史...")
        try:
            orders = client.get_futures_order_history('BTCUSDT', limit=10)
            if isinstance(orders, list):
                print_success(f"订单历史查询成功，最近订单数: {len(orders)}")
                if len(orders) > 0:
                    print_info("最近3个订单:")
                    for order in orders[:3]:
                        symbol = order.get('symbol', 'N/A')
                        side = order.get('side', 'N/A')
                        status = order.get('status', 'N/A')
                        price = order.get('price', 'N/A')
                        print_info(f"  {symbol}: {side} {status} @ {price}")
            else:
                print_success("订单历史查询成功（无历史记录）")
        except Exception as e:
            print_error(f"订单历史查询失败: {e}")
        
        # 测试9: 测试K线API（验证智能回退功能）
        print_info("测试9: 测试K线API（自动选择现货/期货API）...")
        test_symbols = ['BTCUSDT', '1000SHIBUSDT', 'ETHUSDT']
        
        for symbol in test_symbols:
            try:
                print_info(f"  测试 {symbol}:")
                klines = client.get_klines(symbol, '1m', limit=1)
                if klines:
                    price = float(klines[0][4])
                    print_success(f"    ✅ 成功获取 {symbol} K线数据: ${price:,.4f}")
                    print_info(f"    说明: get_klines()会自动选择正确的API（现货或期货）")
                else:
                    print_warning(f"    ⚠️  {symbol} 返回空数据")
            except Exception as e:
                error_msg = str(e)
                print_error(f"    ❌ {symbol} K线获取失败: {error_msg[:100]}")
        
        # 测试期货API K线（如果可用）
        print_info("测试10: 测试期货K线API...")
        try:
            # 直接使用期货API端点获取K线
            
            base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
            
            for symbol in ['BTCUSDT', '1000SHIBUSDT']:
                try:
                    params = {
                        'symbol': symbol,
                        'interval': '1m',
                        'limit': 1
                    }
                    url = f"{base_url}/fapi/v1/klines"
                    response = requests.get(url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        klines = response.json()
                        if klines:
                            price = float(klines[0][4])  # close price
                            print_success(f"    ✅ 期货API成功获取 {symbol} K线: ${price:,.4f}")
                        else:
                            print_warning(f"    ⚠️  {symbol} 期货API返回空数据")
                    else:
                        error = response.json() if response.text else {}
                        print_error(f"    ❌ {symbol} 期货API失败: {error.get('msg', response.status_code)}")
                except Exception as e:
                    print_error(f"    ❌ {symbol} 期货API异常: {str(e)[:100]}")
                    
        except Exception as e:
            print_error(f"期货K线API测试失败: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"交易API测试失败: {e}")
        return False

def print_summary(results):
    """打印测试总结"""
    print_section("测试总结")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print_info(f"总测试数: {total_tests}")
    print_success(f"通过测试: {passed_tests}")
    print_error(f"失败测试: {total_tests - passed_tests}")
    
    print(f"\n{Colors.BOLD}详细结果:{Colors.END}")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        color = Colors.GREEN if result else Colors.RED
        print(f"  {color}{test_name}: {status}{Colors.END}")
    
    if passed_tests == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！币安API连接正常{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  部分测试失败，请检查API配置{Colors.END}")
        print(f"\n{Colors.CYAN}💡 常见解决方案:{Colors.END}")
        print("1. 检查API密钥是否正确")
        print("2. 确认API密钥权限设置")
        print("3. 检查IP白名单设置")
        print("4. 验证系统时间同步")
        print("5. 查看币安API文档获取更多帮助")

def main():
    """主函数"""
    print_header()
    
    # 测试环境变量
    env_ok, api_key, api_secret, testnet = test_environment()
    if not env_ok:
        print_error("环境变量配置错误，无法继续测试")
        return
    
    # 执行各项测试
    results = {}
    
    # 公共API测试
    results["公共API"] = test_public_api()
    
    # 现货API测试
    if api_key and api_secret:
        results["现货API"] = test_spot_api(api_key, api_secret)
        results["合约API"] = test_futures_api(api_key, api_secret)
        results["BinanceClient类"] = test_binance_client()
        results["交易API"] = test_trading_api(api_key, api_secret)
    
    # 打印总结
    print_summary(results)

if __name__ == '__main__':
    main()
