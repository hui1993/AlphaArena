# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alpha Arena is a dual-system AI-powered cryptocurrency trading platform inspired by nof1.ai's Alpha Arena experiment. The repository contains:

1. **Python Legacy System**: A production-ready DeepSeek-V3 trading bot (currently operational)
2. **Next.js Modern System**: A full-stack multi-AI trading arena under development (alpha-arena-nextjs/)

Both systems trade cryptocurrency futures on Binance with AI-driven decision making, real-time monitoring, and comprehensive performance tracking.

**Primary Tech Stack**: Python 3.8+ (legacy), Next.js 15 + TypeScript + PostgreSQL (modern)

## Development Commands

### Python Legacy System (Root Directory)

```bash
# Quick start
./start.sh                          # Start trading bot
python3 alpha_arena_bot.py          # Direct bot execution

# Management
./manage.sh start                   # Start bot
./manage.sh dashboard               # Start web dashboard (Flask on port 5000)
./manage.sh logs                    # View real-time logs
./manage.sh status                  # Show performance metrics
./manage.sh stop                    # Stop bot
./manage.sh restart                 # Restart bot
./manage.sh screen                  # Start in background screen session

# Testing & Setup
python3 test_connection.py          # Test Binance and DeepSeek API connections
pip3 install -r requirements.txt    # Install dependencies

# Monitoring
tail -f logs/alpha_arena_*.log      # View logs
tail -f bot.log                     # View bot logs
tail -f dashboard.log               # View dashboard logs
python3 web_dashboard.py            # Launch Flask dashboard (http://localhost:5000)
```

### Next.js Modern System (alpha-arena-nextjs/)

```bash
cd alpha-arena-nextjs

# Development
npm run dev                         # Start Next.js dev server (http://localhost:3000)
npm run build                       # Build for production
npm run start                       # Start production server
npm run lint                        # Run ESLint

# Database
npx prisma generate                 # Generate Prisma client
npm run prisma:push                 # Push schema to database
npm run prisma:studio               # Open Prisma Studio GUI

# Trading & Testing
npm run worker                      # Run trading loop worker
npm run backtest                    # Run backtest with historical data
```

## Architecture Overview

### Python Legacy System Architecture

The system uses a layered architecture with clear separation of concerns:

**Core Components** (8 Python modules):

1. **alpha_arena_bot.py** (Main Entry Point)
   - Orchestrates all components
   - Manages 24/7 trading loop
   - Handles graceful shutdown (SIGINT/SIGTERM)
   - Configurable via environment variables

2. **ai_trading_engine.py** (AI Decision Layer)
   - Integrates DeepSeek API for trading decisions
   - Analyzes market data + technical indicators → AI decision
   - Implements 15-minute cooldown period to prevent rapid retries
   - Executes trades based on AI confidence levels

3. **deepseek_client.py** (AI Client)
   - DeepSeek API wrapper
   - Generates structured prompts with market context
   - Parses AI responses into actionable decisions
   - Returns: action, confidence, reasoning, position_size, leverage, stop_loss, take_profit

4. **binance_client.py** (Exchange Integration)
   - HMAC SHA256 signature authentication
   - Supports both spot and futures trading
   - Position management (open/close, leverage adjustment)
   - Account info, balance, K-line data retrieval
   - Testnet support via BINANCE_TESTNET env var

5. **market_analyzer.py** (Technical Analysis)
   - Technical indicators: RSI, MACD, Bollinger Bands, SMA, ATR
   - Support/resistance level detection
   - Market trend analysis
   - Real-time market data fetching

6. **risk_manager.py** (Risk Management)
   - Position sizing (max 10% per position)
   - Leverage limits (1-10x)
   - Stop-loss/take-profit calculation
   - Max drawdown protection (15%)
   - Daily loss limits (5%)
   - Position count limits (max 10 positions)

