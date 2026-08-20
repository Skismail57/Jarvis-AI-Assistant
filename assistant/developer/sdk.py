"""
SDK for Custom Integrations
Provides SDK for developers to build custom integrations with JARVIS.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class IntegrationType(Enum):
    VOICE = "voice"
    TEXT = "text"
    SMART_HOME = "smart_home"
    PRODUCTIVITY = "productivity"
    CUSTOM = "custom"


class AuthType(Enum):
    API_KEY = "api_key"
    OAUTH = "oauth"
    NONE = "none"


@dataclass
class IntegrationConfig:
    integration_id: str
    name: str
    integration_type: IntegrationType
    auth_type: AuthType
    api_endpoint: str
    api_key: Optional[str]
    oauth_config: Optional[Dict[str, str]]
    enabled: bool
    config: Dict[str, Any]
    created_at: str
    updated_at: str


class JARVISSDK:
    """SDK for building custom integrations with JARVIS."""
    
    def __init__(self, api_key: str = None, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
    def _init_session(self):
        """Initialize HTTP session."""
        try:
            import requests
            self.session = requests.Session()
            if self.api_key:
                self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
        except ImportError:
            print("[JARVISSDK] requests library not available")
    
    def send_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a message to JARVIS.
        
        Args:
            message: Message to send
            context: Additional context
            
        Returns:
            Response from JARVIS
        """
        if not self.session:
            self._init_session()
        
        payload = {
            'message': message,
            'context': context or {}
        }
        
        if self.session:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {'error': str(e)}
        
        return {'error': 'Session not initialized'}
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            limit: Number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        if not self.session:
            self._init_session()
        
        if self.session:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/conversations",
                    params={'limit': limit}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return []
        
        return []
    
    def trigger_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger an action in JARVIS.
        
        Args:
            action: Action name
            parameters: Action parameters
            
        Returns:
            Action result
        """
        if not self.session:
            self._init_session()
        
        payload = {
            'action': action,
            'parameters': parameters
        }
        
        if self.session:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/actions",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {'error': str(e)}
        
        return {'error': 'Session not initialized'}
    
    def register_webhook(self, event_type: str, url: str) -> Dict[str, Any]:
        """
        Register a webhook for JARVIS events.
        
        Args:
            event_type: Event type to listen for
            url: Webhook URL
            
        Returns:
            Webhook registration result
        """
        if not self.session:
            self._init_session()
        
        payload = {
            'event_type': event_type,
            'url': url
        }
        
        if self.session:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/webhooks",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {'error': str(e)}
        
        return {'error': 'Session not initialized'}
    
    def get_status(self) -> Dict[str, Any]:
        """Get JARVIS status."""
        if not self.session:
            self._init_session()
        
        if self.session:
            try:
                response = self.session.get(f"{self.base_url}/api/status")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {'error': str(e)}
        
        return {'error': 'Session not initialized'}


class IntegrationSDKManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.dev_dir = os.path.join(self.base_dir, "data", "developer")
        self.integrations_file = os.path.join(self.dev_dir, "integrations.json")
        
        os.makedirs(self.dev_dir, exist_ok=True)
        
        # Load integrations
        self.integrations = self._load_integrations()

    def _load_integrations(self) -> Dict[str, IntegrationConfig]:
        """Load integrations from disk."""
        if os.path.exists(self.integrations_file):
            try:
                with open(self.integrations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {int_id: IntegrationConfig(**int_config) for int_id, int_config in data.items()}
            except Exception:
                pass
        return {}

    def _save_integrations(self):
        """Save integrations to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {int_id: asdict(int_config) for int_id, int_config in self.integrations.items()}
            with open(self.integrations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[IntegrationSDK] Failed to save integrations: {e}")

    def create_integration(self, name: str, integration_type: IntegrationType,
                         auth_type: AuthType, api_endpoint: str,
                         api_key: str = None, oauth_config: Dict[str, str] = None) -> IntegrationConfig:
        """
        Create a custom integration configuration.
        
        Args:
            name: Integration name
            integration_type: Type of integration
            auth_type: Authentication type
            api_endpoint: API endpoint
            api_key: API key
            oauth_config: OAuth configuration
            
        Returns:
            IntegrationConfig
        """
        integration_id = f"integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        integration = IntegrationConfig(
            integration_id=integration_id,
            name=name,
            integration_type=integration_type,
            auth_type=auth_type,
            api_endpoint=api_endpoint,
            api_key=api_key,
            oauth_config=oauth_config,
            enabled=True,
            config={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.integrations[integration_id] = integration
        self._save_integrations()
        
        return integration

    def update_integration_config(self, integration_id: str, config: Dict[str, Any]) -> bool:
        """Update integration configuration."""
        if integration_id not in self.integrations:
            return False
        
        self.integrations[integration_id].config.update(config)
        self.integrations[integration_id].updated_at = datetime.now().isoformat()
        self._save_integrations()
        
        return True

    def enable_integration(self, integration_id: str) -> bool:
        """Enable an integration."""
        if integration_id not in self.integrations:
            return False
        
        self.integrations[integration_id].enabled = True
        self.integrations[integration_id].updated_at = datetime.now().isoformat()
        self._save_integrations()
        
        return True

    def disable_integration(self, integration_id: str) -> bool:
        """Disable an integration."""
        if integration_id not in self.integrations:
            return False
        
        self.integrations[integration_id].enabled = False
        self.integrations[integration_id].updated_at = datetime.now().isoformat()
        self._save_integrations()
        
        return True

    def get_integration(self, integration_id: str) -> Optional[IntegrationConfig]:
        """Get an integration by ID."""
        return self.integrations.get(integration_id)

    def get_enabled_integrations(self) -> List[IntegrationConfig]:
        """Get all enabled integrations."""
        return [i for i in self.integrations.values() if i.enabled]

    def get_integrations_by_type(self, integration_type: IntegrationType) -> List[IntegrationConfig]:
        """Get integrations by type."""
        return [i for i in self.integrations.values() if i.integration_type == integration_type]

    def delete_integration(self, integration_id: str) -> bool:
        """Delete an integration."""
        if integration_id not in self.integrations:
            return False
        
        del self.integrations[integration_id]
        self._save_integrations()
        
        return True

    def generate_sdk_code(self, integration_id: str) -> str:
        """Generate SDK code for an integration."""
        integration = self.get_integration(integration_id)
        if not integration:
            return ""
        
        sdk_code = f"""
# JARVIS Integration SDK for {integration.name}
# Generated on {datetime.now().isoformat()}

from jarvis_sdk import JARVISSDK

# Initialize SDK
sdk = JARVISSDK(
    api_key="{integration.api_key or 'YOUR_API_KEY'}",
    base_url="{integration.api_endpoint}"
)

# Example usage
def send_message(message: str):
    \"\"\"Send a message to JARVIS.\"\"\"
    response = sdk.send_message(message)
    return response

def get_history(limit: int = 10):
    \"\"\"Get conversation history.\"\"\"
    return sdk.get_conversation_history(limit)

def trigger_action(action: str, parameters: dict):
    \"\"\"Trigger an action in JARVIS.\"\"\"
    return sdk.trigger_action(action, parameters)

# Custom integration functions
def custom_function():
    \"\"\"Custom function for {integration.name}.\"\"\"
    # Add your custom logic here
    pass
"""
        return sdk_code

    def generate_python_package(self, integration_id: str, output_dir: str) -> Tuple[bool, str]:
        """Generate a Python package for the integration."""
        integration = self.get_integration(integration_id)
        if not integration:
            return False, "Integration not found"
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Create package structure
            package_dir = os.path.join(output_dir, integration.name.lower().replace(' ', '_'))
            os.makedirs(package_dir, exist_ok=True)
            
            # Generate __init__.py
            init_content = f'''
"""
{integration.name} Integration for JARVIS
"""

from .sdk import {integration.name.replace(' ', '')}SDK

__version__ = "1.0.0"
__all__ = ["{integration.name.replace(' ', '')}SDK"]
'''
            with open(os.path.join(package_dir, '__init__.py'), 'w') as f:
                f.write(init_content)
            
            # Generate sdk.py
            sdk_content = self.generate_sdk_code(integration_id)
            with open(os.path.join(package_dir, 'sdk.py'), 'w') as f:
                f.write(sdk_content)
            
            # Generate setup.py
            setup_content = f'''
from setuptools import setup, find_packages

setup(
    name="jarvis-{integration.name.lower().replace(' ', '-')}",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["requests"],
    author="JARVIS",
    description="{integration.name} integration for JARVIS AI Assistant",
    python_requires=">=3.7",
)
'''
            with open(os.path.join(output_dir, 'setup.py'), 'w') as f:
                f.write(setup_content)
            
            return True, f"Package generated in {output_dir}"
        except Exception as e:
            return False, f"Package generation failed: {str(e)}"

    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        total_integrations = len(self.integrations)
        enabled_integrations = len(self.get_enabled_integrations())
        
        # Count by type
        by_type = {}
        for integration in self.integrations.values():
            itype = integration.integration_type.value
            by_type[itype] = by_type.get(itype, 0) + 1
        
        # Count by auth type
        by_auth = {}
        for integration in self.integrations.values():
            auth = integration.auth_type.value
            by_auth[auth] = by_auth.get(auth, 0) + 1
        
        return {
            'total_integrations': total_integrations,
            'enabled_integrations': enabled_integrations,
            'by_type': by_type,
            'by_auth_type': by_auth
        }

    def export_integration(self, integration_id: str, export_path: str) -> Tuple[bool, str]:
        """Export integration configuration."""
        if integration_id not in self.integrations:
            return False, "Integration not found"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.integrations[integration_id]), f, indent=2)
            return True, f"Integration exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
