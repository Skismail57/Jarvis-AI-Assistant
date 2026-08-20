"""
Usage Pattern Analysis and Productivity Metrics
Provides analytics for usage patterns and productivity tracking.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class MetricType(Enum):
    INTERACTION_COUNT = "interaction_count"
    SESSION_DURATION = "session_duration"
    TASK_COMPLETION = "task_completion"
    FEATURE_USAGE = "feature_usage"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"


class TimeGranularity(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class UsageEvent:
    event_id: str
    user_id: str
    event_type: str
    feature: str
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class ProductivityMetric:
    metric_id: str
    user_id: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: str
    context: Dict[str, Any]


@dataclass
class ProductivityReport:
    report_id: str
    user_id: str
    start_date: str
    end_date: str
    total_interactions: int
    total_session_time_minutes: float
    tasks_completed: int
    most_used_features: List[Tuple[str, int]]
    average_response_time_ms: float
    productivity_score: float
    generated_at: str


class UsageAnalyticsManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.analytics_dir = os.path.join(self.base_dir, "data", "analytics")
        self.events_file = os.path.join(self.analytics_dir, "usage_events.json")
        self.metrics_file = os.path.join(self.analytics_dir, "productivity_metrics.json")
        self.reports_file = os.path.join(self.analytics_dir, "productivity_reports.json")
        
        os.makedirs(self.analytics_dir, exist_ok=True)
        
        # Load data
        self.events = self._load_events()
        self.metrics = self._load_metrics()
        self.reports = self._load_reports()

    def _load_events(self) -> Dict[str, UsageEvent]:
        """Load usage events from disk."""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {event_id: UsageEvent(**event) for event_id, event in data.items()}
            except Exception:
                pass
        return {}

    def _save_events(self):
        """Save usage events to disk."""
        try:
            data = {event_id: asdict(event) for event_id, event in self.events.items()}
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[UsageAnalytics] Failed to save events: {e}")

    def _load_metrics(self) -> Dict[str, ProductivityMetric]:
        """Load productivity metrics from disk."""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {metric_id: ProductivityMetric(**metric) for metric_id, metric in data.items()}
            except Exception:
                pass
        return {}

    def _save_metrics(self):
        """Save productivity metrics to disk."""
        try:
            data = {metric_id: asdict(metric) for metric_id, metric in self.metrics.items()}
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[UsageAnalytics] Failed to save metrics: {e}")

    def _load_reports(self) -> Dict[str, ProductivityReport]:
        """Load productivity reports from disk."""
        if os.path.exists(self.reports_file):
            try:
                with open(self.reports_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {report_id: ProductivityReport(**report) for report_id, report in data.items()}
            except Exception:
                pass
        return {}

    def _save_reports(self):
        """Save productivity reports to disk."""
        try:
            data = {report_id: asdict(report) for report_id, report in self.reports.items()}
            with open(self.reports_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[UsageAnalytics] Failed to save reports: {e}")

    def log_event(self, user_id: str, event_type: str, feature: str,
                 metadata: Dict[str, Any] = None) -> UsageEvent:
        """
        Log a usage event.
        
        Args:
            user_id: User ID
            event_type: Type of event
            feature: Feature used
            metadata: Additional metadata
            
        Returns:
            UsageEvent
        """
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        event = UsageEvent(
            event_id=event_id,
            user_id=user_id,
            event_type=event_type,
            feature=feature,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        self.events[event_id] = event
        self._save_events()
        
        return event

    def record_metric(self, user_id: str, metric_type: MetricType, value: float,
                     unit: str = "", context: Dict[str, Any] = None) -> ProductivityMetric:
        """
        Record a productivity metric.
        
        Args:
            user_id: User ID
            metric_type: Type of metric
            value: Metric value
            unit: Unit of measurement
            context: Additional context
            
        Returns:
            ProductivityMetric
        """
        metric_id = f"metric_{metric_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        metric = ProductivityMetric(
            metric_id=metric_id,
            user_id=user_id,
            metric_type=metric_type,
            value=value,
            unit=unit,
            timestamp=datetime.now().isoformat(),
            context=context or {}
        )
        
        self.metrics[metric_id] = metric
        self._save_metrics()
        
        return metric

    def get_user_events(self, user_id: str, start_date: str = None,
                       end_date: str = None) -> List[UsageEvent]:
        """
        Get events for a user within a date range.
        
        Args:
            user_id: User ID
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            List of UsageEvents
        """
        events = [e for e in self.events.values() if e.user_id == user_id]
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            events = [e for e in events if datetime.fromisoformat(e.timestamp) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            events = [e for e in events if datetime.fromisoformat(e.timestamp) <= end]
        
        events.sort(key=lambda x: x.timestamp)
        
        return events

    def get_feature_usage(self, user_id: str = None, start_date: str = None,
                         end_date: str = None) -> Dict[str, int]:
        """
        Get feature usage statistics.
        
        Args:
            user_id: Optional user ID filter
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Dictionary of feature usage counts
        """
        events = list(self.events.values())
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            events = [e for e in events if datetime.fromisoformat(e.timestamp) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            events = [e for e in events if datetime.fromisoformat(e.timestamp) <= end]
        
        feature_counts = defaultdict(int)
        for event in events:
            feature_counts[event.feature] += 1
        
        return dict(feature_counts)

    def get_user_metrics(self, user_id: str, metric_type: MetricType = None,
                       start_date: str = None, end_date: str = None) -> List[ProductivityMetric]:
        """Get metrics for a user."""
        metrics = [m for m in self.metrics.values() if m.user_id == user_id]
        
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            metrics = [m for m in metrics if datetime.fromisoformat(m.timestamp) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            metrics = [m for m in metrics if datetime.fromisoformat(m.timestamp) <= end]
        
        return metrics

    def calculate_productivity_score(self, user_id: str, start_date: str,
                                   end_date: str) -> float:
        """
        Calculate a productivity score for a user.
        
        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Productivity score (0-100)
        """
        events = self.get_user_events(user_id, start_date, end_date)
        metrics = self.get_user_metrics(user_id, None, start_date, end_date)
        
        if not events:
            return 0.0
        
        # Factors for productivity score
        interaction_count = len(events)
        task_completion_metrics = [m for m in metrics if m.metric_type == MetricType.TASK_COMPLETION]
        tasks_completed = sum(m.value for m in task_completion_metrics)
        
        # Calculate score
        base_score = min(100, interaction_count * 2)  # Up to 100 points for interactions
        completion_bonus = min(50, tasks_completed * 10)  # Up to 50 points for tasks
        
        total_score = (base_score + completion_bonus) / 1.5  # Normalize to 0-100
        
        return round(min(100, total_score), 2)

    def generate_productivity_report(self, user_id: str, start_date: str,
                                   end_date: str) -> ProductivityReport:
        """
        Generate a productivity report.
        
        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            
        Returns:
            ProductivityReport
        """
        events = self.get_user_events(user_id, start_date, end_date)
        metrics = self.get_user_metrics(user_id, None, start_date, end_date)
        
        # Calculate total interactions
        total_interactions = len(events)
        
        # Calculate session time
        session_metrics = [m for m in metrics if m.metric_type == MetricType.SESSION_DURATION]
        total_session_time = sum(m.value for m in session_metrics)
        
        # Calculate tasks completed
        task_metrics = [m for m in metrics if m.metric_type == MetricType.TASK_COMPLETION]
        tasks_completed = sum(m.value for m in task_metrics)
        
        # Get most used features
        feature_usage = self.get_feature_usage(user_id, start_date, end_date)
        most_used_features = sorted(feature_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Calculate average response time
        response_metrics = [m for m in metrics if m.metric_type == MetricType.RESPONSE_TIME]
        avg_response_time = sum(m.value for m in response_metrics) / len(response_metrics) if response_metrics else 0
        
        # Calculate productivity score
        productivity_score = self.calculate_productivity_score(user_id, start_date, end_date)
        
        report_id = f"report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = ProductivityReport(
            report_id=report_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            total_interactions=total_interactions,
            total_session_time_minutes=total_session_time,
            tasks_completed=tasks_completed,
            most_used_features=most_used_features,
            average_response_time_ms=avg_response_time,
            productivity_score=productivity_score,
            generated_at=datetime.now().isoformat()
        )
        
        self.reports[report_id] = report
        self._save_reports()
        
        return report

    def get_usage_trends(self, user_id: str, metric_type: MetricType,
                       granularity: TimeGranularity = TimeGranularity.DAILY,
                       days: int = 30) -> Dict[str, float]:
        """
        Get usage trends over time.
        
        Args:
            user_id: User ID
            metric_type: Type of metric to analyze
            granularity: Time granularity
            days: Number of days to analyze
            
        Returns:
            Dictionary of time periods to values
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = self.get_user_metrics(user_id, metric_type, start_date.isoformat(), end_date.isoformat())
        
        # Group by time period
        trends = defaultdict(list)
        for metric in metrics:
            timestamp = datetime.fromisoformat(metric.timestamp)
            
            if granularity == TimeGranularity.HOURLY:
                key = timestamp.strftime('%Y-%m-%d %H:00')
            elif granularity == TimeGranularity.DAILY:
                key = timestamp.strftime('%Y-%m-%d')
            elif granularity == TimeGranularity.WEEKLY:
                key = timestamp.strftime('%Y-W%W')
            else:  # MONTHLY
                key = timestamp.strftime('%Y-%m')
            
            trends[key].append(metric.value)
        
        # Calculate averages
        return {k: sum(v) / len(v) if v else 0 for k, v in trends.items()}

    def get_report(self, report_id: str) -> Optional[ProductivityReport]:
        """Get a productivity report by ID."""
        return self.reports.get(report_id)

    def get_user_reports(self, user_id: str) -> List[ProductivityReport]:
        """Get all reports for a user."""
        return [r for r in self.reports.values() if r.user_id == user_id]

    def clear_old_events(self, days: int = 90) -> int:
        """Clear events older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            event_id for event_id, event in self.events.items()
            if datetime.fromisoformat(event.timestamp) < cutoff_date
        ]
        
        for event_id in to_remove:
            del self.events[event_id]
        
        if to_remove:
            self._save_events()
        
        return len(to_remove)

    def get_statistics(self) -> Dict[str, Any]:
        """Get analytics statistics."""
        total_events = len(self.events)
        total_metrics = len(self.metrics)
        total_reports = len(self.reports)
        
        # Count by event type
        event_types = defaultdict(int)
        for event in self.events.values():
            event_types[event.event_type] += 1
        
        # Count by feature
        features = defaultdict(int)
        for event in self.events.values():
            features[event.feature] += 1
        
        return {
            'total_events': total_events,
            'total_metrics': total_metrics,
            'total_reports': total_reports,
            'by_event_type': dict(event_types),
            'by_feature': dict(features)
        }

    def export_report(self, report_id: str, export_path: str) -> Tuple[bool, str]:
        """Export productivity report to file."""
        if report_id not in self.reports:
            return False, "Report not found"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.reports[report_id]), f, indent=2)
            return True, f"Report exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