7. **performance_tracker.py** (Performance Metrics)
   - Real-time performance tracking
   - Metrics: Sharpe ratio, max drawdown, win rate, total return
   - JSON-based data persistence (performance_data.json)
   - Equity curve tracking
   - Trade history logging

8. **web_dashboard.py** (Monitoring Interface)
   - Flask web server (port 5000)
   - Real-time dashboard (auto-refresh every 10s)
   - Charts: equity curve (Chart.js)
   - Trade history table
   - Performance metrics cards

**Data Flow**:
```
Trading Loop (configurable interval, default 5 min):
  Market Data Fetch (BinanceClient)
    ↓
  Technical Analysis (MarketAnalyzer)
    ↓
  AI Decision (DeepSeekClient via AITradingEngine)
    ↓
  Risk Validation (RiskManager)
    ↓
  Trade Execution (BinanceClient)
    ↓
  Performance Tracking (PerformanceTracker)
    ↓
  Data Persistence (JSON files)
```

**Key Design Patterns**:
- **Dependency Injection**: Components passed to main bot class
- **Single Responsibility**: Each module has one clear purpose
- **Strategy Pattern**: AI decision-making as pluggable strategy
- **Observer Pattern**: Performance tracking observes trade events

### Next.js Modern System Architecture

See `alpha-arena-nextjs/CLAUDE.md` for detailed Next.js architecture documentation.

**Key Differences from Python System**:
- Multi-AI model support (DeepSeek, OpenAI, Claude) vs. single DeepSeek
- PostgreSQL database vs. JSON files
- React dashboard vs. Flask HTML templates
- Real-time WebSocket market data vs. REST polling
- Backtesting engine included
- TypeScript type safety

## Environment Configuration

### Python System (.env in root)

```env
# Binance API (REQUIRED)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=false              # true for testnet, false for mainnet

# DeepSeek API (REQUIRED)
DEEPSEEK_API_KEY=sk-your-key

# Trading Configuration
INITIAL_CAPITAL=10000              # Starting capital in USDT
MAX_POSITION_PCT=10                # Max position size (% of capital)
DEFAULT_LEVERAGE=3                 # Default leverage (1-10)
TRADING_INTERVAL_SECONDS=300       # Trading loop interval (5 min)
TRADING_SYMBOLS=BTCUSDT,ETHUSDT    # Comma-separated trading pairs
```

### Next.js System (.env.local in alpha-arena-nextjs/)

See `alpha-arena-nextjs/CLAUDE.md` for complete Next.js environment variables.

## Critical Patterns and Conventions

### Python System Conventions

**Logging**:
- All modules use Python's `logging` module
- Logs written to `logs/alpha_arena_YYYYMMDD.log`
- Console output includes timestamps and log levels
- Log rotation by date

**Error Handling**:
- All API calls wrapped in try/except
- Graceful degradation on errors
- Auto-retry with exponential backoff
- Trade cooldown on failures (15 min)

**Data Persistence**:
- Performance data: `performance_data.json`
- AI decisions: `ai_decisions.json`
- Trade history embedded in performance data
- Atomic file writes to prevent corruption

**AI Decision Structure**:
```python
{
    "action": "BUY" | "SELL" | "HOLD" | "CLOSE",
    "confidence": 0-100,  # percentage
    "reasoning": "Human-readable explanation",
    "position_size": 0-100,  # percentage of capital
    "leverage": 1-10,
    "stop_loss": 0-100,  # percentage below entry
    "take_profit": 0-100  # percentage above entry
}
```

**Position Management**:
```python
# Open long position
binance_client.open_long(
    symbol='BTCUSDT',
    quantity=0.001,  # BTC amount
    leverage=3
)

# Close all positions for symbol
binance_client.close_all_positions('BTCUSDT')

# Get current positions
positions = binance_client.get_positions()
```

**Risk Checks**:
```python
# RiskManager validates before trade execution:
# 1. Position size <= MAX_POSITION_PCT
# 2. Leverage <= max_leverage config
# 3. Current drawdown < max_drawdown threshold
# 4. Daily loss < daily_loss_limit
# 5. Total positions < max_positions

is_allowed, reason = risk_manager.check_can_open_position(
    symbol='BTCUSDT',
    side='LONG',
    size_usdt=1000
)
```

