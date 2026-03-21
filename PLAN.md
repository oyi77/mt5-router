# MT5 Router - MetaAPI Parity Plan

## Overview
Target: Reach 90%+ feature parity with MetaAPI.cloud
Timeline: 5 phases, ~2-3 weeks implementation

---

## Phase 1: MT5 Account Management (Foundation)
**Goal**: Enable users to add MT5 account credentials and connect to terminals

### Backend Tasks:
1. [ ] Create `MT5Account` model with fields:
   - login (int) - MT5 account number
   - password (encrypted)
   - server (str) - broker server
   - broker (str)
   - account_type (demo/live)
   - connection_status (disconnected/connecting/connected/error)
   - last_connected (datetime)

2. [ ] Create `accounts.py` API router:
   - POST `/api/v1/accounts` - Add new MT5 account
   - GET `/api/v1/accounts` - List user's accounts
   - GET `/api/v1/accounts/{id}` - Get account details
   - PUT `/api/v1/accounts/{id}` - Update account
   - DELETE `/api/v1/accounts/{id}` - Remove account
   - POST `/api/v1/accounts/{id}/connect` - Connect to MT5
   - POST `/api/v1/accounts/{id}/disconnect` - Disconnect

3. [ ] Update `MT5Service`:
   - Add `connect(login, password, server)` method
   - Add `disconnect()` method
   - Add connection status checking
   - Auto-reconnect on failure

4. [ ] Add encryption service for password storage

### Frontend Tasks:
1. [ ] Create `AccountsPanel.tsx` - Account management UI
2. [ ] Add account form dialog (login, password, server)
3. [ ] Add connection status indicator
4. [ ] Add "Connect" / "Disconnect" buttons

---

## Phase 2: Copy Trading System
**Goal**: Implement strategy provider → subscriber signal replication

### Backend Tasks:
1. [ ] Create models:
   - `CopyStrategy` - Strategy provider settings
   - `CopySubscriber` - Subscriber configuration
   - `CopySignal` - Trade signal records
   - `CopyPosition` - Tracked positions

2. [ ] Create `copytrading.py` API router:
   - Strategy management:
     - POST `/api/v1/copy/strategies` - Create strategy
     - GET `/api/v1/copy/strategies` - List strategies
     - PUT `/api/v1/copy/strategies/{id}` - Update
     - DELETE `/api/v1/copy/strategies/{id}` - Remove
   - Subscriber management:
     - POST `/api/v1/copy/subscribers` - Add subscriber
     - GET `/api/v1/copy/subscribers` - List subscribers
     - PUT `/api/v1/copy/subscribers/{id}` - Update
     - DELETE `/api/v1/copy/subscribers/{id}` - Remove
   - Signal processing:
     - POST `/api/v1/copy/signals` - Receive signal
     - GET `/api/v1/copy/signals` - View signal history

3. [ ] Create copy engine service:
   - Monitor provider positions
   - Replicate trades to subscribers
   - Handle Lot sizing (fixed/percentage)
   - Filter by symbol/pair

### Frontend Tasks:
1. [ ] Create `CopyTradingPanel.tsx`
2. [ ] Create strategy setup form
3. [ ] Create subscriber management UI
4. [ ] Add signal history viewer

---

## Phase 3: Trading Statistics & Analytics
**Goal**: Provide MetaTrader-style statistics

### Backend Tasks:
1. [ ] Create stats models:
   - `TradeStatistics` - Aggregated stats
   - `DailySummary` - Daily P&L
   - `PerformanceMetrics` - Win rate, drawdown, etc.

2. [ ] Create `statistics.py` API:
   - GET `/api/v1/stats/summary` - Overall stats
   - GET `/api/v1/stats/daily` - Daily breakdown
   - GET `/api/v1/stats/symbols` - Per-symbol stats
   - GET `/api/v1/stats/trades` - Trade history with metrics
   - GET `/api/v1/stats/equity-curve` - Equity curve data

3. [ ] Implement calculations:
   - Win rate / Loss rate
   - Profit factor
   - Sharpe ratio
   - Max drawdown
   - Average trade duration

### Frontend Tasks:
1. [ ] Create `StatisticsPanel.tsx`
2. [ ] Add equity curve chart
3. [ ] Add trade distribution charts
4. [ ] Add performance metrics cards

---

## Phase 4: Enhanced Webhooks & Signals
**Goal**: External signal reception and event webhooks

### Backend Tasks:
1. [ ] Create webhook receiver:
   - POST `/api/v1/webhooks/receive` - Receive external signals
   - Support TradingView alerts format
   - Support generic JSON format

2. [ ] Create event webhooks:
   - POST `/api/v1/webhooks/configure` - Setup outgoing webhook
   - Events: new trade, position closed, account balance change
   - Signature verification

3. [ ] Create signal forwarding:
   - Forward signals to Copy Trading system
   - Convert webhook format to internal signals

### Frontend Tasks:
1. [ ] Create `WebhooksPanel.tsx`
2. [ ] Add webhook configuration form
3. [ ] Add webhook test button
4. [ ] Add event log viewer

---

## Phase 5: Final Polish & Integration
**Goal**: Bug fixes, performance, and user experience

### Tasks:
1. [ ] Fix any remaining bugs
2. [ ] Add error handling improvements
3. [ ] Optimize database queries
4. [ ] Add unit tests for new features
5. [ ] Update documentation
6. [ ] Final integration testing

---

## Technical Notes

### Account Connection Flow:
```
User adds MT5 account (login, password, server)
    ↓
Backend encrypts password and stores
    ↓
User clicks "Connect"
    ↓
MT5Service.connect() initializes RPYC to container
    ↓
mt5.login(login, password, server) called
    ↓
Connection status updated to "connected"
```

### Copy Trading Flow:
```
Provider opens position (any MT5 terminal)
    ↓
MT5Service detects new position
    ↓
Signal created in CopySignal table
    ↓
CopyEngine processes signal
    ↓
For each subscriber:
    - Calculate lot size
    - Execute opposite trade on subscriber's MT5
    - Record copied position
```

---

## Priority Implementation Order

### Week 1: Foundation
1. MT5 Account model + API
2. Account connection logic
3. Frontend account panel

### Week 2: Core Features
4. Copy trading models + API
5. Copy engine
6. Frontend copy trading UI

### Week 3: Analytics & Polish
7. Statistics API + calculations
8. Webhook receiver + sender
9. Frontend stats + webhooks UI
10. Testing + documentation