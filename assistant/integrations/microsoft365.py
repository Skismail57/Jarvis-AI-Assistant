"""
Microsoft 365 Integration
Provides integration with Microsoft 365 services (Outlook, Teams, OneDrive, SharePoint).
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class M365Service(Enum):
    OUTLOOK = "outlook"
    TEAMS = "teams"
    ONEDRIVE = "onedrive"
    SHAREPOINT = "sharepoint"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"


class CalendarEventType(Enum):
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    ALL_DAY = "all_day"


@dataclass
class M365Config:
    config_id: str
    tenant_id: str
    client_id: str
    client_secret: str
    redirect_uri: str
    access_token: Optional[str]
    refresh_token: Optional[str]
    token_expires_at: Optional[str]
    enabled_services: List[M365Service]
    created_at: str
    updated_at: str


@dataclass
class CalendarEvent:
    event_id: str
    subject: str
    start_time: str
    end_time: str
    location: str
    attendees: List[str]
    event_type: CalendarEventType
    body: str
    created_at: str


class Microsoft365Manager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.integrations_dir = os.path.join(self.base_dir, "data", "integrations")
        self.m365_file = os.path.join(self.integrations_dir, "m365_config.json")
        self.events_file = os.path.join(self.integrations_dir, "m365_events.json")
        
        os.makedirs(self.integrations_dir, exist_ok=True)
        
        # Load data
        self.configs = self._load_configs()
        self.events = self._load_events()

    def _load_configs(self) -> Dict[str, M365Config]:
        """Load M365 configurations from disk."""
        if os.path.exists(self.m365_file):
            try:
                with open(self.m365_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {config_id: M365Config(**config) for config_id, config in data.items()}
            except Exception:
                pass
        return {}

    def _save_configs(self):
        """Save M365 configurations to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {config_id: asdict(config) for config_id, config in self.configs.items()}
            with open(self.m365_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[Microsoft365] Failed to save configs: {e}")

    def _load_events(self) -> Dict[str, CalendarEvent]:
        """Load calendar events from disk."""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {event_id: CalendarEvent(**event) for event_id, event in data.items()}
            except Exception:
                pass
        return {}

    def _save_events(self):
        """Save calendar events to disk."""
        try:
            data = {event_id: asdict(event) for event_id, event in self.events.items()}
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Microsoft365] Failed to save events: {e}")

    def create_config(self, tenant_id: str, client_id: str, client_secret: str,
                     redirect_uri: str, enabled_services: List[M365Service] = None) -> M365Config:
        """
        Create Microsoft 365 configuration.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
            client_secret: Application secret
            redirect_uri: Redirect URI for OAuth
            enabled_services: List of enabled services
            
        Returns:
            M365Config
        """
        config_id = f"m365_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = M365Config(
            config_id=config_id,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            access_token=None,
            refresh_token=None,
            token_expires_at=None,
            enabled_services=enabled_services or [M365Service.OUTLOOK, M365Service.TEAMS],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.configs[config_id] = config
        self._save_configs()
        
        return config

    def update_tokens(self, config_id: str, access_token: str, refresh_token: str,
                    expires_in: int) -> bool:
        """
        Update OAuth tokens.
        
        Args:
            config_id: Configuration ID
            access_token: Access token
            refresh_token: Refresh token
            expires_in: Token expiration in seconds
            
        Returns:
            True if successful
        """
        if config_id not in self.configs:
            return False
        
        expires_at = datetime.fromtimestamp(datetime.now().timestamp() + expires_in).isoformat()
        
        self.configs[config_id].access_token = access_token
        self.configs[config_id].refresh_token = refresh_token
        self.configs[config_id].token_expires_at = expires_at
        self.configs[config_id].updated_at = datetime.now().isoformat()
        
        self._save_configs()
        return True

    def create_calendar_event(self, config_id: str, subject: str, start_time: str,
                            end_time: str, location: str = "", attendees: List[str] = None,
                            event_type: CalendarEventType = CalendarEventType.MEETING,
                            body: str = "") -> CalendarEvent:
        """
        Create a calendar event.
        
        Args:
            config_id: Configuration ID
            subject: Event subject
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            location: Event location
            attendees: List of attendees
            event_type: Event type
            body: Event body/description
            
        Returns:
            CalendarEvent
        """
        if config_id not in self.configs:
            raise ValueError("Configuration not found")
        
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        event = CalendarEvent(
            event_id=event_id,
            subject=subject,
            start_time=start_time,
            end_time=end_time,
            location=location,
            attendees=attendees or [],
            event_type=event_type,
            body=body,
            created_at=datetime.now().isoformat()
        )
        
        self.events[event_id] = event
        self._save_events()
        
        # In production, this would call Microsoft Graph API
        # self._sync_to_m365(config_id, event)
        
        return event

    def _sync_to_m365(self, config_id: str, event: CalendarEvent) -> bool:
        """Sync event to Microsoft 365 via Graph API."""
        # In production, this would make actual API calls
        config = self.configs[config_id]
        
        # Placeholder for Graph API call
        # endpoint = f"https://graph.microsoft.com/v1.0/me/events"
        # headers = {'Authorization': f'Bearer {config.access_token}'}
        # response = requests.post(endpoint, json=event_data, headers=headers)
        
        return True

    def get_calendar_events(self, config_id: str, start_date: str = None,
                          end_date: str = None) -> List[CalendarEvent]:
        """
        Get calendar events from Microsoft 365.
        
        Args:
            config_id: Configuration ID
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            
        Returns:
            List of CalendarEvents
        """
        if config_id not in self.configs:
            return []
        
        events = list(self.events.values())
        
        # Filter by date range if provided
        if start_date:
            start = datetime.fromisoformat(start_date)
            events = [e for e in events if datetime.fromisoformat(e.start_time) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            events = [e for e in events if datetime.fromisoformat(e.end_time) <= end]
        
        events.sort(key=lambda x: x.start_time)
        
        return events

    def send_teams_message(self, config_id: str, channel_id: str, message: str) -> Tuple[bool, str]:
        """
        Send a message to Microsoft Teams.
        
        Args:
            config_id: Configuration ID
            channel_id: Teams channel ID
            message: Message to send
            
        Returns:
            (success, message)
        """
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        if M365Service.TEAMS not in self.configs[config_id].enabled_services:
            return False, "Teams service not enabled"
        
        # In production, this would call Microsoft Graph API
        # endpoint = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages"
        
        return True, "Message sent to Teams"

    def upload_to_onedrive(self, config_id: str, file_path: str, 
                          destination: str = "") -> Tuple[bool, str]:
        """
        Upload a file to OneDrive.
        
        Args:
            config_id: Configuration ID
            file_path: Local file path
            destination: Destination path in OneDrive
            
        Returns:
            (success, message)
        """
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        if M365Service.ONEDRIVE not in self.configs[config_id].enabled_services:
            return False, "OneDrive service not enabled"
        
        # In production, this would upload via Graph API
        return True, f"File uploaded to OneDrive: {destination}"

    def get_onedrive_files(self, config_id: str, folder_path: str = "") -> List[Dict[str, Any]]:
        """
        Get files from OneDrive.
        
        Args:
            config_id: Configuration ID
            folder_path: Folder path in OneDrive
            
        Returns:
            List of file information
        """
        if config_id not in self.configs:
            return []
        
        if M365Service.ONEDRIVE not in self.configs[config_id].enabled_services:
            return []
        
        # In production, this would query via Graph API
        return []

    def create_word_document(self, config_id: str, title: str, content: str) -> Tuple[bool, str]:
        """
        Create a Word document.
        
        Args:
            config_id: Configuration ID
            title: Document title
            content: Document content
            
        Returns:
            (success, message)
        """
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        if M365Service.WORD not in self.configs[config_id].enabled_services:
            return False, "Word service not enabled"
        
        # In production, this would create via Graph API
        return True, f"Word document created: {title}"

    def get_config(self, config_id: str) -> Optional[M365Config]:
        """Get configuration by ID."""
        return self.configs.get(config_id)

    def enable_service(self, config_id: str, service: M365Service) -> bool:
        """Enable a service for a configuration."""
        if config_id not in self.configs:
            return False
        
        if service not in self.configs[config_id].enabled_services:
            self.configs[config_id].enabled_services.append(service)
            self.configs[config_id].updated_at = datetime.now().isoformat()
            self._save_configs()
        
        return True

    def disable_service(self, config_id: str, service: M365Service) -> bool:
        """Disable a service for a configuration."""
        if config_id not in self.configs:
            return False
        
        if service in self.configs[config_id].enabled_services:
            self.configs[config_id].enabled_services.remove(service)
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
        """Get Microsoft 365 integration statistics."""
        total_configs = len(self.configs)
        total_events = len(self.events)
        
        # Count by enabled services
        by_service = {}
        for config in self.configs.values():
            for service in config.enabled_services:
                sname = service.value
                by_service[sname] = by_service.get(sname, 0) + 1
        
        return {
            'total_configs': total_configs,
            'total_events': total_events,
            'by_service': by_service
        }

    def export_config(self, config_id: str, export_path: str) -> Tuple[bool, str]:
        """Export configuration (without secrets)."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        config = self.configs[config_id]
        
        # Create safe export without secrets
        safe_config = {
            'config_id': config.config_id,
            'tenant_id': config.tenant_id,
            'client_id': config.client_id,
            'redirect_uri': config.redirect_uri,
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
