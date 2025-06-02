#!/bin/bash

# Set environment variables
export REGISTRY=${REGISTRY:-your-registry}
export IMAGE_NAME=${IMAGE_NAME:-rate-limiter}
export TAG=${TAG:-latest}
export NAMESPACE=${NAMESPACE:-default}
export DOMAIN=${DOMAIN:-your-domain.com}

# Build and push Docker image
docker build -t ${REGISTRY}/${IMAGE_NAME}:${TAG} .
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}

# Create namespace if it doesn't exist
kubectl create namespace ${NAMESPACE} || true

# Apply Kubernetes manifests
for manifest in $(ls kubernetes/*.yaml); do
    sed "s/your-registry/${REGISTRY}/g" ${manifest} | \
    sed "s/your-domain.com/${DOMAIN}/g" | \
    kubectl apply -f -
done

# Wait for deployment to be ready
kubectl wait --for=condition=ready pod -l app=rate-limiter --timeout=300s

# Verify deployment
kubectl get pods -l app=rate-limiter
kubectl get svc rate-limiter
kubectl get ingress rate-limiter-ingress

# Show deployment status
echo "Deployment complete!"
echo "Service URL: http://rate-limiter.${DOMAIN}"