### Key Workflow: Adding a New Trading Symbol

1. Update `.env`:
   ```bash
   TRADING_SYMBOLS=BTCUSDT,ETHUSDT,NEWUSDT
   ```

2. Bot automatically picks up new symbol in next trading cycle
3. No code changes required

### Key Workflow: Adjusting Risk Parameters

Edit risk manager configuration in `alpha_arena_bot.py`:
```python
risk_config = {
    'max_portfolio_risk': 0.02,  # 2% max risk per trade
    'max_position_size': 0.1,    # 10% max position size
    'max_leverage': 10,          # Max 10x leverage
    'stop_loss_pct': 0.02,       # 2% stop loss
    'take_profit_pct': 0.05,     # 5% take profit
    'max_drawdown': 0.15,        # 15% max drawdown
    'max_positions': 10          # Max 10 concurrent positions
}
```

## Important Safety Considerations

**Real Money Trading System**: Both systems trade with real funds on Binance.

**Safety Checklist**:
1. **Always test on testnet first**: Set `BINANCE_TESTNET=true`
2. **Start with minimal capital**: Test with small amounts
3. **Monitor continuously**: Check logs and dashboard regularly
4. **Validate API keys**: Ensure keys have correct permissions (Futures trading enabled)
5. **IP whitelisting**: Add your IP to Binance API key whitelist
6. **Never commit secrets**: `.env` files are gitignored
7. **Set conservative limits**: Start with low leverage (2-3x) and small positions (5%)
8. **Emergency stop**: Keep `./manage.sh stop` or Ctrl+C readily available

**Binance API Permissions Required**:
- ✅ Enable Futures trading
- ✅ Enable Reading
- ✅ No withdrawal permissions needed (safer)
- ✅ IP whitelist recommended

## Common Development Tasks

### Running the Python Bot in Development

```bash
# Terminal 1: Start bot
./start.sh

# Terminal 2: Monitor logs
tail -f logs/alpha_arena_*.log

# Terminal 3: Web dashboard
python3 web_dashboard.py
# Visit http://localhost:5000
```

### Testing Changes Without Real Trading

1. Set `BINANCE_TESTNET=true` in `.env`
2. Get testnet API keys from https://testnet.binancefuture.com
3. Fund testnet account with fake USDT
4. Run bot normally - all trades execute on testnet

### Debugging AI Decisions

AI decisions are logged to `ai_decisions.json`:
```bash
cat ai_decisions.json | python3 -m json.tool | less
```

Each decision includes:
- Timestamp
- Symbol
- Market data snapshot
- Indicator values
- AI reasoning
- Final decision and confidence

### Modifying AI Decision Logic

Edit `deepseek_client.py` → `make_trading_decision()`:
- Modify the prompt template to change AI context
- Adjust confidence threshold requirements
- Change decision parsing logic

### Adding New Technical Indicators

1. Add indicator calculation to `market_analyzer.py`:
   ```python
   def calculate_new_indicator(self, klines):
       # Implementation
       return indicator_value
   ```

2. Include in `get_comprehensive_analysis()` return dict

3. AI will automatically receive new indicator in next decision

### Performance Monitoring

**Key Files**:
- `performance_data.json`: Current state, all metrics, trade history
- `logs/alpha_arena_*.log`: Detailed execution logs
- Web dashboard: Real-time visualization

**Key Metrics**:
- **Sharpe Ratio**: Risk-adjusted return (>1.0 good, >2.0 excellent)
- **Max Drawdown**: Peak-to-trough decline (<10% excellent, <20% acceptable)
- **Win Rate**: Percentage of profitable trades (>50% good, >60% excellent)
- **Total Return**: Overall profit/loss percentage

## Current Implementation Status

