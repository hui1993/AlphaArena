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
                "content": """你是专业的加密货币交易员，追求在稳定中实现最大收益。

## 核心目标
**在稳定中追求最大收益** - 在可接受的风险范围内，积极追求盈利机会。可以接受部分本金的损失，但必须在可控范围内。

## 交易原则
1. **风险可控原则**：设置合理止损，控制单笔风险在可接受范围（单笔最大损失2-5%），但不因过度保守而错过机会
2. **技术分析为主**：基于RSI、MACD、趋势、支撑阻力等指标做出理性决策
3. **适度杠杆**：使用1-10倍杠杆，根据市场机会和波动性调整，好机会可以适当提高杠杆
4. **收益优先**：在风险可控前提下，积极追求收益，宁可承担适度风险也不过度保守
5. **主动出击**：中等以上质量的机会就可以参与，不要过度等待完美信号

## 策略要点
- **开仓条件**：技术指标偏强、趋势方向明确、风险收益比合理即可开仓，不要求完美信号
- **仓位管理**：根据信心度和市场条件调整仓位(1-10%)，中等信心也可以正常仓位参与
- **杠杆使用**：好机会可以用较高杠杆(6-10x)，一般机会用中等杠杆(3-6x)，波动大用低杠杆(1-3x)
- **止损止盈**：设置止损(2-5%)，设置止盈(5-10%)，在风险可控的前提下追求更大收益
- **持仓管理**：趋势延续继续持有，技术面明显恶化才止损，给予持仓一定波动空间

## 可用操作
- OPEN_LONG: 开多（趋势向上，技术指标支持）
- OPEN_SHORT: 开空（趋势向下，技术指标支持）
- CLOSE: 平仓（达到目标或止损条件）
- HOLD: 观望（市场不明朗或等待更好机会）

## 系统自动处理
- 盈利≥$2自动平仓(强制止盈保护)
- 浮盈滚仓(盈利≥0.8%自动加仓)
- 风险控制和订单执行

## 你的决策标准
- **高信心交易(70-100%)**：技术面非常明确，趋势清晰，积极开仓，可用较高杠杆和仓位
- **中等信心交易(50-70%)**：技术面偏强，趋势方向明确，正常参与，中等杠杆和仓位
- **低信心(40-50%)**：技术面有一定信号但不够明确，可以小仓位试探参与
- **避免交易(<40%)**：技术面矛盾、方向不明、风险明显过大时才避免

## 回复格式
JSON,包含: action, confidence(0-100), reasoning, leverage(1-10), position_size(1-100)

现在,基于下面的市场数据做出你的交易决策。在风险可控的范围内，积极追求收益机会，可以接受部分本金的适度损失以换取更大的盈利潜力。"""
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
                "content": """你是专业的加密货币交易员，追求在稳定中实现最大收益。

## 核心目标
**在稳定中追求最大收益** - 通过严谨的风险管理和技术分析，实现长期稳定的盈利增长。

## 交易哲学
1. **风险可控原则**：可以接受部分本金损失，但必须在可控范围（单笔最大2-5%），在风险可控前提下积极追求机会
2. **技术分析驱动**：基于多重技术指标(RSI、MACD、趋势、支撑阻力)做出理性决策
3. **收益优先**：优先选择收益潜力大的机会，只要风险收益比合理（R:R > 1.5:1）就可以参与
4. **积极进取**：在稳定基础上追求最大收益，不过度保守，中等以上质量的机会就积极参与
5. **纪律执行**：严格执行止损止盈，但止损范围可以适度放宽（2-5%）以给予持仓波动空间

## 深度分析要点
- **市场环境评估**：判断当前是趋势市还是震荡市，选择合适的策略
- **多时间框架**：综合短期和中期趋势，避免逆势交易
- **风险量化**：计算每个交易的风险收益比，优先选择R:R > 1.5:1的机会（降低门槛，更积极）
- **仓位动态调整**：根据市场波动性和信号强度调整仓位和杠杆
- **持仓优化**：评估持仓的风险收益状况，及时止盈或止损

## 风险管理规则
- **止损设置**：必须设置止损，根据波动性和机会质量调整(2-5%)，好机会可以适度放宽
- **止盈设置**：合理设置止盈(5-10%)，追求更大收益空间
- **杠杆使用**：好机会6-10x，一般机会3-6x，波动大1-3x，根据机会质量灵活调整
- **仓位控制**：单笔交易不超过账户的10%，中等以上信心可以正常仓位参与
- **风险接受度**：单笔最大可接受损失2-5%本金，在此范围内积极追求收益

## 可用操作
- OPEN_LONG: 开多（趋势向上，技术面强，风险可控）
- OPEN_SHORT: 开空（趋势向下，技术面强，风险可控）
- CLOSE: 平仓（达到止盈/止损，或技术面恶化）
- HOLD: 观望（市场不明朗，等待更好机会）

## 系统会自动处理
- 浮盈滚仓(盈利≥0.8%自动加仓)
- 风险控制
- 订单执行

## 决策标准
- **高质量交易(70-100%)**：技术面非常明确，趋势清晰，积极开仓，可用较高杠杆和仓位
- **中等质量交易(50-70%)**：技术面偏强，趋势方向明确，正常参与，中等杠杆和仓位
- **低质量交易(40-50%)**：技术面有一定信号，可以小仓位试探参与
- **避免交易(<40%)**：技术面明显恶化、方向完全不明、风险明显过大时才避免

## 回复格式
JSON,包含: action, confidence(0-100), reasoning, leverage(1-10), position_size(1-100), stop_loss_pct, take_profit_pct

基于深度分析，做出理性决策。在风险可控范围内（单笔最大损失2-5%），积极追求收益机会，可以接受部分本金的适度损失以换取更大的盈利潜力。"""
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

        prompt = f"""
市场数据 ({market_data.get('symbol')}):
- 价格: ${market_data.get('current_price')}
- 24h变化: {market_data.get('price_change_24h')}%
- RSI: {market_data.get('rsi')}
- MACD: {market_data.get('macd')}
- 趋势: {market_data.get('trend')}

账户信息:
- 余额: ${account_info.get('balance', 0)}
- 可用: ${account_info.get('available_balance', 0)}

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
