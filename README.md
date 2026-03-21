# MT5 Router - SaaS Trading Platform

A powerful, self-hosted dashboard for managing MetaTrader 5 instances with VNC access, trading API, real-time monitoring, notifications, and multi-tenant SaaS architecture.

## 🚀 Features

### Trading
- **Market Orders**: BUY/SELL with instant execution
- **Pending Orders**: BUY_LIMIT, SELL_LIMIT, BUY_STOP, BUY_STOP_LIMIT, SELL_STOP_LIMIT
- **Order Modification**: Modify SL/TP on open positions
- **Partial Close**: Close partial position volume
- **Real-time Streaming**: WebSocket for live quotes, candles, ticks
- **Trade History**: Full deal history with configurable periods
- **Copy Trading**: Strategy provider/subscriber architecture
- **Trading Statistics**: Performance metrics, equity curves, symbol breakdown
- **MT5 Accounts**: Connect/disconnect multiple MT5 accounts with encrypted credentials

### Instance Management
- **Docker Control**: Create, Start, Stop, Restart, Delete MT5 containers
- **VNC Access**: Browser-based remote desktop via noVNC
- **Container Metrics**: CPU, Memory, Network per instance
- **Logs**: Real-time container log streaming

### Multi-Server SSH Management (v3.0)
- **SSH Server Connections**: Connect and manage multiple VPS servers
- **Remote Docker Control**: Deploy MT5 instances across servers
- **Server Health Monitoring**: Real-time CPU, Memory, Disk metrics
- **Encrypted Credentials**: SSH keys and passwords stored securely
- **Server Status**: Online/Offline health checks

### Monitoring & Alerts
- **System Metrics**: CPU, Memory, Disk with WebSocket streaming
- **Alert Rules**: Price alerts, position alerts, account alerts
- **Telegram Integration**: Real-time notifications via Telegram bot
- **Webhooks**: TradingView and custom webhook support

### SaaS Architecture
- **Multi-tenant**: Complete user management with roles
- **API Keys**: Programmatic access with rate limiting
- **JWT Authentication**: Secure token-based auth
- **Database Persistence**: SQLite (dev) / PostgreSQL (production)
- **Rate Limiting**: Per-user/API-key request throttling
- **Audit Logging**: Track all user actions

### Billing & Subscriptions (v3.0)
- **Stripe Integration**: Subscription billing with checkout
- **Tiered Plans**: Free, Basic, Pro, Enterprise
- **Usage Tracking**: Monitor API calls, servers, instances
- **Invoicing**: Automatic invoice generation
- **Customer Portal**: Self-service billing management

### Authentication & Security (v3.0)
- **Email Verification**: Verify user email addresses
- **Password Reset**: Secure password recovery via email
- **2FA/TOTP**: Two-factor authentication with Google Authenticator
- **Account Lockout**: Brute force protection
- **Security Dashboard**: View security status

## 🏗️ Architecture

```
MT5 Router SaaS Architecture (v3.0)
====================================

Frontend (React)          Backend (FastAPI)         MT5 Instances
┌─────────────────┐      ┌─────────────────┐      ┌─────────────┐
│ Dashboard UI    │ ───▶ │ REST API        │ ───▶ │ Docker      │
│ Trading Panel   │      │ WebSocket       │      │ Containers  │
│ Notifications   │      │ Auth (JWT+API)  │      │ (mt5linux)  │
│ Server Mgmt     │      │ Rate Limiter    │      │             │
│ Billing Panel   │      │ 2FA/TOTP        │      └─────────────┘
└─────────────────┘      └────────┬────────┘
                                  │
                       ┌──────────┴──────────┐
                       │    PostgreSQL/      │
                       │     SQLite          │
                       │ (Users, Alerts,     │
                       │  Billing, Audit)    │
                       └─────────────────────┘

External Integrations
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Telegram    │ │ Webhooks    │ │ Stripe      │ │ SMTP        │
│ Bot API     │ │(TradingView)│ │ (Billing)   │ │ (Email)     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

Multi-Server Architecture
┌─────────────────────────────────────────────────────────────┐
│                     MT5 Router Dashboard                    │
└───────────────────────────┬─────────────────────────────────┘
                            │ SSH (paramiko)
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Server 1   │ │ Server 2   │ │ Server 3   │
    │ (Local)    │ │ (VPS)      │ │ (VPS)      │
    ├────────────┤ ├────────────┤ ├────────────┤
    │ MT5 × 3   │ │ MT5 × 5   │ │ MT5 × 2   │
    │ VNC        │ │ VNC        │ │ VNC        │
    └────────────┘ └────────────┘ └────────────┘
```

## 📋 API Endpoints (60+)

### Authentication
- POST `/api/v1/auth/register` - Register new user
- POST `/api/v1/auth/login` - JWT login (with 2FA support)
- POST `/api/v1/auth/verify-email` - Verify email token
- POST `/api/v1/auth/forgot-password` - Request password reset
- POST `/api/v1/auth/reset-password` - Reset password
- POST `/api/v1/auth/2fa/setup` - Setup 2FA
- POST `/api/v1/auth/2fa/verify` - Verify 2FA token
- GET `/api/v1/auth/me` - Get current user
- POST `/api/v1/users/api-keys` - Create API key
- GET `/api/v1/users/api-keys` - List API keys

