#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

generate_jwt_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(64))"
}

generate_fernet_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

setup_environment() {
    local env=$1
    print_info "Setting up $env environment..."
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists. Backing up to .env.backup"
        cp .env .env.backup
    fi
    
    JWT_SECRET=$(generate_jwt_secret)
    ENCRYPTION_KEY=$(generate_fernet_key)
    
    case $env in
        "local")
            cat > .env << EOF
# MT5 Router - Local Development
APP_NAME=MT5 Router (Local)
APP_VERSION=3.1.0
DEBUG=true
HOST=0.0.0.0
PORT=8080

# Security
JWT_SECRET=$JWT_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY

# Database (SQLite for local)
DATABASE_URL=sqlite:///./data/mt5router.db

# Docker
MT5_IMAGE=lprett/mt5linux:mt5-installed

# Rate Limiting (relaxed for dev)
RATE_LIMIT_PER_MINUTE=1000

# CORS (open for local)
CORS_ORIGINS=*

# Telegram (disabled)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Stripe (disabled)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
EOF
            ;;
            
        "dev")
            cat > .env << EOF
# MT5 Router - Development Server
APP_NAME=MT5 Router (Dev)
APP_VERSION=3.1.0
DEBUG=true
HOST=0.0.0.0
PORT=8080

# Security
JWT_SECRET=$JWT_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY

# Database (SQLite for dev)
DATABASE_URL=sqlite:///./data/mt5router.db

# Docker
MT5_IMAGE=lprett/mt5linux:mt5-installed

# Rate Limiting
RATE_LIMIT_PER_MINUTE=200

# CORS (dev origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://dev.mt5router.local

# Telegram (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Stripe (test mode)
STRIPE_SECRET_KEY=sk_test_
STRIPE_WEBHOOK_SECRET=whsec_
EOF
            ;;
            
        "prod")
            cat > .env << EOF
# MT5 Router - Production
APP_NAME=MT5 Router
APP_VERSION=3.1.0
DEBUG=false
HOST=0.0.0.0
PORT=8080

# Security (IMPORTANT: Keep these secret!)
JWT_SECRET=$JWT_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY

# Database (PostgreSQL for production)
DATABASE_URL=postgresql://mt5router:$(openssl rand -hex 16)@postgres:5432/mt5router

# Docker
MT5_IMAGE=lprett/mt5linux:mt5-installed

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# CORS (your domains only)
CORS_ORIGINS=https://mt-oc.aitradepulse.com,https://*.aitradepulse.com

# Telegram (recommended for production)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Stripe (live mode)
STRIPE_SECRET_KEY=sk_live_
STRIPE_WEBHOOK_SECRET=whsec_

# Redis (for caching)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Database Pool
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
EOF
            ;;
    esac
    
    print_status "Created .env for $env environment"
}

create_directories() {
    mkdir -p data logs
    print_status "Created data and logs directories"
}

check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_status "All dependencies installed"
}

build_and_run() {
    local env=$1
    print_info "Building and starting services for $env..."
    
    case $env in
        "local")
            docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
            ;;
        "dev")
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
            ;;
        "prod")
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
            ;;
    esac
    
    print_status "Services started"
}

wait_for_service() {
    print_info "Waiting for backend to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            print_status "Backend is ready!"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Backend failed to start"
    return 1
}

create_admin_user() {
    print_info "Creating default admin user..."
    
    docker-compose exec -T backend python3 -c "
from app.models.database import User
from app.core.database import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

admin = db.query(User).filter(User.username == 'admin').first()
if not admin:
    admin = User(
        email='admin@mt5router.local',
        username='admin',
        hashed_password=pwd_context.hash('admin123'),
        role='admin',
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    db.commit()
    print('Admin user created: admin / admin123')
else:
    print('Admin user already exists')
db.close()
" 2>/dev/null || print_warning "Could not create admin user (you can do this manually)"
}

show_summary() {
    local env=$1
    echo ""
    echo "=========================================="
    echo -e "${GREEN}MT5 Router Setup Complete!${NC}"
    echo "=========================================="
    echo ""
    echo -e "Environment: ${BLUE}$env${NC}"
    echo ""
    echo "Services:"
    docker-compose ps
    echo ""
    echo "Access URLs:"
    echo -e "  Backend API:  ${GREEN}http://localhost:8080${NC}"
    echo -e "  Frontend:     ${GREEN}http://localhost:3000${NC}"
    echo -e "  API Docs:     ${GREEN}http://localhost:8080/docs${NC}"
    echo ""
    echo "Default Admin:"
    echo -e "  Username: ${YELLOW}admin${NC}"
    echo -e "  Password: ${YELLOW}admin123${NC}"
    echo ""
    echo "Useful Commands:"
    echo "  docker-compose logs -f          # View logs"
    echo "  docker-compose ps               # Check status"
    echo "  docker-compose restart          # Restart services"
    echo "  docker-compose down             # Stop services"
    echo ""
    echo "=========================================="
}

# Main
main() {
    echo ""
    echo "=========================================="
    echo -e "${BLUE}MT5 Router Setup${NC}"
    echo "=========================================="
    echo ""
    
    if [ $# -eq 0 ]; then
        echo "Usage: ./setup.sh [local|dev|prod]"
        echo ""
        echo "Environments:"
        echo "  local  - Local development (SQLite, debug on)"
        echo "  dev    - Development server (SQLite, debug on)"
        echo "  prod   - Production (PostgreSQL, optimized)"
        echo ""
        exit 1
    fi
    
    ENV=$1
    
    case $ENV in
        "local"|"dev"|"prod")
            ;;
        *)
            print_error "Invalid environment: $ENV"
            echo "Valid options: local, dev, prod"
            exit 1
            ;;
    esac
    
    check_dependencies
    setup_environment $ENV
    create_directories
    build_and_run $ENV
    
    if wait_for_service; then
        create_admin_user
        show_summary $ENV
    else
        print_error "Setup failed. Check logs with: docker-compose logs"
        exit 1
    fi
}

main "$@"
