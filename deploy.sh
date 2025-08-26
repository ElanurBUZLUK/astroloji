#!/bin/bash

# Astro-AA Production Deployment Script
# Usage: ./deploy.sh [dev|prod|health|logs|stop|backup|ssl|monitoring]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"
SSL_DIR="./nginx/ssl"

# Detect Docker Compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${PURPLE}[DEBUG]${NC} $1"
}

# Banner
echo -e "${CYAN}"
echo "🚀 =================================="
echo "   Astro-AA Production Deployment"
echo "   Version: 1.0.0"
echo "   Date: $(date)"
echo "==================================="
echo -e "${NC}"

# Load environment variables
load_env() {
    if [ -f "$ENV_FILE" ]; then
        log_info "Loading environment variables from $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    else
        log_warning "$ENV_FILE not found. Using default values."
    fi
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        echo "Installation guide: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Docker Compose is already detected globally
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    directories=(
        "$BACKUP_DIR"
        "$SSL_DIR"
        "./logs"
        "./nginx/logs"
        "./monitoring/grafana/dashboards"
        "./monitoring/grafana/datasources"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_debug "Created directory: $dir"
    done
    
    log_success "Directories created"
}

# Function to build Flutter web app
build_flutter_web() {
    log_info "Building Flutter web app..."
    
    if [ -d "mobile/flutter_app" ]; then
        cd mobile/flutter_app
        
        # Check if Flutter is installed
        if ! command -v flutter &> /dev/null; then
            log_warning "Flutter not found. Skipping web build."
            cd ../..
            return
        fi
        
        # Clean previous build
        flutter clean
        
        # Get dependencies
        flutter pub get
        
        # Build for web
        flutter build web --release --web-renderer html
        
        cd ../..
        log_success "Flutter web app built successfully"
        log_info "Web app size: $(du -sh mobile/flutter_app/build/web | cut -f1)"
    else
        log_warning "Flutter app directory not found. Skipping web build."
    fi
}

# Function to generate SSL certificates
generate_ssl_certificates() {
    log_info "Generating SSL certificates..."
    
    if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
        log_info "Creating self-signed SSL certificate for development..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/key.pem" \
            -out "$SSL_DIR/cert.pem" \
            -subj "/C=TR/ST=Istanbul/L=Istanbul/O=Astro-AA/OU=IT Department/CN=localhost" \
            -addext "subjectAltName=DNS:localhost,DNS:astro-aa.com,DNS:www.astro-aa.com,IP:127.0.0.1"
        
        log_success "Self-signed SSL certificate created"
        log_warning "For production, replace with valid SSL certificates"
    else
        log_info "SSL certificates already exist"
    fi
}

# Function to start services
start_services() {
    local mode=$1
    log_info "Starting $mode deployment..."
    
    load_env
    create_directories
    
    if [ "$mode" = "prod" ]; then
        check_prerequisites
        build_flutter_web
        generate_ssl_certificates
        
        # Use production configuration
        export BUILD_TARGET=production
        
        log_info "Starting production services..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d --build --remove-orphans
        
        log_info "Waiting for services to be ready..."
        sleep 45
        
        # Run health checks
        check_health
        
        # Show service URLs
        show_service_urls "prod"
        
    elif [ "$mode" = "dev" ]; then
        # Use development configuration
        export BUILD_TARGET=development
        
        log_info "Starting development services..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d --build --remove-orphans
        
        log_info "Waiting for services to be ready..."
        sleep 30
        
        # Show service URLs
        show_service_urls "dev"
        
    else
        log_error "Invalid mode: $mode. Use 'dev' or 'prod'"
        exit 1
    fi
}

# Function to show service URLs
show_service_urls() {
    local mode=$1
    
    echo -e "\n${GREEN}🌐 Service URLs:${NC}"
    echo "================================"
    
    if [ "$mode" = "prod" ]; then
        echo "🏠 Frontend:     https://localhost"
        echo "🔧 Backend API:  https://localhost/api"
        echo "👤 Admin Panel:  https://localhost/api/admin"
        echo "❤️  Health Check: https://localhost/health"
    else
        echo "🏠 Frontend:     http://localhost"
        echo "🔧 Backend API:  http://localhost:8000"
        echo "👤 Admin Panel:  http://localhost:8000/admin"
        echo "❤️  Health Check: http://localhost:8000/health"
    fi
    
    echo "🗄️  Database:     localhost:5432"
    echo "🔴 Redis:        localhost:6379"
    echo "================================"
}

# Function to check service health
check_health() {
    log_info "Checking service health..."
    
    local backend_url="http://localhost:8000"
    local max_attempts=10
    local attempt=1
    
    # Wait for backend to be ready
    while [ $attempt -le $max_attempts ]; do
        log_debug "Health check attempt $attempt/$max_attempts"
        
        if curl -f -s "$backend_url/health" > /dev/null; then
            log_success "Backend is healthy"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                log_error "Backend health check failed after $max_attempts attempts"
                docker-compose logs backend
                return 1
            fi
            sleep 5
            ((attempt++))
        fi
    done
    
    # Check database connection
    if $DOCKER_COMPOSE exec -T postgres pg_isready -U "${POSTGRES_USER:-astro_user}" -d "${POSTGRES_DB:-astro_aa}" > /dev/null 2>&1; then
        log_success "Database is healthy"
    else
        log_error "Database health check failed"
        $DOCKER_COMPOSE logs postgres
        return 1
    fi
    
    # Check Redis
    if $DOCKER_COMPOSE exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is healthy"
    else
        log_error "Redis health check failed"
        $DOCKER_COMPOSE logs redis
        return 1
    fi
    
    log_success "All core services are healthy"
}

# Function to show logs
show_logs() {
    local service=$2
    local lines=${3:-100}
    
    if [ -n "$service" ]; then
        log_info "Showing logs for service: $service"
        $DOCKER_COMPOSE logs -f --tail="$lines" "$service"
    else
        log_info "Showing logs for all services"
        $DOCKER_COMPOSE logs -f --tail="$lines"
    fi
}

# Function to backup database
backup_database() {
    log_info "Starting database backup..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Run backup container
    $DOCKER_COMPOSE run --rm backup
    
    if [ $? -eq 0 ]; then
        log_success "Database backup completed"
        log_info "Backup location: $BACKUP_DIR"
        ls -lah "$BACKUP_DIR"/*.gz 2>/dev/null | tail -5
    else
        log_error "Database backup failed"
        return 1
    fi
}

# Function to stop services
stop_services() {
    log_info "Stopping services..."
    $DOCKER_COMPOSE down
    log_success "Services stopped"
}

# Function to clean up
cleanup() {
    log_warning "This will remove all containers, volumes, and images. Are you sure? (y/N)"
    read -r confirmation
    
    if [ "$confirmation" != "y" ] && [ "$confirmation" != "Y" ]; then
        log_info "Cleanup cancelled"
        return 0
    fi
    
    log_info "Cleaning up..."
    $DOCKER_COMPOSE down -v --remove-orphans --rmi all
    docker system prune -f --volumes
    log_success "Cleanup completed"
}

# Function to show system status
show_status() {
    echo -e "\n${CYAN}📊 System Status${NC}"
    echo "================================"
    
    # Service status
    echo -e "\n📋 Service Status:"
    $DOCKER_COMPOSE ps
    
    # Recent logs
    echo -e "\n📝 Recent Errors (last 10):"
    $DOCKER_COMPOSE logs --tail=10 2>&1 | grep -i error || echo "No recent errors found"
}

# Main script logic
case "${1:-help}" in
    "dev")
        start_services "dev"
        ;;
    "prod")
        start_services "prod"
        ;;
    "health")
        check_health
        ;;
    "logs")
        show_logs "$@"
        ;;
    "backup")
        backup_database
        ;;
    "ssl")
        generate_ssl_certificates
        ;;
    "status")
        show_status
        ;;
    "stop")
        stop_services
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|*)
        echo -e "${CYAN}Astro-AA Deployment Script${NC}"
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  dev         - Start development environment"
        echo "  prod        - Start production environment"
        echo "  health      - Check service health"
        echo "  logs [svc]  - Show service logs (optional: specify service)"
        echo "  backup      - Create database backup"
        echo "  ssl         - Generate SSL certificates"
        echo "  status      - Show system status"
        echo "  stop        - Stop all services"
        echo "  cleanup     - Stop services and clean up everything"
        echo ""
        echo "Examples:"
        echo "  $0 prod                    # Start production"
        echo "  $0 logs backend            # Show backend logs"
        echo ""
        exit 1
        ;;
esac