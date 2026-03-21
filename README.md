# MT5 Router

A robust dashboard for managing MetaTrader 5 instances with VNC access, trading API, and real-time monitoring.

## Features

- **Instance Management**: Create, start, stop, restart, and delete MT5 Docker containers
- **VNC Access**: Browser-based remote desktop access to MT5 terminals
- **Trading API**: Full trading functionality via mt5linux RPYC bridge
- **Real-time Monitoring**: System and container metrics with WebSocket updates
- **JWT Authentication**: Secure access control

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)

### Installation

```bash
# Clone the repository
git clone https://github.com/oyi77/mt5-router.git
cd mt5-router

# Copy environment file
cp backend/.env.example .env

# Start services
docker-compose up -d
```

### Default Credentials

- Username: `admin`
- Password: `admin123`

> Change these in production!

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    mt-oc.aitradepulse.com                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Frontend (React)          Backend (FastAPI)                    │
│   ┌─────────────────┐      ┌─────────────────┐                  │
│   │ Dashboard UI    │ ───▶ │ REST API        │                  │
│   │ VNC Viewer      │      │ WebSocket       │                  │
│   │ Trading Panel   │      │ Auth (JWT)      │                  │
│   └─────────────────┘      └────────┬────────┘                  │
│                                      │                           │
│                    ┌─────────────────┼─────────────────┐        │
│                    │                 │                 │        │
│              ┌─────▼─────┐   ┌──────▼──────┐   ┌─────▼─────┐  │
│              │ Docker API │   │ mt5linux    │   │ psutil    │  │
│              │ (Control)  │   │ (Trading)   │   │ (Metrics) │  │
│              └─────┬─────┘   └──────┬──────┘   └─────┬─────┘  │
│                    │                 │                 │        │
│              ┌─────▼─────────────────▼─────────────────▼─────┐  │
│              │            MT5 Docker Container                │  │
│              │  ┌─────────────────┐  ┌─────────────────┐     │  │
│              │  │ MetaTrader 5    │  │ noVNC           │     │  │
│              │  │ (Port 18812)    │  │ (Port 6081)     │     │  │
│              │  └─────────────────┘  └─────────────────┘     │  │
│              └───────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Instances
- `GET /api/v1/instances` - List all MT5 instances
- `POST /api/v1/instances` - Create new instance
- `GET /api/v1/instances/{id}` - Get instance details
- `POST /api/v1/instances/{id}/start` - Start instance
- `POST /api/v1/instances/{id}/stop` - Stop instance
- `POST /api/v1/instances/{id}/restart` - Restart instance
- `DELETE /api/v1/instances/{id}` - Delete instance
- `GET /api/v1/instances/{id}/logs` - Get instance logs
- `GET /api/v1/instances/{id}/stats` - Get instance stats

### VNC
- `GET /api/v1/vnc/{id}/status` - Check VNC status
- `GET /api/v1/vnc/{id}/vnc.html` - VNC viewer page

### Trading
- `GET /api/v1/trading/account` - Get account info
- `GET /api/v1/trading/positions` - Get open positions
- `POST /api/v1/trading/orders` - Place order
- `POST /api/v1/trading/positions/{ticket}/close` - Close position
- `GET /api/v1/trading/history` - Get deal history

### Monitoring
- `GET /api/v1/monitoring/system` - System metrics
- `GET /api/v1/monitoring/instances` - Instance metrics
- `WS /api/v1/monitoring/stream` - Real-time metrics WebSocket

## Cloudflare Router Integration

Add to your Cloudflare Router `mappings.yml`:

```yaml
mappings:
  - subdomain: mt-oc
    port: 8080
    description: MT5 Control Dashboard
    protocol: http
    enabled: true
```

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Security Notes

1. Change the default admin password immediately
2. Update JWT_SECRET in production
3. Enable HTTPS via Cloudflare
4. Restrict Docker socket access in production
5. Use environment-specific configurations

## License

MIT
