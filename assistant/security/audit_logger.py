"""
Audit Logging and Compliance Reporting System
Provides comprehensive audit logging for security events and compliance reporting.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class AuditEventType(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIG = "system_config"
    PRIVACY = "privacy"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class AuditSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    log_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str]
    action: str
    resource: Optional[str]
    outcome: str  # 'success', 'failure', 'partial'
    timestamp: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = None
    compliance_tags: List[str] = None


@dataclass
class ComplianceReport:
    report_id: str
    report_type: str
    period_start: str
    period_end: str
    generated_at: str
    summary: Dict[str, Any]
    findings: List[Dict[str, Any]]
    recommendations: List[str]


class AuditLogger:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.audit_dir = os.path.join(self.base_dir, "data", "audit_logs")
        self.logs_file = os.path.join(self.audit_dir, "audit_logs.json")
        self.reports_file = os.path.join(self.audit_dir, "compliance_reports.json")
        
        os.makedirs(self.audit_dir, exist_ok=True)
        
        # Load data
        self.logs = self._load_logs()
        self.reports = self._load_reports()
        
        # Compliance standards
        self.compliance_standards = self._initialize_compliance_standards()

    def _load_logs(self) -> Dict[str, AuditLogEntry]:
        """Load audit logs from disk."""
        if os.path.exists(self.logs_file):
            try:
                with open(self.logs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {log_id: AuditLogEntry(**log) for log_id, log in data.items()}
            except Exception:
                pass
        return {}

    def _save_logs(self):
        """Save audit logs to disk."""
        try:
            data = {log_id: asdict(log) for log_id, log in self.logs.items()}
            with open(self.logs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AuditLogger] Failed to save logs: {e}")

    def _load_reports(self) -> Dict[str, ComplianceReport]:
        """Load compliance reports from disk."""
        if os.path.exists(self.reports_file):
            try:
                with open(self.reports_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {report_id: ComplianceReport(**report) for report_id, report in data.items()}
            except Exception:
                pass
        return {}

    def _save_reports(self):
        """Save compliance reports to disk."""
        try:
            data = {report_id: asdict(report) for report_id, report in self.reports.items()}
            with open(self.reports_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AuditLogger] Failed to save reports: {e}")

    def _initialize_compliance_standards(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance standards and requirements."""
        return {
            'GDPR': {
                'name': 'General Data Protection Regulation',
                'data_retention_days': 365,
                'right_to_deletion': True,
                'consent_required': True,
                'breach_notification_hours': 72
            },
            'HIPAA': {
                'name': 'Health Insurance Portability and Accountability Act',
                'data_retention_days': 1825,
                'right_to_deletion': False,
                'consent_required': True,
                'breach_notification_hours': 60
            },
            'SOC2': {
                'name': 'Service Organization Control 2',
                'data_retention_days': 2555,
                'right_to_deletion': True,
                'consent_required': True,
                'breach_notification_hours': 24
            },
            'ISO27001': {
                'name': 'ISO/IEC 27001',
                'data_retention_days': 1825,
                'right_to_deletion': True,
                'consent_required': True,
                'breach_notification_hours': 48
            }
        }

    def log_event(self, event_type: AuditEventType, action: str, 
                 user_id: str = None, resource: str = None, outcome: str = "success",
                 severity: AuditSeverity = AuditSeverity.INFO,
                 ip_address: str = None, user_agent: str = None,
                 details: Dict[str, Any] = None, compliance_tags: List[str] = None) -> AuditLogEntry:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Action performed
            user_id: User ID who performed the action
            resource: Resource affected
            outcome: Outcome of the action
            severity: Severity level
            ip_address: IP address
            user_agent: User agent string
            details: Additional details
            compliance_tags: Compliance tags for reporting
            
        Returns:
            AuditLogEntry
        """
        log_id = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        log_entry = AuditLogEntry(
            log_id=log_id,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            action=action,
            resource=resource,
            outcome=outcome,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            compliance_tags=compliance_tags or []
        )
        
        self.logs[log_id] = log_entry
        self._save_logs()
        
        return log_entry

    def log_authentication(self, user_id: str, method: str, outcome: str,
                          ip_address: str = None, user_agent: str = None) -> AuditLogEntry:
        """Log authentication event."""
        return self.log_event(
            event_type=AuditEventType.AUTHENTICATION,
            action=f"Authentication attempt via {method}",
            user_id=user_id,
            outcome=outcome,
            severity=AuditSeverity.WARNING if outcome == "failure" else AuditSeverity.INFO,
            ip_address=ip_address,
            user_agent=user_agent,
            details={'method': method},
            compliance_tags=['GDPR', 'SOC2', 'ISO27001']
        )

    def log_authorization(self, user_id: str, resource: str, action: str,
                        outcome: str, ip_address: str = None) -> AuditLogEntry:
        """Log authorization event."""
        return self.log_event(
            event_type=AuditEventType.AUTHORIZATION,
            action=f"Authorization check for {action}",
            user_id=user_id,
            resource=resource,
            outcome=outcome,
            severity=AuditSeverity.WARNING if outcome == "failure" else AuditSeverity.INFO,
            ip_address=ip_address,
            details={'requested_action': action},
            compliance_tags=['GDPR', 'SOC2']
        )

    def log_data_access(self, user_id: str, resource: str, access_type: str,
                      ip_address: str = None) -> AuditLogEntry:
        """Log data access event."""
        return self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            action=f"Data access: {access_type}",
            user_id=user_id,
            resource=resource,
            outcome="success",
            severity=AuditSeverity.INFO,
            ip_address=ip_address,
            details={'access_type': access_type},
            compliance_tags=['GDPR', 'HIPAA', 'SOC2']
        )

    def log_data_modification(self, user_id: str, resource: str, modification_type: str,
                            outcome: str, ip_address: str = None) -> AuditLogEntry:
        """Log data modification event."""
        return self.log_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            action=f"Data modification: {modification_type}",
            user_id=user_id,
            resource=resource,
            outcome=outcome,
            severity=AuditSeverity.ERROR if outcome == "failure" else AuditSeverity.INFO,
            ip_address=ip_address,
            details={'modification_type': modification_type},
            compliance_tags=['GDPR', 'SOC2', 'ISO27001']
        )

    def log_security_event(self, event_type: str, severity: AuditSeverity,
                         details: Dict[str, Any] = None) -> AuditLogEntry:
        """Log security event."""
        return self.log_event(
            event_type=AuditEventType.SECURITY,
            action=event_type,
            outcome="logged",
            severity=severity,
            details=details or {},
            compliance_tags=['SOC2', 'ISO27001', 'HIPAA']
        )

    def log_privacy_event(self, user_id: str, action: str, resource: str = None,
                        details: Dict[str, Any] = None) -> AuditLogEntry:
        """Log privacy-related event."""
        return self.log_event(
            event_type=AuditEventType.PRIVACY,
            action=action,
            user_id=user_id,
            resource=resource,
            outcome="logged",
            severity=AuditSeverity.INFO,
            details=details or {},
            compliance_tags=['GDPR', 'HIPAA']
        )

    def get_logs(self, event_type: AuditEventType = None, user_id: str = None,
                severity: AuditSeverity = None, start_date: str = None,
                end_date: str = None, limit: int = 100) -> List[AuditLogEntry]:
        """
        Retrieve audit logs with filters.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            severity: Filter by severity
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of results
            
        Returns:
            List of AuditLogEntry
        """
        filtered_logs = list(self.logs.values())
        
        # Apply filters
        if event_type:
            filtered_logs = [log for log in filtered_logs if log.event_type == event_type]
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        
        if severity:
            filtered_logs = [log for log in filtered_logs if log.severity == severity]
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered_logs = [log for log in filtered_logs 
                          if datetime.fromisoformat(log.timestamp) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered_logs = [log for log in filtered_logs 
                          if datetime.fromisoformat(log.timestamp) <= end_dt]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_logs[:limit]

    def get_user_activity(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get user activity summary.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            Activity summary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        user_logs = [
            log for log in self.logs.values()
            if log.user_id == user_id and datetime.fromisoformat(log.timestamp) >= cutoff_date
        ]
        
        # Count by event type
        by_event_type = defaultdict(int)
        for log in user_logs:
            by_event_type[log.event_type.value] += 1
        
        # Count by outcome
        by_outcome = defaultdict(int)
        for log in user_logs:
            by_outcome[log.outcome] += 1
        
        # Count by severity
        by_severity = defaultdict(int)
        for log in user_logs:
            by_severity[log.severity.value] += 1
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_events': len(user_logs),
            'by_event_type': dict(by_event_type),
            'by_outcome': dict(by_outcome),
            'by_severity': dict(by_severity),
            'first_activity': min(log.timestamp for log in user_logs) if user_logs else None,
            'last_activity': max(log.timestamp for log in user_logs) if user_logs else None
        }

    def generate_compliance_report(self, standard: str, days: int = 30) -> ComplianceReport:
        """
        Generate a compliance report for a specific standard.
        
        Args:
            standard: Compliance standard (GDPR, HIPAA, SOC2, ISO27001)
            days: Number of days to include in report
            
        Returns:
            ComplianceReport
        """
        if standard not in self.compliance_standards:
            raise ValueError(f"Unknown compliance standard: {standard}")
        
        report_id = f"report_{standard}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        period_end = datetime.now()
        period_start = period_end - timedelta(days=days)
        
        # Get relevant logs
        relevant_logs = [
            log for log in self.logs.values()
            if standard.lower() in [tag.lower() for tag in log.compliance_tags]
            and datetime.fromisoformat(log.timestamp) >= period_start
        ]
        
        # Analyze logs
        findings = self._analyze_compliance_logs(relevant_logs, standard)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(findings, standard)
        
        # Summary
        summary = {
            'standard': standard,
            'standard_name': self.compliance_standards[standard]['name'],
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'total_events': len(relevant_logs),
            'critical_events': len([log for log in relevant_logs if log.severity == AuditSeverity.CRITICAL]),
            'failed_events': len([log for log in relevant_logs if log.outcome == 'failure']),
            'compliance_score': self._calculate_compliance_score(findings, standard)
        }
        
        report = ComplianceReport(
            report_id=report_id,
            report_type=standard,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            generated_at=datetime.now().isoformat(),
            summary=summary,
            findings=findings,
            recommendations=recommendations
        )
        
        self.reports[report_id] = report
        self._save_reports()
        
        return report

    def _analyze_compliance_logs(self, logs: List[AuditLogEntry], standard: str) -> List[Dict[str, Any]]:
        """Analyze logs for compliance findings."""
        findings = []
        
        # Check for failed authentication attempts
        failed_auth = [log for log in logs if log.event_type == AuditEventType.AUTHENTICATION and log.outcome == 'failure']
        if len(failed_auth) > 5:
            findings.append({
                'type': 'security',
                'severity': 'high',
                'description': f'{len(failed_auth)} failed authentication attempts detected',
                'recommendation': 'Review authentication logs and consider account lockout policies'
            })
        
        # Check for unauthorized access attempts
        unauthorized = [log for log in logs if log.event_type == AuditEventType.AUTHORIZATION and log.outcome == 'failure']
        if len(unauthorized) > 3:
            findings.append({
                'type': 'authorization',
                'severity': 'high',
                'description': f'{len(unauthorized)} unauthorized access attempts',
                'recommendation': 'Review access permissions and investigate suspicious activity'
            })
        
        # Check for data access without proper logging
        data_access = [log for log in logs if log.event_type == AuditEventType.DATA_ACCESS]
        if len(data_access) == 0:
            findings.append({
                'type': 'logging',
                'severity': 'medium',
                'description': 'No data access events logged',
                'recommendation': 'Ensure all data access is properly logged for compliance'
            })
        
        # Check for critical security events
        critical_events = [log for log in logs if log.severity == AuditSeverity.CRITICAL]
        if critical_events:
            findings.append({
                'type': 'security',
                'severity': 'critical',
                'description': f'{len(critical_events)} critical security events detected',
                'recommendation': 'Immediate investigation required'
            })
        
        return findings

    def _generate_recommendations(self, findings: List[Dict[str, Any]], standard: str) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []
        
        standard_config = self.compliance_standards[standard]
        
        # Data retention check
        if standard_config['data_retention_days']:
            recommendations.append(
                f"Ensure data retention policy complies with {standard_config['name']} "
                f"({standard_config['data_retention_days']} days)"
            )
        
        # Right to deletion check
        if standard_config['right_to_deletion']:
            recommendations.append(
                "Verify data deletion processes are in place per GDPR requirements"
            )
        
        # Breach notification check
        recommendations.append(
            f"Ensure breach notification procedures meet {standard_config['breach_notification_hours']} "
            f"hour requirement"
        )
        
        # Add finding-specific recommendations
        for finding in findings:
            if 'recommendation' in finding:
                recommendations.append(finding['recommendation'])
        
        return list(set(recommendations))  # Remove duplicates

    def _calculate_compliance_score(self, findings: List[Dict[str, Any]], standard: str) -> float:
        """Calculate overall compliance score."""
        if not findings:
            return 100.0
        
        # Deduct points based on severity
        score = 100.0
        for finding in findings:
            if finding['severity'] == 'critical':
                score -= 25
            elif finding['severity'] == 'high':
                score -= 15
            elif finding['severity'] == 'medium':
                score -= 10
            elif finding['severity'] == 'low':
                score -= 5
        
        return max(0.0, score)

    def get_audit_trail(self, resource: str, days: int = 30) -> List[AuditLogEntry]:
        """
        Get complete audit trail for a resource.
        
        Args:
            resource: Resource identifier
            days: Number of days to look back
            
        Returns:
            List of AuditLogEntry
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        trail = [
            log for log in self.logs.values()
            if log.resource == resource and datetime.fromisoformat(log.timestamp) >= cutoff_date
        ]
        
        trail.sort(key=lambda x: x.timestamp)
        
        return trail

    def export_logs(self, export_path: str, start_date: str = None, 
                   end_date: str = None) -> Tuple[bool, str]:
        """
        Export audit logs to a file.
        
        Args:
            export_path: Path to export file
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            (success, message)
        """
        try:
            logs_to_export = self.get_logs(
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'period_start': start_date,
                'period_end': end_date,
                'total_logs': len(logs_to_export),
                'logs': [asdict(log) for log in logs_to_export]
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Exported {len(logs_to_export)} logs to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def export_report(self, report_id: str, export_path: str) -> Tuple[bool, str]:
        """
        Export a compliance report.
        
        Args:
            report_id: Report ID
            export_path: Path to export file
            
        Returns:
            (success, message)
        """
        if report_id not in self.reports:
            return False, f"Report not found: {report_id}"
        
        try:
            report = self.reports[report_id]
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(report), f, indent=2)
            
            return True, f"Report exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        total_logs = len(self.logs)
        
        if total_logs == 0:
            return {
                'total_logs': 0,
                'by_event_type': {},
                'by_severity': {},
                'by_outcome': {}
            }
        
        # Count by event type
        by_event_type = defaultdict(int)
        for log in self.logs.values():
            by_event_type[log.event_type.value] += 1
        
        # Count by severity
        by_severity = defaultdict(int)
        for log in self.logs.values():
            by_severity[log.severity.value] += 1
        
        # Count by outcome
        by_outcome = defaultdict(int)
        for log in self.logs.values():
            by_outcome[log.outcome] += 1
        
        return {
            'total_logs': total_logs,
            'by_event_type': dict(by_event_type),
            'by_severity': dict(by_severity),
            'by_outcome': dict(by_outcome),
            'total_reports': len(self.reports)
        }

    def archive_old_logs(self, days: int = 90) -> int:
        """
        Archive logs older than specified days.
        
        Args:
            days: Age in days to archive
            
        Returns:
            Number of logs archived
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logs_to_archive = [
            log_id for log_id, log in self.logs.items()
            if datetime.fromisoformat(log.timestamp) < cutoff_date
        ]
        
        archived_count = len(logs_to_archive)
        
        # Remove from active logs
        for log_id in logs_to_archive:
            del self.logs[log_id]
        
        if archived_count > 0:
            self._save_logs()
        
        return archived_count

    def detect_anomalies(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Detect anomalous patterns in audit logs.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of detected anomalies
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_logs = [
            log for log in self.logs.values()
            if datetime.fromisoformat(log.timestamp) >= cutoff_date
        ]
        
        anomalies = []
        
        # Check for unusual authentication patterns
        auth_logs = [log for log in recent_logs if log.event_type == AuditEventType.AUTHENTICATION]
        user_auth_counts = defaultdict(int)
        for log in auth_logs:
            if log.user_id:
                user_auth_counts[log.user_id] += 1
        
        # Flag users with unusually high authentication attempts
        avg_auth = sum(user_auth_counts.values()) / len(user_auth_counts) if user_auth_counts else 0
        for user_id, count in user_auth_counts.items():
            if count > avg_auth * 3:  # 3x above average
                anomalies.append({
                    'type': 'authentication',
                    'severity': 'high',
                    'description': f'User {user_id} has {count} authentication attempts (avg: {avg_auth:.1f})',
                    'user_id': user_id
                })
        
        # Check for failed authorization spikes
        authz_logs = [log for log in recent_logs if log.event_type == AuditEventType.AUTHORIZATION]
        failed_authz = [log for log in authz_logs if log.outcome == 'failure']
        
        if len(failed_authz) > len(authz_logs) * 0.3:  # More than 30% failures
            anomalies.append({
                'type': 'authorization',
                'severity': 'high',
                'description': f'High authorization failure rate: {len(failed_authz)}/{len(authz_logs)}'
            })
        
        # Check for security event spikes
        security_logs = [log for log in recent_logs if log.event_type == AuditEventType.SECURITY]
        critical_logs = [log for log in security_logs if log.severity == AuditSeverity.CRITICAL]
        
        if len(critical_logs) > 0:
            anomalies.append({
                'type': 'security',
                'severity': 'critical',
                'description': f'{len(critical_logs)} critical security events detected'
            })
        
        return anomalies
