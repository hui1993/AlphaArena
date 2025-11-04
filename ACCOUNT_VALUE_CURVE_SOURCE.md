# 账户价值曲线数据来源说明

## 📊 数据来源和流程

### 数据生成流程

```
Alpha Arena Bot 主循环
  ↓
每60秒调用 _update_account_status()
  ↓
从 Binance API 获取数据
  ├─> get_futures_usdt_balance() → 钱包余额
  └─> get_active_positions() → 持仓列表
  ↓
计算账户总价值
  total_value = balance + unrealized_pnl
  ↓
调用 performance.update_portfolio_value(total_value)
  ↓
保存到 performance_data.json
  {
    "portfolio_values": [
      {
        "time": "2025-11-04T17:38:48.682412",
        "value": 29.56,
        "return_pct": 12.94
      },
      ...
    ]
  }
```

---

## 🔍 详细说明

### 1. 数据记录（Bot 主程序）

**位置**: `alpha_arena_bot.py` 第326-347行

```python
def _update_account_status(self):
    """更新账户状态"""
    # 获取余额
    balance = self.binance.get_futures_usdt_balance()
    
    # 获取持仓
    positions = self.binance.get_active_positions()
    
    # 计算总价值
    unrealized_pnl = sum(float(pos.get('unRealizedProfit', 0)) for pos in positions)
    total_value = balance + unrealized_pnl
    
    # 更新性能追踪
    self.performance.update_portfolio_value(total_value)
```

**更新频率**: 每 **60秒** 更新一次

**计算公式**:
```python
total_value = 钱包余额 + 未实现盈亏总和
```

**数据来源**:
- `钱包余额`: Binance API `get_futures_usdt_balance()` → `totalWalletBalance`
- `未实现盈亏`: Binance API `get_active_positions()` → 所有持仓的 `unRealizedProfit` 总和

---

### 2. 数据存储（性能追踪器）

**位置**: `performance_tracker.py` 第143-162行

```python
def update_portfolio_value(self, current_value: float):
    """
    更新组合价值
    
    Args:
        current_value: 当前总价值
    """
    snapshot = {
        'time': datetime.now().isoformat(),
        'value': current_value,
        'return_pct': ((current_value - self.initial_capital) / self.initial_capital) * 100
    }
    
    self.data['portfolio_values'].append(snapshot)
    
    # 只保留最近 10000 个数据点
    if len(self.data['portfolio_values']) > 10000:
        self.data['portfolio_values'] = self.data['portfolio_values'][-10000:]
    
    self._save_data()  # 保存到 performance_data.json
```

**数据结构**:
```json
{
  "time": "2025-11-04T17:38:48.682412",  // ISO格式时间戳
  "value": 29.56,                         // 账户总价值（美元）
  "return_pct": 12.94                     // 相对于初始资金的收益率（%）
}
```

**存储限制**: 最多保留最近 **10,000** 个数据点（自动清理旧数据）

---

### 3. 数据读取（Web Dashboard API）

**位置**: `web_dashboard.py` 第196-240行

#### 方式1: REST API (`/api/chart`)

```python
@app.route('/api/chart')
def get_chart_data():
    """获取图表数据 API"""
    with open('performance_data.json', 'r') as f:
        data = json.load(f)
    
    portfolio_values = data.get('portfolio_values', [])
    initial_capital = data.get('initial_capital', 0.0)
    
    # 返回最近 500 个数据点
    return jsonify({
        'success': True,
        'data': portfolio_values[-500:],
        'initial_capital': initial_capital
    })
```

**返回数据**: 最近 **500** 个数据点

#### 方式2: WebSocket 推送 (`chart_update`)

**位置**: `web_dashboard.py` 第555-574行

```python
# 推送图表数据
with open('performance_data.json', 'r') as f:
    chart_data = json.load(f)
portfolio_values = chart_data.get('portfolio_values', [])

socketio.emit('chart_update', {
    'success': True,
    'data': portfolio_values[-500:],  # 最近500个数据点
    'initial_capital': initial_capital,
    'timestamp': datetime.now().timestamp()
})
```

**推送频率**: 每 **500ms** 推送一次（实时更新）

---

### 4. 前端显示（Dashboard）

**位置**: `templates/dashboard.html`

#### 数据获取

```javascript
// 方式1: 轮询（每10秒）
function updateChart() {
    fetch('/api/chart')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const data = result.data;  // portfolio_values
                const initialCapital = result.initial_capital;
                // 渲染图表...
            }
        });
}

// 方式2: WebSocket（实时）
socket.on('chart_update', function(result) {
    if (result.success) {
        const data = result.data;  // portfolio_values
        const initialCapital = result.initial_capital;
        // 实时更新图表...
    }
});
```

#### 图表渲染

使用 **Chart.js** 渲染折线图：
- X轴: 时间（从 `time` 字段解析）
- Y轴: 账户价值（从 `value` 字段）

---

