# Kubernetes Failover Load Balancer with Health Check Prioritization

## Overview
This project implements a **Failover-First Load Balancer** with **Health Check Prioritization** for Kubernetes deployments. It includes:
- A Node.js app (`app.js`) that runs on primary, secondary, and failover services in Kubernetes.
- A Python script (`health_checker.py`) that monitors the health of the services and updates a Kubernetes ConfigMap with healthy services.
- A Locust load testing script (`locustfile.py`) that sends traffic in a round-robin fashion only to healthy pods.
The system's failover behavior is tested by scaling down pods.

## Prerequisites
- **Docker**: For building and running containerized applications.
- **Kubernetes**: A Kubernetes cluster (e.g., Minikube, Kind) for deploying services.
- **Python 3**: For running the health checker script.
- **Node.js**: For running the Node.js application.
- **Locust**: For load testing.
- **Kubernetes CLI (kubectl)**

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/simransarawagi95/k8s-health-check-load-testing.git
   cd k8s-health-check-load-testing
   
2. **Set up the Kubernetes cluster**:
    Ensure that your Kubernetes cluster is running and configured. You can use Minikube, Kind, or any Kubernetes provider.
   ```bash
   kind create cluster --name failover-cluster
   
3. **Build Docker images**:
    You need to build Docker images for both the Node.js app, the Python health checker and the locust load tester.
    For Node.js app:
   ```bash
    docker build -t failover-node-app:latest ./app
   ```

    For the health checker:
    ```bash
    docker build -t health-checker:latest ./health_checker
    ```

    For Locust:
    ```bash
    docker build -t locust-load-tester:latest ./locust
    ```

4. **Deploy to Kubernetes**:
    Apply the Kubernetes deployment files for primary, secondary, and failover services:
   ```bash
    kubectl apply -f k8s/deployment-primary.yaml              
    kubectl apply -f k8s/deployment-secondary.yaml  
    kubectl apply -f k8s/deployment-failover.yaml
    kubectl apply -f k8s/service-primary.yaml                 
    kubectl apply -f k8s/service-secondary.yaml     
    kubectl apply -f k8s/service-failover.yaml
   ```

    Deploy the health checker as a CronJob in the Kubernetes cluster:
   ```bash
    kubectl apply -f k8s/healthy-pods-configmap.yaml
    kubectl apply -f k8s/cronjob-health-checker.yaml
    kubectl apply -f k8s/health-checker-role.yaml
    kubectl apply -f k8s/health-checker-rolebinding.yaml
   ```

    Deploy Locust master and worker:
   ```bash
    kubectl apply -f locust/k8s-locust-deployment.yaml        
    kubectl apply -f locust/k8s-locust-service.yaml
    kubectl apply -f locust/k8s-locust-worker-deployment.yaml
   ```

5. **Check the services and pods**:
   ```bash
    kubectl get svc
    kubectl get pods
   ```

6. **Start Locust**:
   ```bash
    kubectl port-forward service/locust-master 8089:8089
   ```
    You can now access the Locust web UI to start the load test. By default, it's available at http://localhost:8089.

## Testing Failover and Traffic Redirection

1. **Downscale Primary Deployment**:
   To simulate a failure and check the failover mechanism, scale down the primary deployment to zero replicas:
   ```bash
   kubectl scale deployment node-app-primary --replicas=0

2. **Check the Service Endpoints**:
   After scaling down the primary deployment, you can check the status of the service endpoints to ensure that traffic is redirected to the secondary or failover pods:
   ```bash
   kubectl get endpoints node-app-primary-service

3. **Observe Locust Logs**:
   Once the primary deployment is scaled down, Locust should automatically start routing traffic to the available pods in the secondary and failover deployments. To observe this behavior, check the Locust logs. You can monitor the traffic distribution by watching the Locust logs as it sends traffic to healthy pods:
   ```bash
    kubectl port-forward service/locust-master 8089:8089
   ```
   You can now access the Locust web UI to start the load test. By default, it's available at http://localhost:8089.

4. **Scale the Primary Deployment Back**:
   Once you've verified that the failover mechanism works correctly, scale the primary deployment back up:
   ```bash
   kubectl scale deployment node-app-primary --replicas=1

The traffic should return to the primary deployment once it's healthy again.











