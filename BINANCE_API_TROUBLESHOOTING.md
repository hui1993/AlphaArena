# Binance API Authentication Troubleshooting Guide

## Current Issue
Your AlphaArena trading bot is experiencing a **401 Unauthorized** error with Binance API:
```
API请求失败: 401 Client Error: Unauthorized for url: https://fapi.binance.com/fapi/v2/positionRisk
详细信息: {'code': -2015, 'msg': 'Invalid API-key, IP, or permissions for action'}
```

## Diagnosis Results
✅ **API Key**: Present and correctly formatted (64 characters)  
✅ **Public API**: Working (can fetch BTC price)  
❌ **Authenticated API**: Failing (account info, positions)  
❌ **Error Code**: -2015 (Invalid API-key, IP, or permissions)

## Root Cause Analysis
The error code **-2015** specifically indicates one of these issues:

### 1. **IP Address Not Whitelisted** (Most Likely)
- Binance API keys can be restricted to specific IP addresses
- Your current IP is not in the whitelist

### 2. **Insufficient API Permissions**
- API key lacks "Futures Trading" permissions
- API key might be restricted to "Spot Trading" only

### 3. **Wrong Environment**
- Using mainnet API key on testnet or vice versa
- Currently configured for mainnet (`BINANCE_TESTNET=false`)

## Step-by-Step Solution

### Step 1: Check Your Current IP Address
```bash
curl -s https://api.ipify.org
```

### Step 2: Verify Binance API Key Settings
1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Find your API key: `rDuvwB1p...`
3. Check the following settings:

#### Required Permissions:
- ✅ **Enable Reading** (for account info)
- ✅ **Enable Futures** (for futures trading)
- ✅ **Enable Spot & Margin Trading** (if using spot)

#### IP Restrictions:
- **Option A**: Remove IP restrictions (allow all IPs)
- **Option B**: Add your current IP to whitelist

### Step 3: Test Different Scenarios

#### Test A: Remove IP Restrictions
1. In Binance API settings, set "Restrict access to trusted IPs only" to **OFF**
2. Save changes
3. Wait 5 minutes for changes to take effect
4. Test again:
```bash
python3 test_api_connection.py
```

#### Test B: Add IP to Whitelist
1. Get your IP: `curl -s https://api.ipify.org`
2. Add this IP to "Restrict access to trusted IPs only"
3. Save changes
4. Wait 5 minutes
5. Test again

#### Test C: Use Testnet (Safer Option)
1. Create a new API key on [Binance Testnet](https://testnet.binancefuture.com/)
2. Update your `.env` file:
```bash
BINANCE_TESTNET=true
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_secret
```
3. Test with testnet

### Step 4: Verify API Key Permissions
Ensure your API key has these permissions:
- **Enable Reading**: Required for account info
- **Enable Futures**: Required for futures trading
- **Enable Spot & Margin Trading**: Required for spot trading

## Quick Fix Commands

### Option 1: Test with Testnet (Recommended for Testing)
```bash
# Update .env file
echo "BINANCE_TESTNET=true" >> .env
# Then test
python3 test_api_connection.py
```

### Option 2: Check Current Configuration
```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Testnet Mode:', os.getenv('BINANCE_TESTNET', 'false'))
print('API Key:', os.getenv('BINANCE_API_KEY', 'NOT SET')[:8] + '...')
"
```

## Expected Results After Fix
When the API is working correctly, you should see:
```
✅ Public API successful! BTC Price: $113,444.20
✅ Authenticated API successful!
   Total Wallet Balance: $XX,XXX.XX
✅ Position risk API successful! Found X positions
```

## Additional Troubleshooting

### If Still Getting 401 Errors:
1. **Wait 5-10 minutes** after changing API settings
2. **Check API key status** - ensure it's not disabled
3. **Verify secret key** - ensure it matches the API key
4. **Check account status** - ensure Binance account is not restricted

### If Getting 403 Forbidden:
- API key lacks required permissions
- Enable "Futures Trading" permission

### If Getting 429 Rate Limit:
- Too many API requests
- Wait before retrying

## Next Steps
1. Fix the API authentication issue using the steps above
2. Test API connection with:
   ```bash
   python3 -c "
   from binance_client import BinanceClient
   import os
   from dotenv import load_dotenv
   load_dotenv()
   client = BinanceClient(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
   print('Account Balance:', client.get_futures_account_info().get('totalWalletBalance', 0))
   "
   ```
3. Once working, you can start the trading bot:
   ```bash
   python3 alpha_arena_bot.py
   ```
4. Access the web dashboard at: `http://localhost:5002`

## Support
If issues persist after following these steps:
1. Check Binance API documentation
2. Contact Binance support
3. Consider using testnet for development/testing
