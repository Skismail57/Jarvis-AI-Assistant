"""
Performance Monitoring and Profiling
Provides performance monitoring and profiling capabilities.
"""

import os
import json
import time
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from functools import wraps
import traceback


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str]
    timestamp: str


@dataclass
class PerformanceAlert:
    alert_id: str
    metric_name: str
    severity: AlertSeverity
    threshold: float
    current_value: float
    message: str
    triggered_at: str
    resolved_at: Optional[str]


@dataclass
class ProfileData:
    profile_id: str
    function_name: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    call_count: int
    timestamp: str


class PerformanceMonitor:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.performance_dir = os.path.join(self.base_dir, "data", "performance")
        self.metrics_file = os.path.join(self.performance_dir, "metrics.json")
        self.alerts_file = os.path.join(self.performance_dir, "alerts.json")
        self.profiles_file = os.path.join(self.performance_dir, "profiles.json")
        
        os.makedirs(self.performance_dir, exist_ok=True)
        
        # Load data
        self.metrics = self._load_metrics()
        self.alerts = self._load_alerts()
        self.profiles = self._load_profiles()
        
        # Alert thresholds
        self.alert_thresholds = {
            'response_time_ms': 1000,
            'memory_usage_mb': 512,
            'cpu_usage_percent': 80,
            'error_rate': 0.05
        }

    def _load_metrics(self) -> Dict[str, PerformanceMetric]:
        """Load metrics from disk."""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {metric_id: PerformanceMetric(**metric) for metric_id, metric in data.items()}
            except Exception:
                pass
        return {}

    def _save_metrics(self):
        """Save metrics to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {metric_id: asdict(metric) for metric_id, metric in self.metrics.items()}
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[PerformanceMonitor] Failed to save metrics: {e}")

    def _load_alerts(self) -> Dict[str, PerformanceAlert]:
        """Load alerts from disk."""
        if os.path.exists(self.alerts_file):
            try:
                with open(self.alerts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {alert_id: PerformanceAlert(**alert) for alert_id, alert in data.items()}
            except Exception:
                pass
        return {}

    def _save_alerts(self):
        """Save alerts to disk."""
        try:
            data = {alert_id: asdict(alert) for alert_id, alert in self.alerts.items()}
            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PerformanceMonitor] Failed to save alerts: {e}")

    def _load_profiles(self) -> Dict[str, ProfileData]:
        """Load profiles from disk."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {profile_id: ProfileData(**profile) for profile_id, profile in data.items()}
            except Exception:
                pass
        return {}

    def _save_profiles(self):
        """Save profiles to disk."""
        try:
            data = {profile_id: asdict(profile) for profile_id, profile in self.profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PerformanceMonitor] Failed to save profiles: {e}")

    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE,
                     labels: Dict[str, str] = None) -> PerformanceMetric:
        """
        Record a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Additional labels
            
        Returns:
            PerformanceMetric
        """
        metric_id = f"metric_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        metric = PerformanceMetric(
            metric_id=metric_id,
            name=name,
            metric_type=metric_type,
            value=value,
            labels=labels or {},
            timestamp=datetime.now().isoformat()
        )
        
        self.metrics[metric_id] = metric
        self._save_metrics()
        
        # Check for alerts
        self._check_alerts(name, value)
        
        return metric

    def _check_alerts(self, metric_name: str, value: float):
        """Check if metric value triggers an alert."""
        threshold = self.alert_thresholds.get(metric_name)
        if threshold is None:
            return
        
        severity = AlertSeverity.INFO
        if value > threshold * 2:
            severity = AlertSeverity.CRITICAL
        elif value > threshold * 1.5:
            severity = AlertSeverity.ERROR
        elif value > threshold:
            severity = AlertSeverity.WARNING
        
        if severity != AlertSeverity.INFO:
            alert_id = f"alert_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            alert = PerformanceAlert(
                alert_id=alert_id,
                metric_name=metric_name,
                severity=severity,
                threshold=threshold,
                current_value=value,
                message=f"{metric_name} exceeded threshold: {value} > {threshold}",
                triggered_at=datetime.now().isoformat(),
                resolved_at=None
            )
            
            self.alerts[alert_id] = alert
            self._save_alerts()

    def profile_function(self, func: Callable):
        """Decorator for profiling function performance."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
            
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            
            # Get memory usage
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / (1024 * 1024)
                cpu_percent = process.cpu_percent()
            except ImportError:
                memory_mb = 0
                cpu_percent = 0
            
            profile_id = f"profile_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            profile = ProfileData(
                profile_id=profile_id,
                function_name=func.__name__,
                execution_time_ms=execution_time_ms,
                memory_usage_mb=memory_mb,
                cpu_usage_percent=cpu_percent,
                call_count=1,
                timestamp=datetime.now().isoformat()
            )
            
            self.profiles[profile_id] = profile
            self._save_profiles()
            
            if not success:
                raise Exception(error) from e
            
            return result
        
        return wrapper

    def get_metrics(self, name: str = None, limit: int = 100) -> List[PerformanceMetric]:
        """Get metrics, optionally filtered by name."""
        metrics = list(self.metrics.values())
        
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        
        return metrics[:limit]

    def get_alerts(self, severity: AlertSeverity = None, 
                   resolved: bool = False) -> List[PerformanceAlert]:
        """Get alerts, optionally filtered."""
        alerts = list(self.alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if not resolved:
            alerts = [a for a in alerts if a.resolved_at is None]
        
        alerts.sort(key=lambda x: x.triggered_at, reverse=True)
        
        return alerts

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id not in self.alerts:
            return False
        
        self.alerts[alert_id].resolved_at = datetime.now().isoformat()
        self._save_alerts()
        
        return True

    def get_function_profiles(self, function_name: str = None) -> List[ProfileData]:
        """Get function profiles."""
        profiles = list(self.profiles.values())
        
        if function_name:
            profiles = [p for p in profiles if p.function_name == function_name]
        
        return profiles

    def get_average_execution_time(self, function_name: str) -> float:
        """Get average execution time for a function."""
        profiles = self.get_function_profiles(function_name)
        
        if not profiles:
            return 0.0
        
        return sum(p.execution_time_ms for p in profiles) / len(profiles)

    def get_slow_functions(self, threshold_ms: float = 100) -> List[ProfileData]:
        """Get functions slower than threshold."""
        return [p for p in self.profiles.values() if p.execution_time_ms > threshold_ms]

    def set_alert_threshold(self, metric_name: str, threshold: float):
        """Set alert threshold for a metric."""
        self.alert_thresholds[metric_name] = threshold

    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total_metrics = len(self.metrics)
        total_alerts = len(self.alerts)
        total_profiles = len(self.profiles)
        
        # Active alerts
        active_alerts = len([a for a in self.alerts.values() if a.resolved_at is None])
        
        # Count by severity
        by_severity = {}
        for alert in self.alerts.values():
            if alert.resolved_at is None:
                severity = alert.severity.value
                by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by metric type
        by_metric_type = {}
        for metric in self.metrics.values():
            mtype = metric.metric_type.value
            by_metric_type[mtype] = by_metric_type.get(mtype, 0) + 1
        
        return {
            'total_metrics': total_metrics,
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'total_profiles': total_profiles,
            'by_severity': by_severity,
            'by_metric_type': by_metric_type,
            'alert_thresholds': self.alert_thresholds
        }

    def clear_old_metrics(self, hours: int = 24) -> int:
        """Clear metrics older than specified hours."""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(hours=hours)
        
        to_remove = [
            metric_id for metric_id, metric in self.metrics.items()
            if datetime.fromisoformat(metric.timestamp) < cutoff_date
        ]
        
        for metric_id in to_remove:
            del self.metrics[metric_id]
        
        if to_remove:
            self._save_metrics()
        
        return len(to_remove)

    def export_performance_report(self, export_path: str) -> Tuple[bool, str]:
        """Export performance report to file."""
        try:
            report = {
                'statistics': self.get_statistics(),
                'slow_functions': [asdict(p) for p in self.get_slow_functions()],
                'active_alerts': [asdict(a) for a in self.get_alerts(resolved=False)],
                'recent_metrics': [asdict(m) for m in self.get_metrics(limit=50)],
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            return True, f"Report exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"


# Global monitor instance
_global_monitor = PerformanceMonitor()


def monitor_performance(func: Callable = None):
    """Decorator for monitoring function performance."""
    return _global_monitor.profile_function(func)


def record_metric(name: str, value: float, **labels):
    """Record a performance metric."""
    return _global_monitor.record_metric(name, value, labels=labels)


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _global_monitor
