#!/usr/bin/env python3
"""
测试DeepSeek API连接
检查API密钥、网络连接和基本功能
"""

import os
import requests
import time
from dotenv import load_dotenv

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("🤖 DeepSeek API 连接测试")
    print("=" * 60)
    print(f"{Colors.END}")

def print_section(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}📋 {title}{Colors.END}")
    print("-" * 40)

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def test_api_key_config():
    """测试API密钥配置"""
    print_section("1. 环境变量检查")
    
    load_dotenv()
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    
    if not api_key:
        print_error("DEEPSEEK_API_KEY 未设置")
        print_info("请在 .env 文件中添加 DEEPSEEK_API_KEY")
        return False, None
    
    print_success(f"API Key: {api_key[:8]}...")
    
    return True, api_key

def test_zenmux_api(api_key):
    """测试ZenMux API（DeepSeek代理）"""
    print_section("2. 测试 ZenMux API")
    
    try:
        url = "https://zenmux.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "user", "content": "你好，请回复'测试成功'"}
            ],
            "stream": False
        }
        
        print_info("发送测试请求到 ZenMux...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0]['message']['content']
                print_success("ZenMux API 连接成功！")
                print_info(f"回复: {message}")
                return True
            else:
                print_error("ZenMux API 响应格式异常")
                print_info(f"响应: {response.text[:200]}")
                return False
        elif response.status_code == 401:
            print_error("API密钥无效或已过期")
            print_warning("请检查 DEEPSEEK_API_KEY 是否正确")
            return False
        elif response.status_code == 403:
            print_error("API访问被拒绝 (403 Forbidden)")
            print_warning("可能的原因:")
            print_warning("  1. API密钥没有权限")
            print_warning("  2. 账户余额不足")
            print_warning("  3. IP地址被限制")
            return False
        elif response.status_code == 429:
            print_error("API请求频率过高 (429)")
            print_warning("请稍后再试")
            return False
        else:
            print_error(f"API调用失败: HTTP {response.status_code}")
            print_info(f"响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("请求超时")
        print_warning("ZenMux服务可能响应缓慢")
        return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到 ZenMux")
        print_warning("请检查网络连接")
        return False
    except Exception as e:
        print_error(f"测试失败: {e}")
        return False

def test_official_deepseek_api(api_key):
    """测试官方DeepSeek API"""
    print_section("3. 测试官方 DeepSeek API")
    
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "你好，请回复'测试成功'"}
            ],
            "stream": False
        }
        
        print_info("发送测试请求到官方API...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0]['message']['content']
                print_success("官方 DeepSeek API 连接成功！")
                print_info(f"回复: {message}")
                return True
            else:
                print_error("官方API响应格式异常")
                print_info(f"响应: {response.text[:200]}")
                return False
        elif response.status_code == 401:
            print_error("API密钥无效或已过期")
            print_warning("请检查 DEEPSEEK_API_KEY 是否正确")
            return False
        elif response.status_code == 403:
            print_error("API访问被拒绝 (403 Forbidden)")
            print_warning("可能的原因:")
            print_warning("  1. API密钥没有权限")
            print_warning("  2. 账户余额不足")
            print_warning("  3. IP地址被限制")
            return False
        elif response.status_code == 429:
            print_error("API请求频率过高 (429)")
            print_warning("请稍后再试")
            return False
        else:
            print_error(f"API调用失败: HTTP {response.status_code}")
            print_info(f"响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("请求超时")
        print_warning("DeepSeek服务可能响应缓慢")
        return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到 DeepSeek")
        print_warning("请检查网络连接")
        return False
    except Exception as e:
        print_error(f"测试失败: {e}")
        return False

def test_deepseek_client():
    """测试DeepSeekClient类"""
    print_section("4. 测试 DeepSeekClient 类")
    
    try:
        from deepseek_client import DeepSeekClient
        
        load_dotenv()
        api_key = os.getenv('DEEPSEEK_API_KEY')
        
        if not api_key:
            print_error("无法初始化 DeepSeekClient: API密钥未设置")
            return False
        
        client = DeepSeekClient(api_key)
        
        print_info("测试 chat_completion 方法...")
        messages = [{"role": "user", "content": "你好，请回复'测试成功'"}]
        result = client.chat_completion(messages)
        
        if result and 'choices' in result:
            response = result['choices'][0]['message']['content']
            print_success("DeepSeekClient 类工作正常")
            print_info(f"回复: {response[:100]}...")
            return True
        else:
            print_error("DeepSeekClient 未返回有效响应")
            return False
            
    except ImportError:
        print_error("无法导入 deepseek_client 模块")
        print_warning("请确保 deepseek_client.py 文件存在")
        return False
    except Exception as e:
        print_error(f"DeepSeekClient 测试失败: {e}")
        return False

def print_summary(results):
    """打印测试总结"""
    print_section("测试总结")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print_info(f"总测试数: {total}")
    print_success(f"通过测试: {passed}")
    print_error(f"失败测试: {total - passed}")
    
    print(f"\n{Colors.BOLD}详细结果:{Colors.END}")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        color = Colors.GREEN if result else Colors.RED
        print(f"  {color}{test_name}: {status}{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！DeepSeek API连接正常{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  部分测试失败，请检查API配置{Colors.END}")
        
        print(f"\n{Colors.CYAN}💡 解决方案:{Colors.END}")
        print("1. 检查 DEEPSEEK_API_KEY 是否正确")
        print("2. 确认账户余额是否充足")
        print("3. 尝试使用其他DeepSeek API端点")
        print("4. 联系DeepSeek客服获取技术支持")

def main():
    print_header()
    
    # 测试配置
    config_ok, api_key = test_api_key_config()
    if not config_ok:
        return
    
    results = {}
    
    # 测试ZenMux
    results["ZenMux API"] = test_zenmux_api(api_key)
    
    # 测试官方API
    results["官方 DeepSeek API"] = test_official_deepseek_api(api_key)
    
    # 测试DeepSeekClient
    results["DeepSeekClient 类"] = test_deepseek_client()
    
    # 打印总结
    print_summary(results)
    
    # 额外建议
    if not any(results.values()):
        print(f"\n{Colors.YELLOW}{Colors.BOLD}建议:{Colors.END}")
        print("如果所有测试都失败，可以尝试:")
        print("1. 检查网络连接")
        print("2. 验证API密钥有效性")
        print("3. 查看DeepSeek账户状态")
        print("4. 考虑使用备用API提供商")

if __name__ == '__main__':
    main()

