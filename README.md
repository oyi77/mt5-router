# MT5 Router - SaaS Trading Platform

A powerful, self-hosted dashboard for managing MetaTrader 5 instances with VNC access, trading API, real-time monitoring, notifications, and multi-tenant SaaS architecture.

## 🚀 Features

### Trading
- **Market Orders**: BUY/SELL with instant execution
- **Pending Orders**: BUY_LIMIT, SELL_LIMIT, BUY_STOP, BUY_STOP_LIMIT
- **Order Modification**: Modify SL/TP on open positions
- **Partial Close**: Close partial position volume
- **Real-time Streaming**: WebSocket for live quotes, candles, ticks
- **Trade History**: Full deal history with configurable periods
- **Copy Trading**: Strategy provider/subscriber architecture (Coming Soon)

### Instance Management
- **Docker Control**: Create, Start, Stop, Restart, Delete MT5 containers
- **VNC Access**: Browser-based remote desktop via noVNC
- **Container Metrics**: CPU, Memory, Network per instance
- **Logs**: Real-time container log streaming

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

## 🏗️ Architecture

```
MT5 Router SaaS Architecture
============================

Frontend (React)          Backend (FastAPI)         MT5 Instances
┌─────────────────┐      ┌─────────────────┐      ┌─────────────┐
│ Dashboard UI    │ ───▶ │ REST API        │ ───▶ │ Docker      │
│ Trading Panel   │      │ WebSocket       │      │ Containers  │
│ Notifications   │      │ Auth (JWT+API)  │      │ (mt5linux)  │
│ Admin Panel     │      │ Rate Limiter    │      │             │
└─────────────────┘      └────────┬────────┘      └─────────────┘
                                  │
                       ┌──────────┴──────────┐
                       │    PostgreSQL/      │
                       │     SQLite          │
                       │ (Users, Alerts,     │
                       │  Audit, Usage)      │
                       └─────────────────────┘

External Integrations
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Telegram    │ │ Webhooks    │ │ Stripe      │
│ Bot API     │ │(TradingView)│ │ (Billing)   │
└─────────────┘ └─────────────┘ └─────────────┘
```

## 📋 API Endpoints (40+)

### Authentication
- POST `/api/v1/auth/register` - Register new user
- POST `/api/v1/auth/login` - JWT login
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

### Notifications
- POST `/api/v1/notifications/telegram/configure` - Setup Telegram
- POST `/api/v1/notifications/webhooks` - Add webhook
- POST `/api/v1/notifications/alerts` - Create alert rule
- GET `/api/v1/notifications/alerts` - List alerts

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

## 🔄 WebSocket Connections
- `/api/v1/monitoring/stream` - Real-time system metrics
- `/api/v1/trading/ticks` - Real-time price ticks

## 📝 License
MIT

## 🔗 Links
- [GitHub](https://github.com/oyi77/mt5-router)
- [Issues](https://github.com/oyi77/mt5-router/issues)