## 📈 数据字段说明

### portfolio_values 数组中的每个对象

| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| `time` | String | ISO格式时间戳 | `datetime.now().isoformat()` |
| `value` | Float | 账户总价值（美元） | `balance + unrealized_pnl` |
| `return_pct` | Float | 收益率（%） | `(value - initial_capital) / initial_capital * 100` |

### 计算示例

```
初始资金: $20.00
当前钱包余额: $26.18
未实现盈亏: +$3.39
账户总价值: $26.18 + $3.39 = $29.57

收益率: ($29.57 - $20.00) / $20.00 * 100% = 47.85%
```

---

## 🔄 完整数据流

```
1. Bot 主循环（每60秒）
   └─> _update_account_status()
       ├─> Binance API: get_futures_usdt_balance()
       │   └─> 返回: balance = $26.18
       ├─> Binance API: get_active_positions()
       │   └─> 返回: positions = [...]
       │       └─> 计算: unrealized_pnl = sum(unRealizedProfit)
       └─> 计算: total_value = balance + unrealized_pnl
           └─> total_value = $29.57
   
2. 性能追踪器
   └─> update_portfolio_value($29.57)
       ├─> 创建快照: {time, value, return_pct}
       ├─> 追加到 portfolio_values[]
       └─> 保存到 performance_data.json
   
3. Web Dashboard
   ├─> REST API: GET /api/chart
   │   └─> 读取 performance_data.json
   │       └─> 返回: portfolio_values[-500:]
   │
   └─> WebSocket: chart_update (每500ms)
       └─> 读取 performance_data.json
           └─> 推送: portfolio_values[-500:]
   
4. 前端显示
   └─> Chart.js 渲染折线图
       ├─> X轴: 时间（time字段）
       └─> Y轴: 账户价值（value字段）
```

---

## ⚙️ 关键配置

### 更新频率

| 组件 | 频率 | 说明 |
|------|------|------|
| Bot 数据记录 | 每 60 秒 | `alpha_arena_bot.py` 主循环 |
| WebSocket 推送 | 每 500ms | `web_dashboard.py` 后台线程 |
| 前端轮询 | 每 10 秒 | `dashboard.html` 备用方案 |

### 数据限制

| 限制项 | 数值 | 位置 |
|--------|------|------|
| 最大存储点数 | 10,000 | `performance_tracker.py` |
| API 返回点数 | 500 | `web_dashboard.py` |
| WebSocket 推送点数 | 500 | `web_dashboard.py` |

---

## 📝 数据文件位置

**主数据文件**: `performance_data.json`

**文件结构**:
```json
{
  "start_time": "2025-10-29T16:36:47.508164",
  "initial_capital": 0.0,
  "portfolio_values": [
    {
      "time": "2025-11-04T17:38:48.682412",
      "value": 29.56,
      "return_pct": 12.94
    },
    ...
  ],
  "trades": [...],
  "metrics": {...}
}
```

---

## 🔍 数据验证

### 检查数据是否正常更新

```bash
# 查看最新数据点
python3 -c "import json; data = json.load(open('performance_data.json')); pv = data.get('portfolio_values', []); print(f'Total points: {len(pv)}'); print(f'Latest: {pv[-1] if pv else \"N/A\"}')"

# 查看数据更新时间
ls -lh performance_data.json
```

### 检查 Bot 是否在运行

```bash
# 查看进程
ps aux | grep alpha_arena_bot

# 查看日志
tail -f logs/alpha_arena_*.log | grep "账户状态"
```

---

## ⚠️ 注意事项

1. **数据更新延迟**:
   - Bot 每60秒更新一次数据
   - 如果 Bot 停止运行，数据不会更新
   - 前端显示的是最后记录的数据点

2. **数据准确性**:
   - 数据来自 Binance API，反映实时账户状态
   - 账户总价值 = 钱包余额 + 未实现盈亏
   - 包含所有持仓的浮盈/浮亏

3. **数据清理**:
   - 自动保留最近10,000个数据点
   - 旧数据会被自动删除（FIFO）
   - API 只返回最近500个数据点

4. **初始资金**:
   - 如果 `initial_capital` 为 0，会尝试从 Binance API 获取
   - 收益率计算基于 `initial_capital`

---

## 📌 总结

**账户价值曲线数据来源**:
1. **数据源**: Binance Futures API
   - `totalWalletBalance` (钱包余额)
   - `unRealizedProfit` (未实现盈亏)

2. **计算**: `total_value = balance + unrealized_pnl`

3. **记录**: Bot 每60秒调用 `update_portfolio_value()`

4. **存储**: `performance_data.json` 的 `portfolio_values` 字段

5. **显示**: 前端通过 `/api/chart` 或 WebSocket `chart_update` 获取数据

6. **渲染**: Chart.js 渲染折线图

**数据流**: Binance API → Bot计算 → 性能追踪器 → JSON文件 → Dashboard API → 前端图表

