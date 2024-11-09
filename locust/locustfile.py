import logging
import time
import json
from locust import HttpUser, task, between
from kubernetes import client, config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ConfigMap details
NAMESPACE = "default"
CONFIGMAP_NAME = "healthy-pods-configmap"

# Round-robin index to track the current pod to send traffic to
pod_index = {}
last_refresh_time = 0
refresh_interval = 30  # seconds to wait before re-reading the ConfigMap

# Kubernetes API client setup
config.load_incluster_config()  # Use this if running inside a Kubernetes cluster
v1 = client.CoreV1Api()

# Fetch healthy pods from the ConfigMap
# def get_healthy_pods_from_configmap():
#     """Get the healthy pods from the ConfigMap."""
#     cm = v1.read_namespaced_config_map(CONFIGMAP_NAME, NAMESPACE)
#     healthy_pods_str = cm.data.get("healthy_pods", "[]")
#     try:
#         healthy_pods = eval(healthy_pods_str)  # Convert string to dictionary
#     except Exception as e:
#         logger.error(f"Error parsing ConfigMap data: {e}")
#         healthy_pods = {}
#     return healthy_pods

def get_healthy_pods_from_configmap():
    """Get the healthy pods from the ConfigMap."""
    cm = v1.read_namespaced_config_map(CONFIGMAP_NAME, NAMESPACE)
    healthy_pods_str = cm.data.get("healthy_pods", "{}")  # Default to empty dict if not found
    try:
        healthy_pods = json.loads(healthy_pods_str)  # Safely convert string to dictionary
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing ConfigMap data: {e}")
        healthy_pods = {}
    return healthy_pods

# Initialize the round-robin indices for each service
def initialize_pod_index(healthy_pods):
    """Initialize the round-robin index for each service."""
    for service, pods in healthy_pods.items():
        pod_index[service] = 0

# Locust user class
class LoadTest(HttpUser):
    wait_time = between(1, 5)  # Adjust the time between requests

    def on_start(self):
        """Fetch healthy pods and initialize the round-robin index."""
        self.healthy_pods = get_healthy_pods_from_configmap()
        initialize_pod_index(self.healthy_pods)
    
    def refresh_healthy_pods(self):
        """Refresh healthy pods from the ConfigMap periodically."""
        global last_refresh_time
        if time.time() - last_refresh_time > refresh_interval:
            logger.info("Refreshing healthy pods from ConfigMap.")
            self.healthy_pods = get_healthy_pods_from_configmap()
            initialize_pod_index(self.healthy_pods)
            last_refresh_time = time.time()

    def get_next_healthy_pod(self, service_name):
        """Get the next healthy pod for the specified service using round-robin."""
        if service_name not in self.healthy_pods or not self.healthy_pods[service_name]:
            logger.warning(f"No healthy pods available for {service_name}")
            return None

        # Get the current pod index for round-robin distribution
        index = pod_index.get(service_name, 0)
        pod_ip = self.healthy_pods[service_name][index]

        # Update the round-robin index
        pod_index[service_name] = (index + 1) % len(self.healthy_pods[service_name])

        return pod_ip

    @task
    def send_traffic(self):
        """Send traffic to the healthy pods using round-robin."""
        self.refresh_healthy_pods()
        for service in ["node-app-primary-service", "node-app-secondary-service", "node-app-failover-service"]:
            pod_ip = self.get_next_healthy_pod(service)
            if pod_ip:
                url = f"http://{pod_ip}:3000"
                logger.info(f"Sending traffic to service: {service} at {url}")
                self.client.get(url)
                break
            else:
                logger.warning(f"No healthy pods available for service {service}. Skipping traffic distribution.")


# from locust import HttpUser, task, between
# import logging
# import itertools

# # Set up logging to console
# logging.basicConfig(level=logging.DEBUG)

# class NodeAppUser(HttpUser):
#     wait_time = between(1, 3)  # Random wait time between tasks

#     # Create a cycle iterator for round-robin load balancing
#     services = [
#         "http://node-app-primary-service.default.svc.cluster.local",
#         "http://node-app-secondary-service.default.svc.cluster.local",
#         "http://node-app-failover-service.default.svc.cluster.local"
#     ]
#     service_cycle = itertools.cycle(services)  # This will loop over the services infinitely

#     # Define the task that will be executed by Locust
#     @task
#     def load_test(self):
#         # Get the next service from the round-robin cycle
#         service = next(self.service_cycle)
        
#         response = self.client.get(f"{service}/health")

#         # Print status code and other response data for debugging
#         logging.info(f"Request sent to {service}: {response.status_code}")

#         # Check if the health endpoint is up
#         if response.status_code != 200:
#             logging.info(f"Service {service} failed, status code: {response.status_code}")

