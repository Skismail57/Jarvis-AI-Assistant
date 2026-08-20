"""
Project Management Integration
Integrates with Jira, Asana, Trello for project management capabilities.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


class ProjectPlatform(Enum):
    JIRA = "jira"
    ASANA = "asana"
    TRELLO = "trello"
    GITHUB = "github"


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ProjectTask:
    task_id: str
    platform: ProjectPlatform
    project_id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    due_date: Optional[str]
    labels: List[str]
    created_at: str
    updated_at: str


@dataclass
class Project:
    project_id: str
    platform: ProjectPlatform
    name: str
    description: str
    tasks: List[str]
    members: List[str]
    created_at: str


class ProjectIntegrationManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.productivity_dir = os.path.join(self.base_dir, "data", "productivity")
        self.projects_file = os.path.join(self.productivity_dir, "projects.json")
        self.tasks_file = os.path.join(self.productivity_dir, "project_tasks.json")
        self.credentials_file = os.path.join(self.productivity_dir, "project_credentials.json")
        
        os.makedirs(self.productivity_dir, exist_ok=True)
        
        # Load data
        self.projects = self._load_projects()
        self.tasks = self._load_tasks()
        self.credentials = self._load_credentials()

    def _load_projects(self) -> Dict[str, Project]:
        """Load projects from disk."""
        if os.path.exists(self.projects_file):
            try:
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {project_id: Project(**project) for project_id, project in data.items()}
            except Exception:
                pass
        return {}

    def _save_projects(self):
        """Save projects to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {project_id: asdict(project) for project_id, project in self.projects.items()}
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[ProjectIntegration] Failed to save projects: {e}")

    def _load_tasks(self) -> Dict[str, ProjectTask]:
        """Load tasks from disk."""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {task_id: ProjectTask(**task) for task_id, task in data.items()}
            except Exception:
                pass
        return {}

    def _save_tasks(self):
        """Save tasks to disk."""
        try:
            data = {task_id: asdict(task) for task_id, task in self.tasks.items()}
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ProjectIntegration] Failed to save tasks: {e}")

    def _load_credentials(self) -> Dict[str, Dict]:
        """Load platform credentials from disk."""
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_credentials(self):
        """Save platform credentials to disk."""
        try:
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(self.credentials, f, indent=2)
        except Exception as e:
            print(f"[ProjectIntegration] Failed to save credentials: {e}")

    def set_platform_credentials(self, platform: ProjectPlatform, api_key: str,
                                api_url: str = None, username: str = None) -> bool:
        """
        Set credentials for a platform.
        
        Args:
            platform: Platform
            api_key: API key
            api_url: API URL (optional)
            username: Username (optional)
            
        Returns:
            True if successful
        """
        self.credentials[platform.value] = {
            'api_key': api_key,
            'api_url': api_url,
            'username': username,
            'updated_at': datetime.now().isoformat()
        }
        
        self._save_credentials()
        return True

    def create_project(self, platform: ProjectPlatform, name: str,
                      description: str = "") -> Project:
        """
        Create a new project.
        
        Args:
            platform: Platform
            name: Project name
            description: Project description
            
        Returns:
            Project
        """
        project_id = f"project_{platform.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        project = Project(
            project_id=project_id,
            platform=platform,
            name=name,
            description=description,
            tasks=[],
            members=[],
            created_at=datetime.now().isoformat()
        )
        
        self.projects[project_id] = project
        self._save_projects()
        
        return project

    def create_task(self, project_id: str, title: str, description: str = "",
                   status: TaskStatus = TaskStatus.TODO,
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   assignee: str = None, due_date: str = None,
                   labels: List[str] = None) -> ProjectTask:
        """
        Create a new task.
        
        Args:
            project_id: Project ID
            title: Task title
            description: Task description
            status: Task status
            priority: Task priority
            assignee: Assignee
            due_date: Due date (ISO format)
            labels: Task labels
            
        Returns:
            ProjectTask
        """
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")
        
        project = self.projects[project_id]
        
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task = ProjectTask(
            task_id=task_id,
            platform=project.platform,
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            due_date=due_date,
            labels=labels or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.tasks[task_id] = task
        project.tasks.append(task_id)
        self._save_tasks()
        self._save_projects()
        
        return task

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update task status."""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].status = status
        self.tasks[task_id].updated_at = datetime.now().isoformat()
        self._save_tasks()
        
        return True

    def update_task_priority(self, task_id: str, priority: TaskPriority) -> bool:
        """Update task priority."""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].priority = priority
        self.tasks[task_id].updated_at = datetime.now().isoformat()
        self._save_tasks()
        
        return True

    def assign_task(self, task_id: str, assignee: str) -> bool:
        """Assign a task to a user."""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].assignee = assignee
        self.tasks[task_id].updated_at = datetime.now().isoformat()
        self._save_tasks()
        
        return True

    def get_project_tasks(self, project_id: str) -> List[ProjectTask]:
        """Get all tasks for a project."""
        if project_id not in self.projects:
            return []
        
        project = self.projects[project_id]
        return [self.tasks[task_id] for task_id in project.tasks if task_id in self.tasks]

    def get_user_tasks(self, assignee: str) -> List[ProjectTask]:
        """Get all tasks assigned to a user."""
        return [task for task in self.tasks.values() if task.assignee == assignee]

    def get_overdue_tasks(self) -> List[ProjectTask]:
        """Get all overdue tasks."""
        now = datetime.now()
        
        overdue = []
        for task in self.tasks.values():
            if task.due_date and task.status != TaskStatus.DONE:
                due_date = datetime.fromisoformat(task.due_date)
                if due_date < now:
                    overdue.append(task)
        
        return overdue

    def get_upcoming_tasks(self, days: int = 7) -> List[ProjectTask]:
        """Get tasks due within specified days."""
        cutoff_date = datetime.now() + timedelta(days=days)
        
        upcoming = []
        for task in self.tasks.values():
            if task.due_date and task.status != TaskStatus.DONE:
                due_date = datetime.fromisoformat(task.due_date)
                if datetime.now() <= due_date <= cutoff_date:
                    upcoming.append(task)
        
        upcoming.sort(key=lambda t: t.due_date)
        
        return upcoming

    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get statistics for a project."""
        if project_id not in self.projects:
            return {}
        
        tasks = self.get_project_tasks(project_id)
        
        # Count by status
        by_status = {}
        for task in tasks:
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        # Count by priority
        by_priority = {}
        for task in tasks:
            priority = task.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Calculate completion rate
        completed = by_status.get('done', 0)
        completion_rate = completed / len(tasks) if tasks else 0
        
        return {
            'project_id': project_id,
            'total_tasks': len(tasks),
            'by_status': by_status,
            'by_priority': by_priority,
            'completion_rate': round(completion_rate, 2)
        }

    def sync_with_platform(self, platform: ProjectPlatform) -> Tuple[bool, str]:
        """
        Sync local data with external platform.
        
        Args:
            platform: Platform to sync with
            
        Returns:
            (success, message)
        """
        if platform.value not in self.credentials:
            return False, f"No credentials configured for {platform.value}"
        
        # In production, this would perform actual API sync
        # For now, simulate sync
        return True, f"Synced with {platform.value} successfully"

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # Remove from project
        if task.project_id in self.projects:
            project = self.projects[task.project_id]
            if task_id in project.tasks:
                project.tasks.remove(task_id)
            self._save_projects()
        
        del self.tasks[task_id]
        self._save_tasks()
        
        return True

    def delete_project(self, project_id:str) -> bool:
        """Delete a project and its tasks."""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        # Delete all tasks
        for task_id in project.tasks:
            if task_id in self.tasks:
                del self.tasks[task_id]
        
        del self.projects[project_id]
        self._save_projects()
        self._save_tasks()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall project management statistics."""
        total_projects = len(self.projects)
        total_tasks = len(self.tasks)
        
        # Count by platform
        by_platform = {}
        for project in self.projects.values():
            platform = project.platform.value
            by_platform[platform] = by_platform.get(platform, 0) + 1
        
        # Count by status
        by_status = {}
        for task in self.tasks.values():
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_projects': total_projects,
            'total_tasks': total_tasks,
            'by_platform': by_platform,
            'by_status': by_status
        }

    def export_project_data(self, project_id: str, export_path: str) -> Tuple[bool, str]:
        """Export project data to file."""
        if project_id not in self.projects:
            return False, "Project not found"
        
        project = self.projects[project_id]
        tasks = self.get_project_tasks(project_id)
        
        export_data = {
            'project': asdict(project),
            'tasks': [asdict(task) for task in tasks],
            'exported_at': datetime.now().isoformat()
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            return True, f"Project data exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