### Python Trading System ✅ (v3.5-v3.6 Production)
**Status**: Fully operational 24/7 trading bot with aggressive configuration

**Current Version**: v3.6 (2分钟超短线 + 60x杠杆 + 浮盈滚仓)

**Core Features Active**:
- ✅ DeepSeek Chat V3.1 AI decision engine
- ✅ Rolling position manager (0.8%触发, 60%加仓, 最多3次)
- ✅ ATR dynamic trailing stops (2.0x multiplier)
- ✅ Force close on $2 profit target
- ✅ ROLL state tracking (6次限制)
- ✅ Advanced position management
- ✅ Web dashboard (Flask, port 5000)
- ✅ Comprehensive performance tracking
- ✅ 60x leverage enforcement

**Key Files**:
- `alpha_arena_bot.py` - Main orchestrator (1000 lines)
- `ai_trading_engine.py` - AI decision integration (953 lines)
- `deepseek_client.py` - DeepSeek API wrapper
- `rolling_position_manager.py` - 浮盈滚仓管理
- `roll_tracker.py` - ROLL状态追踪
- `advanced_position_manager.py` - 高级仓位管理
- `trailing_stop_manager.py` - ATR动态止损
- `performance_tracker.py` - 性能指标追踪
- `web_dashboard.py` - Flask仪表板

**State Files** (auto-generated):
- `performance_data.json` - 交易记录和性能指标
- `ai_decisions.json` - AI决策历史（最近200条）
- `roll_state.json` - 滚仓状态（每个symbol的ROLL次数）
- `runtime_state.json` - 系统运行统计（可选）

### Next.js Modern System 📋 (70% Complete - Archived)
See `alpha-arena-nextjs/CLAUDE.md` for detailed status.

**Note**: 开发重心已转向Python系统的v3.x系列优化。Next.js系统作为未来多AI竞技场备选方案保留。

**Completed**: Core libraries, database schema, AI integration, backtesting
**In Progress**: API routes, React UI components
**Planned**: Multi-AI model arena, advanced analytics

## System Differences and Migration Path

**When to use Python system**:
- Immediate trading needs
- Single AI model (DeepSeek) sufficient
- Simple deployment requirements
- Familiar with Python ecosystem

**When to use Next.js system**:
- Multi-AI model comparison needed
- Advanced analytics and backtesting
- Modern web UI preferred
- Scalability and type safety important

**Migration Strategy**:
Both systems can run simultaneously. The Next.js system is designed as an enhanced replacement but is not yet feature-complete. Continue using Python system for production trading while developing Next.js features.

## File Organization

```
AlphaArena/
├── Python Trading System (Root)
│   ├── alpha_arena_bot.py          # Main bot orchestrator
│   ├── ai_trading_engine.py        # AI decision integration
│   ├── deepseek_client.py          # DeepSeek API wrapper
│   ├── binance_client.py           # Binance API wrapper
│   ├── market_analyzer.py          # Technical indicators
│   ├── risk_manager.py             # Risk management
│   ├── performance_tracker.py      # Performance metrics
│   ├── web_dashboard.py            # Flask dashboard
│   ├── start.sh                    # Quick start script
│   ├── manage.sh                   # Management utilities
│   ├── .env                        # Configuration (not in git)
│   ├── requirements.txt            # Python dependencies
│   ├── logs/                       # Log files
│   ├── templates/                  # Flask HTML templates
│   ├── performance_data.json       # Performance state
│   └── ai_decisions.json           # AI decision log
│
└── alpha-arena-nextjs/             # Next.js Modern System
    ├── app/                        # Next.js App Router
    ├── lib/                        # Core libraries
    ├── prisma/                     # Database schema
    ├── package.json                # Node dependencies
    └── CLAUDE.md                   # Next.js-specific docs
```

## Troubleshooting Common Issues

### Bot stops unexpectedly
- Check `logs/alpha_arena_*.log` for errors
- Verify API key validity and permissions
- Check Binance API rate limits
- Ensure sufficient balance in account

