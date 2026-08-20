"""
CRM Integration (Salesforce, HubSpot)
Provides integration with CRM platforms for customer relationship management.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class CRMPlatform(Enum):
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"


class RecordType(Enum):
    LEAD = "lead"
    CONTACT = "contact"
    ACCOUNT = "account"
    OPPORTUNITY = "opportunity"
    DEAL = "deal"
    TASK = "task"


class LeadStatus(Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    LOST = "lost"
    CONVERTED = "converted"


@dataclass
class CRMConfig:
    config_id: str
    platform: CRMPlatform
    api_key: str
    api_url: str
    username: Optional[str]
    password: Optional[str]
    access_token: Optional[str]
    token_expires_at: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class CRMRecord:
    record_id: str
    config_id: str
    record_type: RecordType
    name: str
    email: str
    phone: str
    company: str
    status: str
    value: float
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class CRMIntegrationManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.integrations_dir = os.path.join(self.base_dir, "data", "integrations")
        self.crm_file = os.path.join(self.integrations_dir, "crm_configs.json")
        self.records_file = os.path.join(self.integrations_dir, "crm_records.json")
        
        os.makedirs(self.integrations_dir, exist_ok=True)
        
        # Load data
        self.configs = self._load_configs()
        self.records = self._load_records()

    def _load_configs(self) -> Dict[str, CRMConfig]:
        """Load CRM configurations from disk."""
        if os.path.exists(self.crm_file):
            try:
                with open(self.crm_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {config_id: CRMConfig(**config) for config_id, config in data.items()}
            except Exception:
                pass
        return {}

    def _save_configs(self):
        """Save CRM configurations to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {config_id: asdict(config) for config_id, config in self.configs.items()}
            with open(self.crm_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[CRMIntegration] Failed to save configs: {e}")

    def _load_records(self) -> Dict[str, CRMRecord]:
        """Load CRM records from disk."""
        if os.path.exists(self.records_file):
            try:
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {record_id: CRMRecord(**record) for record_id, record in data.items()}
            except Exception:
                pass
        return {}

    def _save_records(self):
        """Save CRM records to disk."""
        try:
            data = {record_id: asdict(record) for record_id, record in self.records.items()}
            with open(self.records_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[CRMIntegration] Failed to save records: {e}")

    def create_config(self, platform: CRMPlatform, api_key: str, api_url: str,
                     username: str = None, password: str = None) -> CRMConfig:
        """
        Create CRM configuration.
        
        Args:
            platform: CRM platform
            api_key: API key
            api_url: API URL
            username: Username (for Salesforce)
            password: Password (for Salesforce)
            
        Returns:
            CRMConfig
        """
        config_id = f"crm_{platform.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = CRMConfig(
            config_id=config_id,
            platform=platform,
            api_key=api_key,
            api_url=api_url,
            username=username,
            password=password,
            access_token=None,
            token_expires_at=None,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.configs[config_id] = config
        self._save_configs()
        
        return config

    def create_record(self, config_id: str, record_type: RecordType, name: str,
                    email: str = "", phone: str = "", company: str = "",
                    status: str = "new", value: float = 0.0,
                    metadata: Dict[str, Any] = None) -> CRMRecord:
        """
        Create a CRM record.
        
        Args:
            config_id: Configuration ID
            record_type: Type of record
            name: Contact/lead name
            email: Email address
            phone: Phone number
            company: Company name
            status: Status
            value: Deal/opportunity value
            metadata: Additional metadata
            
        Returns:
            CRMRecord
        """
        if config_id not in self.configs:
            raise ValueError("Configuration not found")
        
        record_id = f"record_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        record = CRMRecord(
            record_id=record_id,
            config_id=config_id,
            record_type=record_type,
            name=name,
            email=email,
            phone=phone,
            company=company,
            status=status,
            value=value,
            metadata=metadata or {},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.records[record_id] = record
        self._save_records()
        
        # In production, this would sync to the CRM platform
        # self._sync_to_crm(config_id, record)
        
        return record

    def _sync_to_crm(self, config_id: str, record: CRMRecord) -> bool:
        """Sync record to CRM platform."""
        config = self.configs[config_id]
        
        # In production, this would make actual API calls
        # Salesforce: use simple_salesforce
        # HubSpot: use hubspot-api-client
        # Pipedrive: use pipedrive-python
        
        return True

    def update_record(self, record_id: str, **kwargs) -> bool:
        """Update a CRM record."""
        if record_id not in self.records:
            return False
        
        record = self.records[record_id]
        
        if 'name' in kwargs:
            record.name = kwargs['name']
        if 'email' in kwargs:
            record.email = kwargs['email']
        if 'phone' in kwargs:
            record.phone = kwargs['phone']
        if 'company' in kwargs:
            record.company = kwargs['company']
        if 'status' in kwargs:
            record.status = kwargs['status']
        if 'value' in kwargs:
            record.value = kwargs['value']
        if 'metadata' in kwargs:
            record.metadata.update(kwargs['metadata'])
        
        record.updated_at = datetime.now().isoformat()
        self._save_records()
        
        return True

    def get_records(self, config_id: str, record_type: RecordType = None) -> List[CRMRecord]:
        """Get records for a configuration."""
        if config_id not in self.configs:
            return []
        
        records = [r for r in self.records.values() if r.config_id == config_id]
        
        if record_type:
            records = [r for r in records if r.record_type == record_type]
        
        return records

    def search_records(self, config_id: str, query: str) -> List[CRMRecord]:
        """Search records by name, email, or company."""
        if config_id not in self.configs:
            return []
        
        query_lower = query.lower()
        
        records = [
            r for r in self.records.values()
            if r.config_id == config_id and (
                query_lower in r.name.lower() or
                query_lower in r.email.lower() or
                query_lower in r.company.lower()
            )
        ]
        
        return records

    def convert_lead(self, record_id: str, opportunity_value: float = 0.0) -> bool:
        """Convert a lead to an opportunity."""
        if record_id not in self.records:
            return False
        
        record = self.records[record_id]
        
        if record.record_type != RecordType.LEAD:
            return False
        
        # Create opportunity record
        opportunity = self.create_record(
            config_id=record.config_id,
            record_type=RecordType.OPPORTUNITY,
            name=record.name,
            email=record.email,
            phone=record.phone,
            company=record.company,
            status="new",
            value=opportunity_value,
            metadata={'converted_from_lead': record_id}
        )
        
        # Update lead status
        record.status = LeadStatus.CONVERTED.value
        record.updated_at = datetime.now().isoformat()
        self._save_records()
        
        return True

    def get_pipeline_value(self, config_id: str) -> float:
        """Get total value of all opportunities."""
        records = self.get_records(config_id, RecordType.OPPORTUNITY)
        return sum(r.value for r in records)

    def get_config(self, config_id: str) -> Optional[CRMConfig]:
        """Get configuration by ID."""
        return self.configs.get(config_id)

    def delete_record(self, record_id: str) -> bool:
        """Delete a CRM record."""
        if record_id not in self.records:
            return False
        
        del self.records[record_id]
        self._save_records()
        
        return True

    def delete_config(self, config_id: str) -> bool:
        """Delete a configuration."""
        if config_id not in self.configs:
            return False
        
        del self.configs[config_id]
        self._save_configs()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get CRM integration statistics."""
        total_configs = len(self.configs)
        total_records = len(self.records)
        
        # Count by platform
        by_platform = {}
        for config in self.configs.values():
            platform = config.platform.value
            by_platform[platform] = by_platform.get(platform, 0) + 1
        
        # Count by record type
        by_record_type = {}
        for record in self.records.values():
            rtype = record.record_type.value
            by_record_type[rtype] = by_record_type.get(rtype, 0) + 1
        
        return {
            'total_configs': total_configs,
            'total_records': total_records,
            'by_platform': by_platform,
            'by_record_type': by_record_type
        }

    def export_records(self, config_id: str, export_path: str) -> Tuple[bool, str]:
        """Export records to file."""
        if config_id not in self.configs:
            return False, "Configuration not found"
        
        records = self.get_records(config_id)
        
        try:
            export_data = {
                'config_id': config_id,
                'records': [asdict(r) for r in records],
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Records exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
