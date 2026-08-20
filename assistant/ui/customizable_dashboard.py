"""
Customizable Dashboards
Provides customizable dashboard configuration for personalized UI.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class WidgetType(Enum):
    WEATHER = "weather"
    CALENDAR = "calendar"
    TASKS = "tasks"
    SMART_HOME = "smart_home"
    MUSIC = "music"
    NEWS = "news"
    STATISTICS = "statistics"
    QUICK_ACTIONS = "quick_actions"
    VOICE_STATUS = "voice_status"
    CUSTOM = "custom"


class LayoutType(Enum):
    GRID = "grid"
    LIST = "list"
    MASONRY = "masonry"
    FREEFORM = "freeform"


@dataclass
class Widget:
    widget_id: str
    widget_type: WidgetType
    title: str
    position: Dict[str, int]  # {'x': 0, 'y': 0, 'w': 2, 'h': 2}
    config: Dict[str, Any]
    is_enabled: bool
    created_at: str


@dataclass
class Dashboard:
    dashboard_id: str
    user_id: str
    name: str
    layout_type: LayoutType
    widgets: List[str]
    theme: str  # 'light', 'dark', 'auto'
    is_default: bool
    created_at: str
    updated_at: str


class DashboardManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.ui_dir = os.path.join(self.base_dir, "data", "ui")
        self.dashboards_file = os.path.join(self.ui_dir, "dashboards.json")
        self.widgets_file = os.path.join(self.ui_dir, "dashboard_widgets.json")
        
        os.makedirs(self.ui_dir, exist_ok=True)
        
        # Load data
        self.dashboards = self._load_dashboards()
        self.widgets = self._load_widgets()

    def _load_dashboards(self) -> Dict[str, Dashboard]:
        """Load dashboards from disk."""
        if os.path.exists(self.dashboards_file):
            try:
                with open(self.dashboards_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {dashboard_id: Dashboard(**dashboard) for dashboard_id, dashboard in data.items()}
            except Exception:
                pass
        return {}

    def _save_dashboards(self):
        """Save dashboards to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {dashboard_id: asdict(dashboard) for dashboard_id, dashboard in self.dashboards.items()}
            with open(self.dashboards_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[DashboardManager] Failed to save dashboards: {e}")

    def _load_widgets(self) -> Dict[str, Widget]:
        """Load widgets from disk."""
        if os.path.exists(self.widgets_file):
            try:
                with open(self.widgets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {widget_id: Widget(**widget) for widget_id, widget in data.items()}
            except Exception:
                pass
        return {}

    def _save_widgets(self):
        """Save widgets to disk."""
        try:
            data = {widget_id: asdict(widget) for widget_id, widget in self.widgets.items()}
            with open(self.widgets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DashboardManager] Failed to save widgets: {e}")

    def create_dashboard(self, user_id: str, name: str, layout_type: LayoutType = LayoutType.GRID,
                       theme: str = "auto") -> Dashboard:
        """
        Create a new dashboard.
        
        Args:
            user_id: User ID
            name: Dashboard name
            layout_type: Layout type
            theme: Theme preference
            
        Returns:
            Dashboard
        """
        dashboard_id = f"dashboard_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        dashboard = Dashboard(
            dashboard_id=dashboard_id,
            user_id=user_id,
            name=name,
            layout_type=layout_type,
            widgets=[],
            theme=theme,
            is_default=False,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.dashboards[dashboard_id] = dashboard
        self._save_dashboards()
        
        return dashboard

    def add_widget(self, dashboard_id: str, widget_type: WidgetType, title: str,
                 position: Dict[str, int], config: Dict[str, Any] = None) -> Widget:
        """
        Add a widget to a dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            widget_type: Widget type
            title: Widget title
            position: Widget position {'x': 0, 'y': 0, 'w': 2, 'h': 2}
            config: Widget configuration
            
        Returns:
            Widget
        """
        if dashboard_id not in self.dashboards:
            raise ValueError(f"Dashboard not found: {dashboard_id}")
        
        widget_id = f"widget_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        widget = Widget(
            widget_id=widget_id,
            widget_type=widget_type,
            title=title,
            position=position,
            config=config or {},
            is_enabled=True,
            created_at=datetime.now().isoformat()
        )
        
        self.widgets[widget_id] = widget
        self.dashboards[dashboard_id].widgets.append(widget_id)
        self.dashboards[dashboard_id].updated_at = datetime.now().isoformat()
        
        self._save_widgets()
        self._save_dashboards()
        
        return widget

    def update_widget_position(self, widget_id: str, position: Dict[str, int]) -> bool:
        """Update widget position."""
        if widget_id not in self.widgets:
            return False
        
        self.widgets[widget_id].position = position
        self._save_widgets()
        
        return True

    def update_widget_config(self, widget_id: str, config: Dict[str, Any]) -> bool:
        """Update widget configuration."""
        if widget_id not in self.widgets:
            return False
        
        self.widgets[widget_id].config.update(config)
        self._save_widgets()
        
        return True

    def enable_widget(self, widget_id: str) -> bool:
        """Enable a widget."""
        if widget_id not in self.widgets:
            return False
        
        self.widgets[widget_id].is_enabled = True
        self._save_widgets()
        
        return True

    def disable_widget(self, widget_id: str) -> bool:
        """Disable a widget."""
        if widget_id not in self.widgets:
            return False
        
        self.widgets[widget_id].is_enabled = False
        self._save_widgets()
        
        return True

    def remove_widget(self, dashboard_id: str, widget_id: str) -> bool:
        """Remove a widget from a dashboard."""
        if dashboard_id not in self.dashboards:
            return False
        
        if widget_id not in self.dashboards[dashboard_id].widgets:
            return False
        
        self.dashboards[dashboard_id].widgets.remove(widget_id)
        self.dashboards[dashboard_id].updated_at = datetime.now().isoformat()
        self._save_dashboards()
        
        # Delete widget if not used elsewhere
        if not any(widget_id in d.widgets for d in self.dashboards.values()):
            del self.widgets[widget_id]
            self._save_widgets()
        
        return True

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get a dashboard by ID."""
        return self.dashboards.get(dashboard_id)

    def get_user_dashboards(self, user_id: str) -> List[Dashboard]:
        """Get all dashboards for a user."""
        return [d for d in self.dashboards.values() if d.user_id == user_id]

    def get_default_dashboard(self, user_id: str) -> Optional[Dashboard]:
        """Get default dashboard for a user."""
        user_dashboards = self.get_user_dashboards(user_id)
        for dashboard in user_dashboards:
            if dashboard.is_default:
                return dashboard
        return user_dashboards[0] if user_dashboards else None

    def set_default_dashboard(self, dashboard_id: str) -> bool:
        """Set a dashboard as default for its user."""
        if dashboard_id not in self.dashboards:
            return False
        
        dashboard = self.dashboards[dashboard_id]
        user_id = dashboard.user_id
        
        # Remove default from other dashboards
        for d in self.dashboards.values():
            if d.user_id == user_id:
                d.is_default = False
        
        dashboard.is_default = True
        self._save_dashboards()
        
        return True

    def update_dashboard_theme(self, dashboard_id: str, theme: str) -> bool:
        """Update dashboard theme."""
        if dashboard_id not in self.dashboards:
            return False
        
        self.dashboards[dashboard_id].theme = theme
        self.dashboards[dashboard_id].updated_at = datetime.now().isoformat()
        self._save_dashboards()
        
        return True

    def update_dashboard_layout(self, dashboard_id: str, layout_type: LayoutType) -> bool:
        """Update dashboard layout type."""
        if dashboard_id not in self.dashboards:
            return False
        
        self.dashboards[dashboard_id].layout_type = layout_type
        self.dashboards[dashboard_id].updated_at = datetime.now().isoformat()
        self._save_dashboards()
        
        return True

    def get_dashboard_widgets(self, dashboard_id: str) -> List[Widget]:
        """Get all widgets for a dashboard."""
        if dashboard_id not in self.dashboards:
            return []
        
        dashboard = self.dashboards[dashboard_id]
        return [self.widgets[wid] for wid in dashboard.widgets if wid in self.widgets]

    def get_enabled_widgets(self, dashboard_id: str) -> List[Widget]:
        """Get enabled widgets for a dashboard."""
        widgets = self.get_dashboard_widgets(dashboard_id)
        return [w for w in widgets if w.is_enabled]

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard."""
        if dashboard_id not in self.dashboards:
            return False
        
        dashboard = self.dashboards[dashboard_id]
        
        # Remove widgets
        for widget_id in dashboard.widgets:
            if widget_id in self.widgets:
                del self.widgets[widget_id]
        
        del self.dashboards[dashboard_id]
        self._save_dashboards()
        self._save_widgets()
        
        return True

    def duplicate_dashboard(self, dashboard_id: str, new_name: str) -> Optional[Dashboard]:
        """Duplicate a dashboard."""
        if dashboard_id not in self.dashboards:
            return None
        
        original = self.dashboards[dashboard_id]
        
        new_dashboard = self.create_dashboard(
            user_id=original.user_id,
            name=new_name,
            layout_type=original.layout_type,
            theme=original.theme
        )
        
        # Copy widgets
        for widget_id in original.widgets:
            if widget_id in self.widgets:
                original_widget = self.widgets[widget_id]
                new_widget = self.add_widget(
                    dashboard_id=new_dashboard.dashboard_id,
                    widget_type=original_widget.widget_type,
                    title=original_widget.title,
                    position=original_widget.position.copy(),
                    config=original_widget.config.copy()
                )
        
        return new_dashboard

    def get_statistics(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        total_dashboards = len(self.dashboards)
        total_widgets = len(self.widgets)
        
        # Count by layout type
        by_layout = {}
        for dashboard in self.dashboards.values():
            layout = dashboard.layout_type.value
            by_layout[layout] = by_layout.get(layout, 0) + 1
        
        # Count by widget type
        by_widget_type = {}
        for widget in self.widgets.values():
            wtype = widget.widget_type.value
            by_widget_type[wtype] = by_widget_type.get(wtype, 0) + 1
        
        return {
            'total_dashboards': total_dashboards,
            'total_widgets': total_widgets,
            'by_layout': by_layout,
            'by_widget_type': by_widget_type
        }

    def export_dashboard(self, dashboard_id: str, export_path: str) -> Tuple[bool, str]:
        """Export dashboard configuration."""
        if dashboard_id not in self.dashboards:
            return False, "Dashboard not found"
        
        dashboard = self.dashboards[dashboard_id]
        widgets = self.get_dashboard_widgets(dashboard_id)
        
        export_data = {
            'dashboard': asdict(dashboard),
            'widgets': [asdict(w) for w in widgets],
            'exported_at': datetime.now().isoformat()
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            return True, f"Dashboard exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
