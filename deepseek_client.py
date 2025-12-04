"""
DeepSeek API 客户端
用于 AI 交易决策
"""

import requests
import json
from typing import Dict, List, Optional
import logging
from datetime import datetime
import pytz


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self, api_key: str):
        """
        初始化 DeepSeek 客户端

        Args:
            api_key: DeepSeek API 密钥
        """
        self.api_key = api_key
        # 优先使用官方API，如果失败则使用ZenMux
        self.base_url = "https://api.deepseek.com/v1"  # 官方 DeepSeek API
        self.zenmux_url = "https://zenmux.ai/api/v1"  # ZenMux API 备用
        self.model_name = "deepseek-chat"  # 官方模型名称
        self.zenmux_model = "deepseek/deepseek-chat"  # ZenMux 模型名称
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)

    def get_trading_session(self) -> Dict:
        """获取当前交易时段信息(仅用于日志记录)"""
        try:
            utc_tz = pytz.UTC
            now_utc = datetime.now(utc_tz)
            utc_hour = now_utc.hour

            beijing_tz = pytz.timezone('Asia/Shanghai')
            now_beijing = now_utc.astimezone(beijing_tz)
            beijing_hour = now_beijing.hour

            # 欧美重叠盘
            if 13 <= utc_hour < 17:
                return {'session': '欧美重叠盘', 'volatility': 'high', 'recommendation': '最佳交易时段', 'aggressive_mode': True, 'beijing_hour': beijing_hour, 'utc_hour': utc_hour}
            # 欧洲盘
            elif 8 <= utc_hour < 13:
                return {'session': '欧洲盘', 'volatility': 'medium', 'recommendation': '较好交易时段', 'aggressive_mode': True, 'beijing_hour': beijing_hour, 'utc_hour': utc_hour}
            # 美国盘
            elif 17 <= utc_hour < 22:
                return {'session': '美国盘', 'volatility': 'medium', 'recommendation': '较好交易时段', 'aggressive_mode': True, 'beijing_hour': beijing_hour, 'utc_hour': utc_hour}
            # 亚洲盘
            else:
                return {'session': '亚洲盘', 'volatility': 'low', 'recommendation': '正常交易时段', 'aggressive_mode': True, 'beijing_hour': beijing_hour, 'utc_hour': utc_hour}
        except Exception as e:
            self.logger.error(f"获取交易时段失败: {e}")
            return {'session': '未知', 'volatility': 'unknown', 'recommendation': '谨慎交易', 'aggressive_mode': False, 'beijing_hour': 0, 'utc_hour': 0}

    def chat_completion(self, messages: List[Dict], model: str = "deepseek/deepseek-chat",
                       temperature: float = 0.7, max_tokens: int = 2000,
                       timeout: int = None, max_retries: int = 2) -> Dict:
        """
        调用 DeepSeek Chat 完成 API（带重试机制）

        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数 (0-2)
            max_tokens: 最大 token 数
            timeout: 超时时间（秒），None则自动根据模型类型设置
            max_retries: 最大重试次数

        Returns:
            API 响应
        """
        # 根据模型类型自动设置超时时间
        if timeout is None:
            timeout = 60   # Chat V3.1模型：1分钟

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # 重试机制
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.warning(f"正在重试... (第{attempt}/{max_retries}次)")

                # 首先尝试官方API
                try:
                    # 确保使用官方API的模型名称
                    official_payload = payload.copy()
                    official_payload["model"] = self.model_name
                    
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=official_payload,
                        timeout=timeout
                    )
                    response.raise_for_status()
                    result = response.json()
                except (requests.exceptions.RequestException, ValueError) as api_error:
                    # 如果官方API失败，尝试ZenMux备用
                    if attempt == 0:  # 只在第一次失败时尝试备用
                        self.logger.warning(f"官方API失败，尝试ZenMux备用: {api_error}")
                        payload["model"] = self.zenmux_model
                        response = requests.post(
                            f"{self.zenmux_url}/chat/completions",
                            headers=self.headers,
                            json=payload,
                            timeout=timeout
                        )
                        response.raise_for_status()
                        result = response.json()
                    else:
                        raise api_error

                # 记录缓存使用情况（如果API返回了缓存统计）
                if 'usage' in result:
                    usage = result['usage']
                    cache_hit = usage.get('prompt_cache_hit_tokens', 0)
                    cache_miss = usage.get('prompt_cache_miss_tokens', 0)
                    total_prompt = usage.get('prompt_tokens', 0)

                    if cache_hit > 0 or cache_miss > 0:
                        cache_rate = (cache_hit / (cache_hit + cache_miss) * 100) if (cache_hit + cache_miss) > 0 else 0
                        savings = cache_hit * 0.9  # 缓存命中节省90%成本
                        self.logger.info(f"[MONEY] 缓存统计 - 命中率: {cache_rate:.1f}% | "
                                       f"命中: {cache_hit} tokens | 未命中: {cache_miss} tokens | "
                                       f"节省约: {savings:.0f} tokens成本")

                return result

            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    self.logger.warning(f"请求超时（{timeout}秒），准备重试...")
                    continue
                else:
                    self.logger.error(f"DeepSeek API 超时失败（已重试{max_retries}次）: {e}")
                    raise

            except Exception as e:
                self.logger.error(f"DeepSeek API 调用失败: {e}")
                raise

    def reasoning_completion(self, messages: List[Dict], max_tokens: int = 4000) -> Dict:
        """使用DeepSeek-R1推理模型"""
        return self.chat_completion(
            messages=messages,
            model="deepseek/deepseek-reasoner",
            temperature=1.0,
            max_tokens=max_tokens
        )

    def analyze_market_and_decide(self, market_data: Dict,
                                  account_info: Dict,
                                  trade_history: List[Dict] = None) -> Dict:
        """
        分析市场并做出交易决策(带重试机制)
        """
        # 构建提示词
        prompt = self._build_trading_prompt(market_data, account_info, trade_history)

        messages = [
            {
                "role": "system",
                "content": """你是专业的加密货币交易员，根据账户规模动态调整策略。

## 核心策略原则（根据账户规模动态调整）

### 小账户策略（余额 < $1000）- 激进增长模式
**目标：快速滚大账户，小钱变中钱**
- **核心思想**：小账户必须激进才能快速成长，宁可承担较大风险也要抓住机会
- **杠杆使用**：积极使用高杠杆(8-10x)，好机会必须用满杠杆，一般机会也用6-8x
- **仓位管理**：大仓位参与(8-15%)，高信心机会可以用到15-20%仓位
- **开仓条件**：降低门槛，技术面偏强即可开仓，不要过度等待完美信号
- **止损止盈**：止损放宽(3-8%)，止盈提高(10-20%)，给予持仓更大波动空间
- **风险接受度**：可以接受单笔最大损失5-10%，追求高风险高收益

### 大账户策略（余额 >= $1000）- 稳健增长模式
**目标：稳定增长，保护已有收益**
- **核心思想**：大账户优先保护本金，稳健增长，避免大幅回撤
- **杠杆使用**：适度使用杠杆(3-6x)，好机会用6x，一般机会用3-4x
- **仓位管理**：中等仓位参与(5-10%)，高信心机会最多10%
- **开仓条件**：提高门槛，需要技术面明确、趋势清晰才开仓
- **止损止盈**：严格止损(2-4%)，合理止盈(5-10%)，及时锁定利润
- **风险接受度**：单笔最大损失控制在2-5%，优先保护本金

## 通用交易原则
1. **技术分析为主**：基于RSI、MACD、趋势、支撑阻力等指标做出理性决策
2. **市场环境判断**：趋势市积极开仓，震荡市谨慎观望
3. **风险收益比**：小账户追求R:R > 1:1即可，大账户要求R:R > 1.5:1
4. **主动出击**：小账户不要过度等待，大账户可以更谨慎

## 可用操作
- OPEN_LONG: 开多（趋势向上，技术指标支持）
- OPEN_SHORT: 开空（趋势向下，技术指标支持）
- CLOSE: 平仓（达到目标或止损条件）
- HOLD: 观望（市场不明朗或等待更好机会）

## 系统自动处理
- 盈利≥$2自动平仓(强制止盈保护)
- 浮盈滚仓(盈利≥0.8%自动加仓)
- 风险控制和订单执行

## 决策标准（根据账户规模调整）

### 小账户决策标准
- **高信心交易(60-100%)**：技术面明确即可，积极开仓，用高杠杆(8-10x)和大仓位(10-15%)
- **中等信心交易(40-60%)**：技术面偏强即可参与，用中高杠杆(6-8x)和中等仓位(8-12%)
- **低信心(30-40%)**：有一定信号就可以小仓位试探，用中等杠杆(5-6x)和小仓位(5-8%)
- **避免交易(<30%)**：只有技术面完全矛盾、方向完全不明时才避免

### 大账户决策标准
- **高信心交易(70-100%)**：技术面非常明确，趋势清晰，用中等杠杆(5-6x)和中等仓位(8-10%)
- **中等信心交易(50-70%)**：技术面偏强，趋势方向明确，用低中杠杆(3-5x)和小中仓位(5-8%)
- **低信心(40-50%)**：技术面有一定信号，可以小仓位试探，用低杠杆(2-3x)和小仓位(3-5%)
- **避免交易(<40%)**：技术面不够明确时避免交易

## 回复格式
JSON,包含: action, confidence(0-100), reasoning, leverage(1-10), position_size(1-100), stop_loss_pct, take_profit_pct

**重要**：根据提示词中的账户规模信息，动态调整你的策略。小账户要激进快速滚大，大账户要稳健保护收益。"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # 重试最多2次
        for attempt in range(2):
            try:
                self.logger.info(f"API调用尝试 {attempt + 1}/2...")
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    timeout=180  # 增加到180秒
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']

                    # 解析AI返回
                    decision = self._parse_decision(content)
                    self.logger.info(f"✅ API调用成功 (尝试{attempt + 1})")
                    return {
                        'success': True,
                        'decision': decision,
                        'raw_response': content,
                        'model_used': 'deepseek-chat'
                    }
                else:
                    self.logger.error(f"API错误 {response.status_code}: {response.text}")
                    if attempt < 1:  # 如果还有重试机会
                        continue
                    return {
                        'success': False,
                        'error': f"API错误: {response.status_code}"
                    }

            except requests.exceptions.Timeout as e:
                self.logger.error(f"⏰ API超时 (尝试{attempt + 1}/2): {e}")
                if attempt < 1:  # 如果还有重试机会
                    continue
                return {
                    'success': False,
                    'error': 'API超时,请稍后重试'
                }
            except Exception as e:
                self.logger.error(f"❌ API异常 (尝试{attempt + 1}/2): {e}")
                if attempt < 1:
                    continue
                return {
                    'success': False,
                    'error': str(e)
                }

        # 不应该到达这里
        return {
            'success': False,
            'error': '所有重试均失败'
        }

    def evaluate_position_for_closing(self, position_info: Dict, market_data: Dict, account_info: Dict, roll_tracker=None) -> Dict:
        """评估持仓是否应该平仓"""
        
        # 获取ROLL状态信息
        symbol = position_info.get('symbol', '')
        roll_count = 0
        if roll_tracker:
            roll_count = roll_tracker.get_roll_count(symbol)
        
        prompt = f"""当前持有 {position_info['symbol']} {'多单' if position_info['side'] == 'LONG' else '空单'}:
- 入场价: ${position_info['entry_price']}
- 当前价: ${position_info['current_price']}
- 盈亏: {position_info['unrealized_pnl_pct']:+.2f}%
- 杠杆: {position_info['leverage']}x
- 持仓时长: {position_info['holding_time']}
- 滚仓次数: {roll_count}/3

市场数据:
- RSI: {market_data.get('rsi')}
- MACD: {market_data.get('macd', {}).get('histogram', 'N/A')}
- 趋势: {market_data.get('trend')}
- 24h变化: {market_data.get('price_change_24h')}%

系统已配置:
- 盈利≥0.8%自动滚仓(系统处理)
- 最多滚3次

决定: CLOSE平仓 或 HOLD继续持有?"""

        messages = [
            {
                "role": "system",
                "content": """你是专业交易员。评估是否应该平仓。

## 回复格式
JSON: {"action": "CLOSE或HOLD", "confidence": 0-100, "narrative": "决策说明"}"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=180  # 统一增加到180秒
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                decision = self._parse_decision(content)
                return decision
            else:
                return {"action": "HOLD", "confidence": 0, "narrative": "API错误"}
        except Exception as e:
            self.logger.error(f"评估持仓异常: {e}")
            return {"action": "HOLD", "confidence": 0, "narrative": f"异常: {str(e)}"}

    def analyze_with_reasoning(self, market_data: Dict, account_info: Dict,
                               trade_history: List[Dict] = None,
                               use_deepthink: bool = False) -> Dict:
        """使用推理模型分析市场"""
        prompt = self._build_trading_prompt(market_data, account_info, trade_history)
        
        messages = [
            {
                "role": "system",
                "content": """你是专业的加密货币交易员，根据账户规模动态调整策略。

## 核心策略原则（根据账户规模动态调整）

### 小账户策略（余额 < $1000）- 激进增长模式
**目标：快速滚大账户，小钱变中钱**
- **核心思想**：小账户必须激进才能快速成长，宁可承担较大风险也要抓住机会
- **杠杆使用**：积极使用高杠杆(8-10x)，好机会必须用满杠杆，一般机会也用6-8x
- **仓位管理**：大仓位参与(8-15%)，高信心机会可以用到15-20%仓位
- **开仓条件**：降低门槛，技术面偏强即可开仓，不要过度等待完美信号
- **止损止盈**：止损放宽(3-8%)，止盈提高(10-20%)，给予持仓更大波动空间
- **风险接受度**：可以接受单笔最大损失5-10%，追求高风险高收益

### 大账户策略（余额 >= $1000）- 稳健增长模式
**目标：稳定增长，保护已有收益**
- **核心思想**：大账户优先保护本金，稳健增长，避免大幅回撤
- **杠杆使用**：适度使用杠杆(3-6x)，好机会用6x，一般机会用3-4x
- **仓位管理**：中等仓位参与(5-10%)，高信心机会最多10%
- **开仓条件**：提高门槛，需要技术面明确、趋势清晰才开仓
- **止损止盈**：严格止损(2-4%)，合理止盈(5-10%)，及时锁定利润
- **风险接受度**：单笔最大损失控制在2-5%，优先保护本金

## 深度分析要点
- **市场环境评估**：判断当前是趋势市还是震荡市，选择合适的策略
- **多时间框架**：综合短期和中期趋势，避免逆势交易
- **风险量化**：小账户追求R:R > 1:1即可，大账户要求R:R > 1.5:1
- **仓位动态调整**：根据账户规模和信号强度调整仓位和杠杆
- **持仓优化**：评估持仓的风险收益状况，及时止盈或止损

## 通用交易原则
1. **技术分析驱动**：基于多重技术指标(RSI、MACD、趋势、支撑阻力)做出理性决策
2. **主动出击**：小账户不要过度等待，大账户可以更谨慎
3. **纪律执行**：严格执行止损止盈，但根据账户规模调整止损范围

## 可用操作
- OPEN_LONG: 开多（趋势向上，技术指标支持）
- OPEN_SHORT: 开空（趋势向下，技术指标支持）
- CLOSE: 平仓（达到止盈/止损，或技术面恶化）
- HOLD: 观望（市场不明朗，等待更好机会）

## 系统会自动处理
- 浮盈滚仓(盈利≥0.8%自动加仓)
- 风险控制
- 订单执行

## 决策标准（根据账户规模调整）

### 小账户决策标准
- **高信心交易(60-100%)**：技术面明确即可，积极开仓，用高杠杆(8-10x)和大仓位(10-15%)
- **中等信心交易(40-60%)**：技术面偏强即可参与，用中高杠杆(6-8x)和中等仓位(8-12%)
- **低信心(30-40%)**：有一定信号就可以小仓位试探，用中等杠杆(5-6x)和小仓位(5-8%)
- **避免交易(<30%)**：只有技术面完全矛盾、方向完全不明时才避免

### 大账户决策标准
- **高信心交易(70-100%)**：技术面非常明确，趋势清晰，用中等杠杆(5-6x)和中等仓位(8-10%)
- **中等信心交易(50-70%)**：技术面偏强，趋势方向明确，用低中杠杆(3-5x)和小中仓位(5-8%)
- **低信心(40-50%)**：技术面有一定信号，可以小仓位试探，用低杠杆(2-3x)和小仓位(3-5%)
- **避免交易(<40%)**：技术面不够明确时避免交易

## 回复格式
JSON,包含: action, confidence(0-100), reasoning, leverage(1-10), position_size(1-100), stop_loss_pct, take_profit_pct

**重要**：根据提示词中的账户规模信息，动态调整你的策略。小账户要激进快速滚大，大账户要稳健保护收益。基于深度分析，做出理性决策。"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self.reasoning_completion(messages, max_tokens=8000)
            
            if 'error' in response:
                return {
                    'success': False,
                    'error': response['error']
                }
            
            content = response['choices'][0]['message']['content']
            decision = self._parse_decision(content)
            
            return {
                'success': True,
                'decision': decision,
                'raw_response': content
            }

        except Exception as e:
            self.logger.error(f"AI 决策失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _build_trading_prompt(self, market_data: Dict,
                             account_info: Dict,
                             trade_history: List[Dict] = None) -> str:
        """构建交易提示词"""
        
        balance = account_info.get('balance', 0)
        # 判断账户规模：小于$1000为小账户，需要激进策略快速滚大
        is_small_account = balance < 1000
        account_size = "小账户" if is_small_account else "大账户"
        strategy_mode = "激进增长模式" if is_small_account else "稳健增长模式"

        prompt = f"""
市场数据 ({market_data.get('symbol')}):
- 价格: ${market_data.get('current_price')}
- 24h变化: {market_data.get('price_change_24h')}%
- RSI: {market_data.get('rsi')}
- MACD: {market_data.get('macd')}
- 趋势: {market_data.get('trend')}

账户信息:
- 余额: ${balance:,.2f}
- 可用: ${account_info.get('available_balance', 0):,.2f}
- 账户规模: {account_size} ({strategy_mode})

做出你的交易决策。"""

        return prompt

    def _parse_decision(self, content: str) -> Dict:
        """解析AI返回的决策"""
        try:
            # 尝试直接解析JSON
            import re
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                return {
                    "action": decision.get("action", "HOLD"),
                    "confidence": decision.get("confidence", 50),
                    "reasoning": decision.get("reasoning", decision.get("narrative", content[:200])),
                    "leverage": decision.get("leverage", 10),
                    "position_size": decision.get("position_size", 30),
                    "stop_loss_pct": decision.get("stop_loss_pct", 3),
                    "take_profit_pct": decision.get("take_profit_pct", 8),
                    "narrative": decision.get("narrative", decision.get("reasoning", ""))
                }
        except Exception as e:
            self.logger.error(f"解析AI决策失败: {e}")

        # 默认返回
        return {
            "action": "HOLD",
            "confidence": 50,
            "reasoning": content[:200] if content else "无法解析",
            "leverage": 10,
            "position_size": 30,
            "stop_loss_pct": 3,
            "take_profit_pct": 8
        }