### DeepSeek API errors
- Verify API key in `.env`
- Check DeepSeek account balance/credits
- Review API rate limits
- Check `ai_decisions.json` for error messages

### Binance connection issues
- Verify API keys in `.env`
- Check IP whitelist on Binance
- Ensure Futures trading enabled on API key
- Test with `python3 test_connection.py`

### Dashboard not updating
- Verify `performance_data.json` exists and is valid JSON
- Check Flask server logs in `dashboard.log`
- Clear browser cache and refresh
- Ensure port 5000 not blocked by firewall

### Position execution failures
- Check account balance (need margin for futures)
- Verify minimum notional value (usually $20+ USDT)
- Check symbol is valid and trading
- Review risk manager limits in logs

## Critical Implementation Details (v3.5-v3.6)

### Rolling Position Strategy (浮盈滚仓)

**Trigger Conditions** (rolling_position_manager.py):
```python
profit_threshold_pct=0.8  # 盈利>0.8%触发滚仓
roll_ratio=0.6            # 每次用60%浮盈加仓
max_rolls=3               # 单个持仓最多滚3次
min_roll_interval_minutes=1  # 最小间隔1分钟
```

**Execution Flow** (alpha_arena_bot.py:865-947):
1. 检查滚仓条件（盈亏百分比）
2. 构建持仓信息（symbol, pnl_pct, quantity, entry_price, side）
3. 调用 `rolling_manager.should_roll_position()`
4. 如果触发：执行市价加仓单（保持同方向）
5. 记录滚仓到 `rolling_manager.record_roll(symbol)`
6. 更新 roll_tracker 状态

**ROLL State Tracking** (roll_tracker.py):
- Max rolls per position: 6次 (硬限制)
- Data file: `roll_state.json`
- Tracks: original entry price, current roll count, roll history
- Methods: `can_roll()`, `increment_roll_count()`, `get_original_entry_price()`

**Integration Points**:
- alpha_arena_bot.py:153 - RollTracker initialization
- alpha_arena_bot.py:156-162 - RollingPositionManager initialization
- alpha_arena_bot.py:372-373 - Check and execute rolling before AI evaluation
- alpha_arena_bot.py:636-811 - Legacy ROLL execution (AI-triggered)
- ai_trading_engine.py:53 - RollTracker passed to AITradingEngine

### Force Close on Profit Target

**Implementation** (alpha_arena_bot.py:830-863):
```python
PROFIT_TARGET = 2.0  # $2 USD threshold

if unrealized_pnl >= PROFIT_TARGET:
    # Execute immediate close
    close_result = self.binance.close_all_positions(symbol)
    # Bypasses AI evaluation
```

**Execution Priority**:
1. Rolling check (if position exists)
2. **Force close check** (if profit ≥ $2)
3. AI evaluation (only if not force closed)

**Integration**: alpha_arena_bot.py:376-377

### Leverage Configuration (v3.6)

**Force 60x Leverage** (ai_trading_engine.py:441-450):
```python
MAX_LEVERAGE = 60  # Hard limit
leverage = 60  # Force all positions to 60x

# Smart adjustment for Binance requirements:
min_notional = max(20, min_qty * current_price)
required_leverage = int(min_notional / amount) + 1
leverage = min(max(leverage, required_leverage), 60)
```

**Position Precision Rules** (ai_trading_engine.py:545-563, 664-681):
```python
Symbol-specific minimum quantities:
- BTCUSDT: 0.001 BTC (3 decimals)
- ETHUSDT: 0.001 ETH (3 decimals)
- BNBUSDT: 0.1 BNB (1 decimal)
- SOLUSDT: 0.1 SOL (1 decimal)
- DOGEUSDT: 1 DOGE (0 decimals, integer)
- Others: 0.1 (1 decimal default)
```

**Why Smart Adjustment**:
- Binance requires minimum notional value ($20+ USDT)
- Small accounts may need higher leverage to meet minimum
- Precision rules prevent "LOT_SIZE" errors

