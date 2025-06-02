#!/bin/bash

# Set default values for environment variables
export REGISTRY=${REGISTRY:-your-registry}
export NAMESPACE=${NAMESPACE:-default}
export DOMAIN=${DOMAIN:-your-domain.com}
export ENVIRONMENT=${ENVIRONMENT:-production}

# Colors for output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m"

# Function to print colored messages
print_status() {
    echo -e "${BLUE}[*] ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}[+] ${1}${NC}"
}

print_error() {
    echo -e "${RED}[-] ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] ${1}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate environment variables
validate_env() {
    if [ -z "$REGISTRY" ]; then
        print_error "REGISTRY environment variable is not set"
        exit 1
    fi

    if [ -z "$DOMAIN" ]; then
        print_error "DOMAIN environment variable is not set"
        exit 1
    fi
}

# Function to validate Kubernetes cluster
validate_cluster() {
    print_status "Validating Kubernetes cluster..."
    
    if ! command_exists kubectl; then
        print_error "kubectl is not installed"
        exit 1
    fi

    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_error "Unable to connect to Kubernetes cluster"
        exit 1
    fi

    print_success "Kubernetes cluster is accessible"
}

# Function to build and push Docker images
build_images() {
    print_status "Building and pushing Docker images..."
    
    # List of services to build
    services=(
        "api-gateway"
        "service-mesh"
        "rate-limiter"
        "monitoring"
        "visualization"
        "security-manager"
    )

    for service in "${services[@]}"; do
        print_status "Building $service..."
        
        # Build Docker image
        docker build -t "$REGISTRY/$service:$ENVIRONMENT" -f "docker/$service/Dockerfile" .
        
        # Push to registry
        docker push "$REGISTRY/$service:$ENVIRONMENT"
        
        print_success "$service built and pushed successfully"
    done
}

# Function to create namespaces
create_namespaces() {
    print_status "Creating namespaces..."
    
    # Create main namespace
    kubectl create namespace "$NAMESPACE" || true
    
    # Create monitoring namespace
    kubectl create namespace "monitoring" || true
    
    print_success "Namespaces created"
}

# Function to deploy core services
deploy_core_services() {
    print_status "Deploying core services..."
    
    # Deploy Redis
    kubectl apply -f kubernetes/redis/
    
    # Deploy PostgreSQL
    kubectl apply -f kubernetes/postgres/
    
    # Deploy RabbitMQ
    kubectl apply -f kubernetes/rabbitmq/
    
    print_success "Core services deployed"
}

# Function to deploy monitoring stack
deploy_monitoring() {
    print_status "Deploying monitoring stack..."
    
    # Deploy Prometheus
    kubectl apply -f kubernetes/prometheus/
    
    # Deploy Grafana
    kubectl apply -f kubernetes/grafana/
    
    # Deploy Jaeger
    kubectl apply -f kubernetes/jaeger/
    
    print_success "Monitoring stack deployed"
}

# Function to deploy alerting system
deploy_alerting() {
    print_status "Deploying alerting system..."
    
    # Deploy Alertmanager
    kubectl apply -f kubernetes/alertmanager/
    
    # Deploy Slack webhook
    kubectl apply -f kubernetes/slack-webhook/
    
    # Deploy Discord webhook
    kubectl apply -f kubernetes/discord-webhook/
    
    print_success "Alerting system deployed"
}

# Function to deploy visualization
deploy_visualization() {
    print_status "Deploying visualization..."
    
    # Deploy visualization service
    kubectl apply -f kubernetes/visualization/
    
    # Deploy visualization dashboard
    kubectl apply -f kubernetes/visualization-dashboard/
    
    print_success "Visualization deployed"
}

# Function to deploy security services
deploy_security() {
    print_status "Deploying security services..."
    
    # Deploy security manager
    kubectl apply -f kubernetes/security-manager/
    
    # Deploy rate limiter
    kubectl apply -f kubernetes/rate-limiter/
    
    print_success "Security services deployed"
}

# Function to deploy service mesh
deploy_service_mesh() {
    print_status "Deploying service mesh..."
    
    # Deploy Istio
    kubectl apply -f kubernetes/istio/
    
    # Deploy Envoy
    kubectl apply -f kubernetes/envoy/
    
    print_success "Service mesh deployed"
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check pods
    kubectl get pods -A
    
    # Check services
    kubectl get svc -A
    
    # Check deployments
    kubectl get deployments -A
    
    # Check ingresses
    kubectl get ingresses -A
    
    print_success "Deployment verified"
}

# Function to show deployment status
show_status() {
    print_status "Deployment status:"
    
    echo -e "\n${BLUE}Cluster Information:${NC}"
    kubectl cluster-info
    
    echo -e "\n${BLUE}Pods:${NC}"
    kubectl get pods -A
    
    echo -e "\n${BLUE}Services:${NC}"
    kubectl get svc -A
    
    echo -e "\n${BLUE}Ingresses:${NC}"
    kubectl get ingresses -A
    
    echo -e "\n${BLUE}Deployments:${NC}"
    kubectl get deployments -A
}

# Main deployment function
main() {
    print_status "Starting deployment..."
    
    # Validate environment
    validate_env
    
    # Validate cluster
    validate_cluster
    
    # Create namespaces
    create_namespaces
    
    # Build and push images
    build_images
    
    # Deploy core services
    deploy_core_services
    
    # Deploy monitoring
    deploy_monitoring
    
    # Deploy alerting
    deploy_alerting
    
    # Deploy visualization
    deploy_visualization
    
    # Deploy security
    deploy_security
    
    # Deploy service mesh
    deploy_service_mesh
    
    # Verify deployment
    verify_deployment
    
    # Show status
    show_status
    
    print_success "Deployment completed successfully!"
}

# Execute main function
main
