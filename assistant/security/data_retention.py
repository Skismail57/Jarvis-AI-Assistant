"""
Data Retention Policies and GDPR Compliance System
Manages data retention policies, user consent, and GDPR compliance requirements.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class DataType(Enum):
    PERSONAL = "personal"
    CONVERSATION = "conversation"
    AUDIO = "audio"
    BIOMETRIC = "biometric"
    USAGE = "usage"
    SYSTEM = "system"


class ConsentStatus(Enum):
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"


@dataclass
class RetentionPolicy:
    policy_id: str
    data_type: DataType
    retention_days: int
    auto_delete: bool
    anonymize_before_delete: bool
    legal_hold: bool = False
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class UserConsent:
    consent_id: str
    user_id: str
    consent_type: str  # 'data_processing', 'biometric', 'analytics', 'marketing'
    status: ConsentStatus
    granted_at: str
    revoked_at: Optional[str] = None
    expires_at: Optional[str] = None
    version: str = "1.0"
    metadata: Dict[str, Any] = None


@dataclass
class DataRecord:
    record_id: str
    user_id: str
    data_type: DataType
    data_hash: str
    created_at: str
    expires_at: str
    retention_policy_id: str
    is_deleted: bool = False
    deleted_at: Optional[str] = None
    anonymized: bool = False
    legal_hold: bool = False


class DataRetentionManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.retention_dir = os.path.join(self.base_dir, "data", "retention")
        self.policies_file = os.path.join(self.retention_dir, "policies.json")
        self.consents_file = os.path.join(self.retention_dir, "consents.json")
        self.records_file = os.path.join(self.retention_dir, "records.json")
        
        os.makedirs(self.retention_dir, exist_ok=True)
        
        # Load data
        self.policies = self._load_policies()
        self.consents = self._load_consents()
        self.records = self._load_records()
        
        # Initialize default policies
        self._initialize_default_policies()

    def _load_policies(self) -> Dict[str, RetentionPolicy]:
        """Load retention policies from disk."""
        if os.path.exists(self.policies_file):
            try:
                with open(self.policies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {policy_id: RetentionPolicy(**policy) for policy_id, policy in data.items()}
            except Exception:
                pass
        return {}

    def _save_policies(self):
        """Save retention policies to disk."""
        try:
            data = {policy_id: asdict(policy) for policy_id, policy in self.policies.items()}
            with open(self.policies_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DataRetention] Failed to save policies: {e}")

    def _load_consents(self) -> Dict[str, UserConsent]:
        """Load user consents from disk."""
        if os.path.exists(self.consents_file):
            try:
                with open(self.consents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {consent_id: UserConsent(**consent) for consent_id, consent in data.items()}
            except Exception:
                pass
        return {}

    def _save_consents(self):
        """Save user consents to disk."""
        try:
            data = {consent_id: asdict(consent) for consent_id, consent in self.consents.items()}
            with open(self.consents_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DataRetention] Failed to save consents: {e}")

    def _load_records(self) -> Dict[str, DataRecord]:
        """Load data records from disk."""
        if os.path.exists(self.records_file):
            try:
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {record_id: DataRecord(**record) for record_id, record in data.items()}
            except Exception:
                pass
        return {}

    def _save_records(self):
        """Save data records to disk."""
        try:
            data = {record_id: asdict(record) for record_id, record in self.records.items()}
            with open(self.records_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DataRetention] Failed to save records: {e}")

    def _initialize_default_policies(self):
        """Initialize default retention policies."""
        if not self.policies:
            default_policies = {
                'personal_data_gdpr': RetentionPolicy(
                    policy_id='personal_data_gdpr',
                    data_type=DataType.PERSONAL,
                    retention_days=365,  # 1 year per GDPR
                    auto_delete=True,
                    anonymize_before_delete=True
                ),
                'conversation_data': RetentionPolicy(
                    policy_id='conversation_data',
                    data_type=DataType.CONVERSATION,
                    retention_days=90,  # 3 months
                    auto_delete=True,
                    anonymize_before_delete=True
                ),
                'audio_data': RetentionPolicy(
                    policy_id='audio_data',
                    data_type=DataType.AUDIO,
                    retention_days=30,  # 30 days
                    auto_delete=True,
                    anonymize_before_delete=True
                ),
                'biometric_data': RetentionPolicy(
                    policy_id='biometric_data',
                    data_type=DataType.BIOMETRIC,
                    retention_days=365,  # 1 year
                    auto_delete=True,
                    anonymize_before_delete=True
                ),
                'usage_data': RetentionPolicy(
                    policy_id='usage_data',
                    data_type=DataType.USAGE,
                    retention_days=730,  # 2 years
                    auto_delete=True,
                    anonymize_before_delete=True
                ),
                'system_logs': RetentionPolicy(
                    policy_id='system_logs',
                    data_type=DataType.SYSTEM,
                    retention_days=90,  # 3 months
                    auto_delete=True,
                    anonymize_before_delete=False
                )
            }
            
            self.policies = default_policies
            self._save_policies()

    def create_retention_policy(self, data_type: DataType, retention_days: int,
                               auto_delete: bool = True, anonymize_before_delete: bool = True) -> RetentionPolicy:
        """
        Create a new retention policy.
        
        Args:
            data_type: Type of data
            retention_days: Number of days to retain
            auto_delete: Whether to auto-delete after retention period
            anonymize_before_delete: Whether to anonymize before deletion
            
        Returns:
            Created RetentionPolicy
        """
        policy_id = f"policy_{data_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        policy = RetentionPolicy(
            policy_id=policy_id,
            data_type=data_type,
            retention_days=retention_days,
            auto_delete=auto_delete,
            anonymize_before_delete=anonymize_before_delete
        )
        
        self.policies[policy_id] = policy
        self._save_policies()
        
        return policy

    def update_retention_policy(self, policy_id: str, retention_days: int = None,
                               auto_delete: bool = None, legal_hold: bool = None) -> bool:
        """Update an existing retention policy."""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        
        if retention_days is not None:
            policy.retention_days = retention_days
        
        if auto_delete is not None:
            policy.auto_delete = auto_delete
        
        if legal_hold is not None:
            policy.legal_hold = legal_hold
        
        self._save_policies()
        
        return True

    def record_consent(self, user_id: str, consent_type: str, 
                     status: ConsentStatus = ConsentStatus.GRANTED,
                     expires_days: int = None) -> UserConsent:
        """
        Record user consent.
        
        Args:
            user_id: User ID
            consent_type: Type of consent
            status: Consent status
            expires_days: Days until consent expires
            
        Returns:
            UserConsent
        """
        consent_id = f"consent_{user_id}_{consent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        expires_at = None
        if expires_days:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        consent = UserConsent(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            status=status,
            granted_at=datetime.now().isoformat(),
            expires_at=expires_at
        )
        
        self.consents[consent_id] = consent
        self._save_consents()
        
        return consent

    def revoke_consent(self, user_id: str, consent_type: str) -> bool:
        """Revoke user consent."""
        # Find active consent
        for consent_id, consent in self.consents.items():
            if consent.user_id == user_id and consent.consent_type == consent_type:
                if consent.status == ConsentStatus.GRANTED:
                    consent.status = ConsentStatus.REVOKED
                    consent.revoked_at = datetime.now().isoformat()
                    self._save_consents()
                    return True
        
        return False

    def check_consent(self, user_id: str, consent_type: str) -> Tuple[bool, Optional[UserConsent]]:
        """
        Check if user has granted consent.
        
        Args:
            user_id: User ID
            consent_type: Type of consent
            
        Returns:
            (has_consent, consent_object)
        """
        # Find most recent consent
        user_consents = [
            consent for consent in self.consents.values()
            if consent.user_id == user_id and consent.consent_type == consent_type
        ]
        
        if not user_consents:
            return False, None
        
        # Sort by granted_at (newest first)
        user_consents.sort(key=lambda x: x.granted_at, reverse=True)
        latest_consent = user_consents[0]
        
        # Check if consent is still valid
        if latest_consent.status != ConsentStatus.GRANTED:
            return False, latest_consent
        
        if latest_consent.expires_at:
            expires_at = datetime.fromisoformat(latest_consent.expires_at)
            if datetime.now() > expires_at:
                latest_consent.status = ConsentStatus.EXPIRED
                self._save_consents()
                return False, latest_consent
        
        return True, latest_consent

    def register_data_record(self, user_id: str, data_type: DataType,
                           data_hash: str, policy_id: str = None) -> DataRecord:
        """
        Register a data record for retention tracking.
        
        Args:
            user_id: User ID
            data_type: Type of data
            data_hash: Hash of the data for identification
            policy_id: Retention policy to use
            
        Returns:
            DataRecord
        """
        # Select policy if not provided
        if policy_id is None:
            matching_policies = [p for p in self.policies.values() if p.data_type == data_type]
            if matching_policies:
                policy_id = matching_policies[0].policy_id
            else:
                # Create default policy
                policy = self.create_retention_policy(data_type)
                policy_id = policy.policy_id
        
        if policy_id not in self.policies:
            raise ValueError(f"Policy not found: {policy_id}")
        
        policy = self.policies[policy_id]
        
        record_id = f"record_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        expires_at = (datetime.now() + timedelta(days=policy.retention_days)).isoformat()
        
        record = DataRecord(
            record_id=record_id,
            user_id=user_id,
            data_type=data_type,
            data_hash=data_hash,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            retention_policy_id=policy_id
        )
        
        self.records[record_id] = record
        self._save_records()
        
        return record

    def apply_retention_policies(self) -> Dict[str, int]:
        """
        Apply retention policies to delete expired data.
        
        Returns:
            Statistics about actions taken
        """
        now = datetime.now()
        actions = {
            'expired_records': 0,
            'deleted_records': 0,
            'anonymized_records': 0,
            'legal_hold_records': 0
        }
        
        for record in self.records.values():
            if record.is_deleted:
                continue
            
            # Check if record is on legal hold
            if record.legal_hold:
                actions['legal_hold_records'] += 1
                continue
            
            # Check if expired
            expires_at = datetime.fromisoformat(record.expires_at)
            if now > expires_at:
                actions['expired_records'] += 1
                
                # Get policy
                policy = self.policies.get(record.retention_policy_id)
                if policy and policy.auto_delete:
                    if policy.anonymize_before_delete:
                        # Anonymize first
                        record.anonymized = True
                        actions['anonymized_records'] += 1
                    
                    # Mark as deleted
                    record.is_deleted = True
                    record.deleted_at = now.isoformat()
                    actions['deleted_records'] += 1
        
        if actions['deleted_records'] > 0:
            self._save_records()
        
        return actions

    def set_legal_hold(self, record_id: str, hold: bool = True) -> bool:
        """Set or remove legal hold on a data record."""
        if record_id not in self.records:
            return False
        
        self.records[record_id].legal_hold = hold
        self._save_records()
        
        return True

    def request_data_deletion(self, user_id: str) -> Tuple[bool, str]:
        """
        Process GDPR right to deletion request.
        
        Args:
            user_id: User ID requesting deletion
            
        Returns:
            (success, message)
        """
        # Find all user records
        user_records = [
            record for record in self.records.values()
            if record.user_id == user_id and not record.is_deleted
        ]
        
        if not user_records:
            return True, "No data found for deletion"
        
        # Mark all records for deletion
        for record in user_records:
            if not record.legal_hold:
                record.is_deleted = True
                record.deleted_at = datetime.now().isoformat()
                record.anonymized = True
        
        self._save_records()
        
        return True, f"Marked {len(user_records)} records for deletion"

    def request_data_export(self, user_id: str) -> Dict[str, Any]:
        """
        Process GDPR right to data portability request.
        
        Args:
            user_id: User ID requesting export
            
        Returns:
            Export summary
        """
        # Find all user records
        user_records = [
            record for record in self.records.values()
            if record.user_id == user_id
        ]
        
        # Get user consents
        user_consents = [
            consent for consent in self.consents.values()
            if consent.user_id == user_id
        ]
        
        return {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'total_records': len(user_records),
            'records_by_type': self._count_by_type(user_records),
            'consents': [asdict(consent) for consent in user_consents],
            'note': 'This is a summary. Actual data export requires integration with data storage.'
        }

    def _count_by_type(self, records: List[DataRecord]) -> Dict[str, int]:
        """Count records by data type."""
        counts = defaultdict(int)
        for record in records:
            counts[record.data_type.value] += 1
        return dict(counts)

    def get_user_data_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of all data held for a user."""
        user_records = [
            record for record in self.records.values()
            if record.user_id == user_id
        ]
        
        active_records = [r for r in user_records if not r.is_deleted]
        deleted_records = [r for r in user_records if r.is_deleted]
        
        return {
            'user_id': user_id,
            'total_records': len(user_records),
            'active_records': len(active_records),
            'deleted_records': len(deleted_records),
            'by_type': self._count_by_type(active_records),
            'consents': len([c for c in self.consents.values() if c.user_id == user_id])
        }

    def get_retention_statistics(self) -> Dict[str, Any]:
        """Get retention statistics."""
        total_records = len(self.records)
        
        if total_records == 0:
            return {
                'total_records': 0,
                'by_type': {},
                'by_status': {},
                'total_consents': 0
            }
        
        # Count by type
        by_type = defaultdict(int)
        for record in self.records.values():
            by_type[record.data_type.value] += 1
        
        # Count by status
        active = len([r for r in self.records.values() if not r.is_deleted])
        deleted = len([r for r in self.records.values() if r.is_deleted])
        
        return {
            'total_records': total_records,
            'by_type': dict(by_type),
            'by_status': {'active': active, 'deleted': deleted},
            'total_policies': len(self.policies),
            'total_consents': len(self.consents)
        }

    def generate_gdpr_report(self) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        now = datetime.now()
        
        # Check consent status
        total_consents = len(self.consents)
        active_consents = len([c for c in self.consents.values() if c.status == ConsentStatus.GRANTED])
        
        # Check data retention
        expired_not_deleted = len([
            r for r in self.records.values()
            if not r.is_deleted and datetime.fromisoformat(r.expires_at) < now
        ])
        
        # Check anonymization
        deleted_not_anonymized = len([
            r for r in self.records.values()
            if r.is_deleted and not r.anonymized
        ])
        
        # Calculate compliance score
        compliance_score = 100.0
        if expired_not_deleted > 0:
            compliance_score -= 20
        if deleted_not_anonymized > 0:
            compliance_score -= 10
        if active_consents < total_consents * 0.8:  # Less than 80% consent rate
            compliance_score -= 15
        
        return {
            'report_date': now.isoformat(),
            'standard': 'GDPR',
            'compliance_score': max(0.0, compliance_score),
            'consent_rate': round(active_consents / total_consents * 100, 2) if total_consents > 0 else 100,
            'expired_not_deleted': expired_not_deleted,
            'deleted_not_anonymized': deleted_not_anonymized,
            'recommendations': self._generate_gdpr_recommendations(
                expired_not_deleted, deleted_not_anonymized, active_consents, total_consents
            )
        }

    def _generate_gdpr_recommendations(self, expired_not_deleted: int, 
                                       deleted_not_anonymized: int, 
                                       active_consents: int, total_consents: int) -> List[str]:
        """Generate GDPR compliance recommendations."""
        recommendations = []
        
        if expired_not_deleted > 0:
            recommendations.append(f"Delete {expired_not_deleted} expired data records")
        
        if deleted_not_anonymized > 0:
            recommendations.append(f"Anonymize {deleted_not_anonymized} deleted records before final deletion")
        
        if active_consents < total_consents * 0.8:
            recommendations.append("Review and update user consent collection process")
        
        if not recommendations:
            recommendations.append("All GDPR requirements are being met")
        
        return recommendations

    def cleanup_deleted_records(self, days: int = 7) -> int:
        """
        Permanently remove deleted records after grace period.
        
        Args:
            days: Grace period in days
            
        Returns:
            Number of records permanently removed
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            record_id for record_id, record in self.records.items()
            if record.is_deleted and record.deleted_at
            and datetime.fromisoformat(record.deleted_at) < cutoff_date
        ]
        
        for record_id in to_remove:
            del self.records[record_id]
        
        if to_remove:
            self._save_records()
        
        return len(to_remove)

    def export_retention_data(self, export_path: str) -> Tuple[bool, str]:
        """Export retention data for backup/audit."""
        try:
            export_data = {
                'policies': {policy_id: asdict(policy) for policy_id, policy in self.policies.items()},
                'consents': {consent_id: asdict(consent) for consent_id, consent in self.consents.items()},
                'records': {record_id: asdict(record) for record_id, record in self.records.items()},
                'statistics': self.get_retention_statistics(),
                'gdpr_report': self.generate_gdpr_report(),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Retention data exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"
