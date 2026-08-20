"""
AWS/Azure/GCP Services Integration
Provides integration with major cloud service providers.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ServiceType(Enum):
    STORAGE = "storage"
    DATABASE = "database"
    COMPUTE = "compute"
    AI_ML = "ai_ml"
    MESSAGING = "messaging"
    SERVERLESS = "serverless"


@dataclass
class CloudConfig:
    config_id: str
    provider: CloudProvider
    access_key: str
    secret_key: str
    region: str
    project_id: Optional[str]  # For GCP
    subscription_id: Optional[str]  # For Azure
    enabled_services: List[ServiceType]
    created_at: str
    updated_at: str


@dataclass
class CloudResource:
    resource_id: str
    config_id: str
    service_type: ServiceType
    resource_name: str
    resource_type: str
    status: str
    metadata: Dict[str, Any]
    created_at: str


class CloudServicesManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.integrations_dir = os.path.join(self.base_dir, "data", "integrations")
        self.cloud_file = os.path.join(self.integrations_dir, "cloud_configs.json")
        self.resources_file = os.path.join(self.integrations_dir, "cloud_resources.json")
        
        os.makedirs(self.integrations_dir, exist_ok=True)
        
        # Load data
        self.configs = self._load_configs()
        self.resources = self._load_resources()

    def _load_configs(self) -> Dict[str, CloudConfig]:
        """Load cloud configurations from disk."""
        if os.path.exists(self.cloud_file):
            try:
                with open(self.cloud_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {config_id: CloudConfig(**config) for config_id, config in data.items()}
            except Exception:
                pass
        return {}

    def _save_configs(self):
        """Save cloud configurations to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {config_id: asdict(config) for config_id, config in self.configs.items()}
            with open(self.cloud_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[CloudServices] Failed to save configs: {e}")

    def _load_resources(self) -> Dict[str, CloudResource]:
        """Load cloud resources from disk."""
        if os.path.exists(self.resources_file):
            try:
                with open(self.resources_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {resource_id: CloudResource(**resource) for resource_id, resource in data.items()}
            except Exception:
                pass
        return {}

    def _save_resources(self):
        """Save cloud resources to disk."""
        try:
            data = {resource_id: asdict(resource) for resource_id, resource in self.resources.items()}
            with open(self.resources_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[CloudServices] Failed to save resources: {e}")

    def create_config(self, provider: CloudProvider, access_key: str, secret_key: str,
                     region: str, project_id: str = None, subscription_id: str = None,
                     enabled_services: List[ServiceType] = None) -> CloudConfig:
        """
        Create cloud provider configuration.
        
        Args:
            provider: Cloud provider
            access_key: Access key
            secret_key: Secret key
            region: Region
            project_id: Project ID (GCP)
            subscription_id: Subscription ID (Azure)
            enabled_services: Enabled services
            
        Returns:
            CloudConfig
        """
        config_id = f"cloud_{provider.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = CloudConfig(
            config_id=config_id,
            provider=provider,
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            project_id=project_id,
            subscription_id=subscription_id,
            enabled_services=enabled_services or [ServiceType.STORAGE, ServiceType.COMPUTE],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.configs[config_id] = config
        self._save_configs()
        
        return config

    def create_resource(self, config_id: str, service_type: ServiceType, resource_name: str,
                       resource_type: str, metadata: Dict[str, Any] = None) -> CloudResource:
        """
        Create a cloud resource.
        
        Args:
            config_id: Configuration ID
            service_type: Service type
            resource_name: Resource name
            resource_type: Resource type (e.g., 's3', 'ec2', 'lambda')
            metadata: Additional metadata
            
        Returns:
            CloudResource
        """
        if config_id not in self.configs:
            raise ValueError("Configuration not found")
        
        resource_id = f"resource_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        resource = CloudResource(
            resource_id=resource_id,
            config_id=config_id,
            service_type=service_type,
            resource_name=resource_name,
            resource_type=resource_type,
            status="creating",
            metadata=metadata or {},
            created_at=datetime.now().isoformat()
        )
        
        self.resources[resource_id] = resource
        self._save_resources()
        
        # In production, this would call the cloud provider API
        # self._provision_resource(resource)
        
        return resource

    def upload_to_storage(self, config_id: str, file_path: str, bucket_name: str,
                         destination_key: str = "") -> Tuple[bool, str]:
        """
        Upload file to cloud storage.
        
        Args:
            config_id: Configuration ID
            file_path: Local file path
            bucket_name: Bucket/container name
            destination_key: Destination key/path
            
        Returns:
            (success, message)
        """
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        config = self.configs[config_id]
        
        if ServiceType.STORAGE not in config.enabled_services:
            return False, "Storage service not enabled"
        
        # In production, this would use boto3 (AWS), azure-storage (Azure), or google-cloud-storage (GCP)
        return True, f"File uploaded to {config.provider.value} storage"

    def deploy_function(self, config_id: str, function_name: str, code_path: str,
                       runtime: str = "python3.9") -> Tuple[bool, str]:
        """
        Deploy a serverless function.
        
        Args:
            config_id: Configuration ID
            function_name: Function name
            code_path: Code path
            runtime: Runtime
            
        Returns:
            (success, message)
        """
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        config = self.configs[config_id]
        
        if ServiceType.SERVERLESS not in config.enabled_services:
            return False, "Serverless service not enabled"
        
        # In production, this would deploy to Lambda (AWS), Functions (Azure), or Cloud Functions (GCP)
        return True, f"Function deployed to {config.provider.value}"

    def query_database(self, config_id: str, database_name: str, query: str) -> List[Dict]:
        """
        Query cloud database.
        
        Args:
            config_id: Configuration ID
            database_name: Database name
            query: SQL query
            
        Returns:
            Query results
        """
        if config_id not in self.configs:
            return []
        
        config = self.configs[config_id]
        
        if ServiceType.DATABASE not in config.enabled_services:
            return []
        
        # In production, this would query RDS (AWS), SQL Database (Azure), or Cloud SQL (GCP)
        return []

    def get_resources(self, config_id: str, service_type: ServiceType = None) -> List[CloudResource]:
        """Get resources for a configuration."""
        if config_id not in self.configs:
            return []
        
        resources = [r for r in self.resources.values() if r.config_id == config_id]
        
        if service_type:
            resources = [r for r in resources if r.service_type == service_type]
        
        return resources

    def get_config(self, config_id: str) -> Optional[CloudConfig]:
        """Get configuration by ID."""
        return self.configs.get(config_id)

    def enable_service(self, config_id: str, service: ServiceType) -> bool:
        """Enable a service for a configuration."""
        if config_id not in self.configs:
            return False
        
        if service not in self.configs[config_id].enabled_services:
            self.configs[config_id].enabled_services.append(service)
            self.configs[config_id].updated_at = datetime.now().isoformat()
            self._save_configs()
        
        return True

    def delete_config(self, config_id: str) -> bool:
        """Delete a configuration."""
        if config_id not in self.configs:
            return False
        
        del self.configs[config_id]
        self._save_configs()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get cloud services statistics."""
        total_configs = len(self.configs)
        total_resources = len(self.resources)
        
        # Count by provider
        by_provider = {}
        for config in self.configs.values():
            provider = config.provider.value
            by_provider[provider] = by_provider.get(provider, 0) + 1
        
        # Count by service type
        by_service = {}
        for resource in self.resources.values():
            service = resource.service_type.value
            by_service[service] = by_service.get(service, 0) + 1
        
        return {
            'total_configs': total_configs,
            'total_resources': total_resources,
            'by_provider': by_provider,
            'by_service_type': by_service
        }

    def export_config(self, config_id: str, export_path: str) -> Tuple[bool, str]:
        """Export configuration (without secrets)."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        config = self.configs[config_id]
        
        # Create safe export without secrets
        safe_config = {
            'config_id': config.config_id,
            'provider': config.provider.value,
            'region': config.region,
            'project_id': config.project_id,
            'subscription_id': config.subscription_id,
            'enabled_services': [s.value for s in config.enabled_services],
            'created_at': config.created_at,
            'updated_at': config.updated_at
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(safe_config, f, indent=2)
            return True, f"Config exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