### Trading
- GET `/api/v1/trading/account` - Account info
- GET `/api/v1/trading/positions` - Open positions
- POST `/api/v1/trading/orders` - Place order
- PUT `/api/v1/trading/positions/{id}/modify` - Modify SL/TP
- POST `/api/v1/trading/positions/{id}/partial-close` - Partial close
- GET `/api/v1/trading/symbols/{symbol}/candles` - Candle data
- WS `/api/v1/trading/ticks` - Real-time ticks

### SSH Servers (v3.0)
- POST `/api/v1/servers` - Add SSH server
- GET `/api/v1/servers` - List SSH servers
- PUT `/api/v1/servers/{id}` - Update server
- DELETE `/api/v1/servers/{id}` - Remove server
- POST `/api/v1/servers/{id}/health` - Check server health
- GET `/api/v1/servers/{id}/instances` - List remote instances
- POST `/api/v1/servers/{id}/instances` - Deploy instance on server
- POST `/api/v1/servers/{id}/instances/{name}/{action}` - Control remote instance

### Billing (v3.0)
- GET `/api/v1/billing/tiers` - List subscription tiers
- GET `/api/v1/billing/subscription` - Get current subscription
- POST `/api/v1/billing/checkout` - Create Stripe checkout
- GET `/api/v1/billing/portal` - Get customer portal URL
- POST `/api/v1/billing/cancel` - Cancel subscription
- POST `/api/v1/billing/reactivate` - Reactivate subscription
- GET `/api/v1/billing/invoices` - List invoices
- GET `/api/v1/billing/usage` - Get usage stats
- POST `/api/v1/billing/webhook` - Stripe webhook

### Notifications
- POST `/api/v1/notifications/telegram/configure` - Setup Telegram
- POST `/api/v1/notifications/webhooks` - Add webhook
- POST `/api/v1/notifications/alerts` - Create alert rule
- GET `/api/v1/notifications/alerts` - List alerts

### MT5 Accounts
- GET/POST `/api/v1/accounts` - List/Create MT5 accounts
- DELETE `/api/v1/accounts/{id}` - Delete account
- POST `/api/v1/accounts/{id}/connect` - Connect to broker
- POST `/api/v1/accounts/{id}/disconnect` - Disconnect from broker

### Copy Trading
- GET/POST `/api/v1/copy/strategies` - List/Create strategies
- GET/POST `/api/v1/copy/subscribers` - List/Create subscribers
- GET `/api/v1/copy/signals` - Get signals

### Trading Statistics
- GET `/api/v1/stats/summary` - Overall performance metrics
- GET `/api/v1/stats/daily` - Daily breakdown
- GET `/api/v1/stats/symbols` - Per-symbol stats
- GET `/api/v1/stats/equity-curve` - Equity curve data

### Webhooks
- GET `/api/v1/webhooks` - List webhooks
- POST `/api/v1/webhooks/configure` - Configure webhook
- POST `/api/v1/webhooks/receive` - Receive external signals
- DELETE `/api/v1/webhooks/{id}` - Delete webhook
- POST `/api/v1/webhooks/test/{id}` - Test webhook

### Instances
- GET/POST `/api/v1/instances` - List/Create instances
- POST `/api/v1/instances/{id}/start|stop|restart`
- GET `/api/v1/instances/{id}/logs|stats`

### VNC
- GET `/api/v1/vnc/{id}/status` - VNC status
- GET `/api/v1/vnc/{id}/vnc.html` - VNC viewer

## 🚀 Quick Start

### Development
```bash
git clone https://github.com/oyi77/mt5-router.git
cd mt5-router
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
```

### Production
```bash
docker-compose --profile production up -d
```

### Default Credentials
- Username: `admin`
- Password: `admin123`

## 🔐 Authentication

### JWT Token
```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -d "username=admin&password=admin123"
```

### API Key
```bash
curl -H "X-API-Key: mtr_xxxxxxxxxxxx" \
  http://localhost:8080/api/v1/trading/account
```

## 📱 Telegram Notifications
1. Create bot via @BotFather
2. Get chat ID
3. Configure via dashboard or API

## 📊 Alert Rules
```json
{
  "alert_type": "price",
  "symbol": "XAUUSD",
  "condition": "greater_than",
  "value": 2400,
  "channel": "telegram"
}
```

## 💳 Subscription Tiers

| Tier | Price | Servers | Instances | API Calls/Day |
|------|-------|---------|-----------|---------------|
| Free | $0 | 1 | 1 | 1,000 |
| Basic | $29/mo | 3 | 5 | 10,000 |
| Pro | $79/mo | 10 | 25 | 100,000 |
| Enterprise | Custom | ∞ | ∞ | ∞ |

## 🔄 WebSocket Connections
- `/api/v1/monitoring/stream` - Real-time system metrics
- `/api/v1/trading/ticks` - Real-time price ticks

## 📝 License
MIT

## 🔗 Links
- [GitHub](https://github.com/oyi77/mt5-router)
- [Issues](https://github.com/oyi77/mt5-router/issues)