### AI Decision Flow (When Position Exists)

**Sequence** (alpha_arena_bot.py:330-509):
```
1. Fetch market data (ticker, price, volume)
2. Check existing position
3. IF position exists:
   a. _check_and_execute_rolling(symbol, position)
      → rolling_position_manager.should_roll_position()
      → Execute market order if conditions met

   b. _check_and_force_close_if_profit_target(symbol, position)
      → If unrealized_pnl >= $2: close_all_positions()
      → Return True (skip AI evaluation)

   c. ai_engine.analyze_position_for_closing(symbol, position, runtime_stats)
      → DeepSeek evaluates: HOLD, CLOSE, or ROLL
      → Execute based on AI decision

4. ELSE (no position):
   a. ai_engine.analyze_and_trade(symbol, max_position_pct, runtime_stats)
      → DeepSeek decides: BUY, SELL, or HOLD
      → Execute based on AI decision
```

### State File Formats

**performance_data.json**:
```json
{
  "metrics": {
    "account_value": 10250.50,
    "total_return_pct": 2.50,
    "sharpe_ratio": 1.85,
    "max_drawdown_pct": 5.2,
    "win_rate_pct": 65.0,
    "total_trades": 45
  },
  "equity_curve": [...],
  "trades": [...]
}
```

**ai_decisions.json** (最近200条):
```json
[
  {
    "timestamp": "2025-10-25T10:30:00",
    "cycle": 123,
    "account_snapshot": {...},
    "decision": {
      "symbol": "BTCUSDT",
      "action": "OPEN_LONG",
      "confidence": 75,
      "leverage": 60,
      "reasoning": "..."
    },
    "session_info": {
      "session": "Asian",
      "volatility": "low",
      "aggressive_mode": true
    },
    "position_snapshot": null
  }
]
```

**roll_state.json**:
```json
{
  "BTCUSDT": {
    "original_entry_price": 95000.0,
    "current_roll_count": 2,
    "max_rolls": 6,
    "roll_history": [
      {
        "timestamp": "2025-10-25T10:15:00",
        "current_price": 95800.0,
        "profit_pct": 0.84,
        "reinvest_amount": 50.0
      }
    ]
  }
}
```

### Critical Code References

**Main Loop** (alpha_arena_bot.py:185-231):
- Line 206: Update account status
- Line 210: Process each symbol
- Line 220: Sleep for TRADING_INTERVAL_SECONDS

**AI Trading Engine** (ai_trading_engine.py):
- Line 96-223: analyze_and_trade() - Main trading analysis
- Line 225-319: analyze_position_for_closing() - Position evaluation
- Line 537-653: _open_long_position() - Execute long with precision
- Line 655-771: _open_short_position() - Execute short with precision

**Rolling Manager** (alpha_arena_bot.py):
- Line 156-162: RollingPositionManager initialization
- Line 865-947: _check_and_execute_rolling() - Auto rolling check
- Line 636-811: execute_roll_strategy() - AI-triggered rolling

**Force Close** (alpha_arena_bot.py):
- Line 830-863: _check_and_force_close_if_profit_target()

### Important Behavioral Notes

1. **AI Has Full Autonomy**: No confidence thresholds, AI decides everything
2. **60x Leverage is Forced**: All positions use 60x regardless of AI suggestion (v3.6)
3. **$2 Profit Target Bypasses AI**: Immediate close without AI evaluation
4. **Rolling is Automatic**: Checked before AI evaluation when position exists
5. **ROLL Limit is Hard**: Max 6 rolls per position (V2.0), 3 rolls (V3.5 via RollingPositionManager)
6. **Account Display Throttled**: Only shows every 120 seconds to reduce log spam
7. **Trade Cooldown**: 15 minutes after failed trades to prevent rapid retries
8. **Dual Model System**: Chat (quick) every analysis + Reasoner (deep) every 10 minutes
