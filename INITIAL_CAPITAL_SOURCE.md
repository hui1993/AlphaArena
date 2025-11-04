# 初始资金数据来源说明

## 📊 数据来源优先级

初始资金的获取遵循以下优先级顺序：

### 1. **Binance API 实时余额**（优先）⭐

**位置**: 
- `alpha_arena_bot.py` (第150-159行)
- `web_dashboard.py` (第50-62行)

**获取方式**:
```python
actual_balance = self.binance.get_futures_usdt_balance()
self.initial_capital = actual_balance
```

**说明**:
- 从 Binance Futures API 获取合约账户的 USDT 余额
- 这是**真实账户余额**，作为初始资金的基准
- 如果获取成功，会覆盖配置文件中的值

### 2. **配置文件默认值**（备用）

**位置**: 
- `config.py` (第41行)
- `.env` 文件中的 `INITIAL_CAPITAL` 环境变量

**默认值**:
```python
INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '20'))
```

**说明**:
- 仅在 Binance API 获取失败时使用
- `.env` 文件中的值优先级高于代码默认值
- 如果 `.env` 中未设置，使用代码默认值 `20`

### 3. **performance_data.json 存储值**（历史记录）

**位置**: `performance_data.json` 文件

**字段**:
```json
{
  "initial_capital": 0.0,
  "portfolio_values": [...]
}
```

**说明**:
- 首次运行时，会保存当时获取的初始资金值
- 如果文件中的 `initial_capital` 为 `0.0`，表示可能是首次运行或数据异常
- 前端图表会读取这个值，如果为 0，会尝试从 Binance API 重新获取

---

## 🔄 数据流

### Alpha Arena Bot 启动流程

```
1. 读取 .env 配置
   └─> INITIAL_CAPITAL=20 (默认值)
   
2. 初始化 Binance 客户端
   └─> 连接 Binance Futures API
   
3. 获取实际余额
   └─> get_futures_usdt_balance()
       ├─> 成功: 使用实际余额作为 initial_capital
       └─> 失败: 使用配置文件值 (20)
       
4. 初始化 PerformanceTracker
   └─> 传入 initial_capital
   
5. 保存到 performance_data.json
   └─> {"initial_capital": 实际值}
```

### Web Dashboard 启动流程

```
1. 初始化客户端
   └─> init_clients()
   
2. 获取 Binance 余额
   └─> binance_client.get_futures_usdt_balance()
       ├─> 成功: 使用实际余额
       └─> 失败: 使用环境变量 INITIAL_CAPITAL (默认 10000)
       
3. 初始化 PerformanceTracker
   └─> 传入 initial_capital
   
4. /api/chart 接口
   └─> 读取 performance_data.json
       ├─> 如果 initial_capital == 0.0
       │   └─> 尝试从 Binance API 重新获取
       └─> 返回给前端
```

---

## 📝 代码位置

### 1. Bot 主程序 (`alpha_arena_bot.py`)

```python
# 第150-159行
# [NEW] 从Binance API获取实际账户余额，替代配置文件中的初始资金
try:
    actual_balance = self.binance.get_futures_usdt_balance()
    self.logger.info(f"[OK] 实际余额: ${actual_balance:,.2f}")
    # 使用实际余额替代配置文件值
    self.initial_capital = actual_balance
except Exception as e:
    self.logger.warning(f"[WARNING] 无法获取Binance余额，使用配置文件值: {e}")
    # 回退到配置文件值
    pass

# 第179-182行
# 性能追踪器（使用实际余额）
self.performance = PerformanceTracker(
    initial_capital=self.initial_capital,
    data_file='performance_data.json'
)
```

### 2. Web Dashboard (`web_dashboard.py`)

```python
# 第50-62行
if performance_tracker is None:
    # [NEW] 从Binance API获取实际余额，替代配置文件
    try:
        initial_capital = binance_client.get_futures_usdt_balance()
        print(f"[OK] Web仪表板: 从Binance API获取实际余额: ${initial_capital:,.2f}")
    except Exception as e:
        print(f"[WARNING] 无法获取Binance余额，使用配置文件默认值: {e}")
        initial_capital = float(os.getenv('INITIAL_CAPITAL', 10000))

    performance_tracker = PerformanceTracker(
        initial_capital=initial_capital,
        data_file='performance_data.json'
    )

# 第209-218行 (API 接口)
# 如果初始资金为0，尝试从Binance获取当前余额作为初始资金
if initial_capital == 0.0:
    try:
        account_info = binance_client.get_futures_account_info()
        total_wallet_balance = float(account_info.get('totalWalletBalance', 0))
        if total_wallet_balance > 0:
            initial_capital = total_wallet_balance
    except Exception:
        pass
```

### 3. 配置文件 (`config.py`)

```python
# 第41行
INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '20'))
```

### 4. 性能追踪器 (`performance_tracker.py`)

```python
# 第17-30行
def __init__(self, initial_capital: float = 10000.0, data_file: str = 'performance_data.json'):
    self.initial_capital = initial_capital
    self.data_file = data_file
    # ...
    self.data = self._load_data()  # 加载历史数据

def _load_data(self) -> Dict:
    if os.path.exists(self.data_file):
        # 加载已有数据（包含历史 initial_capital）
        ...
    else:
        # 首次运行，保存新的 initial_capital
        return {
            'initial_capital': self.initial_capital,
            ...
        }
```

---

## ⚠️ 注意事项

1. **首次运行**: 
   - 如果 `performance_data.json` 不存在，会创建新文件并保存初始资金
   - 如果文件已存在，会读取文件中的 `initial_capital` 值（可能已过时）

2. **数据不一致**:
   - Bot 和 Dashboard 可能使用不同的初始资金值（如果它们在不同时间启动）
   - Bot 启动时获取的余额会被保存到 `performance_data.json`
   - Dashboard 启动时也会尝试获取余额，但不会覆盖已保存的值

3. **值为 0.0 的情况**:
   - 如果 `performance_data.json` 中的 `initial_capital` 为 `0.0`，可能是：
     - 首次运行时的默认值
     - 数据文件损坏
     - API 获取失败时的异常值

4. **建议**:
   - 定期检查 `performance_data.json` 中的 `initial_capital` 是否正确
   - 如果发现异常，可以手动修改或删除文件让系统重新初始化

---

## 🔍 如何查看当前初始资金

### 方法1: 查看 performance_data.json
```bash
cat performance_data.json | grep initial_capital
```

### 方法2: 查看日志
```bash
# Bot 启动日志
grep "实际余额" logs/alpha_arena_*.log

# Dashboard 启动日志
grep "实际余额" logs/web_dashboard.log
```

### 方法3: 通过 API
```bash
curl http://localhost:5000/api/chart | jq .initial_capital
```

---

## 📌 总结

**初始资金的最终来源**:
1. **运行时**: Binance API 获取的实际余额（优先）
2. **配置**: `.env` 文件中的 `INITIAL_CAPITAL`（备用）
3. **历史**: `performance_data.json` 中保存的值（用于图表显示）

**最佳实践**:
- 让系统自动从 Binance API 获取初始资金（最准确）
- 只在 API 不可用时才依赖配置文件
- 定期检查 `performance_data.json` 中的数据是否正确

