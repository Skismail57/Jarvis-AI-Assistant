"""
Natural Language Task Parser
Parses natural language input into structured tasks with dates, priorities, and context.
"""

import os
import json
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCategory(Enum):
    WORK = "work"
    PERSONAL = "personal"
    SHOPPING = "shopping"
    HEALTH = "health"
    FINANCE = "finance"
    HOME = "home"
    OTHER = "other"


@dataclass
class ParsedTask:
    task_id: str
    title: str
    description: str
    priority: TaskPriority
    category: TaskCategory
    due_date: Optional[str]
    due_time: Optional[str]
    assignee: Optional[str]
    tags: List[str]
    estimated_duration: Optional[int]  # in minutes
    recurring: bool
    recurring_pattern: Optional[str]
    parsed_at: str


class TaskParser:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.productivity_dir = os.path.join(self.base_dir, "data", "productivity")
        self.tasks_file = os.path.join(self.productivity_dir, "parsed_tasks.json")
        
        os.makedirs(self.productivity_dir, exist_ok=True)
        
        # Load tasks
        self.tasks = self._load_tasks()
        
        # Initialize patterns
        self._initialize_patterns()

    def _load_tasks(self) -> Dict[str, ParsedTask]:
        """Load parsed tasks from disk."""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {task_id: ParsedTask(**task) for task_id, task in data.items()}
            except Exception:
                pass
        return {}

    def _save_tasks(self):
        """Save tasks to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {task_id: asdict(task) for task_id, task in self.tasks.items()}
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[TaskParser] Failed to save tasks: {e}")

    def _initialize_patterns(self):
        """Initialize regex patterns for parsing."""
        self.date_patterns = {
            'today': r'\btoday\b',
            'tomorrow': r'\btomorrow\b',
            'next_week': r'\bnext week\b',
            'next_month': r'\bnext month\b',
            'in_x_days': r'\bin (\d+) days?\b',
            'on_date': r'\bon (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            'day_of_week': r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
        }
        
        self.time_patterns = {
            'at_time': r'\bat (\d{1,2}:\d{2})\b',
            'in_hours': r'\bin (\d+) hours?\b',
            'in_minutes': r'\bin (\d+) minutes?\b'
        }
        
        self.priority_patterns = {
            'urgent': r'\burgent\b',
            'high': r'\bhigh priority\b',
            'important': r'\bimportant\b',
            'low': r'\blow priority\b',
            'asap': r'\basap\b'
        }
        
        self.category_patterns = {
            'work': r'\bwork\b|\boffice\b|\bmeeting\b',
            'personal': r'\bpersonal\b|\bhome\b|\bmyself\b',
            'shopping': r'\bbuy\b|\bshop\b|\bpurchase\b|\bget\b',
            'health': r'\bexercise\b|\bworkout\b|\bdoctor\b|\bhealth\b',
            'finance': r'\bbill\b|\bpayment\b|\bbank\b|\bmoney\b',
            'home': r'\bclean\b|\bfix\b|\brepair\b|\bhousehold\b'
        }
        
        self.duration_patterns = {
            'hours': r'\b(\d+) hours?\b',
            'minutes': r'\b(\d+) minutes?\b',
            'duration': r'\btake (\d+) (hours?|minutes?)\b'
        }
        
        self.recurring_patterns = {
            'daily': r'\bdaily\b|\bevery day\b',
            'weekly': r'\bweekly\b|\bevery week\b',
            'monthly': r'\bmonthly\b|\bevery month\b'
        }

    def parse_task(self, text: str) -> ParsedTask:
        """
        Parse natural language text into a structured task.
        
        Args:
            text: Natural language task description
            
        Returns:
            ParsedTask
        """
        text_lower = text.lower()
        
        # Extract title (first sentence or first 50 chars)
        title = text.split('.')[0].strip()[:50]
        
        # Extract priority
        priority = self._extract_priority(text_lower)
        
        # Extract category
        category = self._extract_category(text_lower)
        
        # Extract due date
        due_date = self._extract_due_date(text_lower)
        
        # Extract due time
        due_time = self._extract_due_time(text_lower)
        
        # Extract assignee
        assignee = self._extract_assignee(text)
        
        # Extract tags
        tags = self._extract_tags(text)
        
        # Extract duration
        duration = self._extract_duration(text_lower)
        
        # Extract recurring pattern
        recurring, recurring_pattern = self._extract_recurring(text_lower)
        
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task = ParsedTask(
            task_id=task_id,
            title=title,
            description=text,
            priority=priority,
            category=category,
            due_date=due_date,
            due_time=due_time,
            assignee=assignee,
            tags=tags,
            estimated_duration=duration,
            recurring=recurring,
            recurring_pattern=recurring_pattern,
            parsed_at=datetime.now().isoformat()
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        return task

    def _extract_priority(self, text: str) -> TaskPriority:
        """Extract task priority from text."""
        if re.search(self.priority_patterns['urgent'], text):
            return TaskPriority.URGENT
        elif re.search(self.priority_patterns['high'], text) or re.search(self.priority_patterns['important'], text):
            return TaskPriority.HIGH
        elif re.search(self.priority_patterns['low'], text):
            return TaskPriority.LOW
        else:
            return TaskPriority.MEDIUM

    def _extract_category(self, text: str) -> TaskCategory:
        """Extract task category from text."""
        for category, pattern in self.category_patterns.items():
            if re.search(pattern, text):
                return TaskCategory(category)
        return TaskCategory.OTHER

    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text."""
        now = datetime.now()
        
        # Today
        if re.search(self.date_patterns['today'], text):
            return now.date().isoformat()
        
        # Tomorrow
        elif re.search(self.date_patterns['tomorrow'], text):
            return (now + timedelta(days=1)).date().isoformat()
        
        # Next week
        elif re.search(self.date_patterns['next_week'], text):
            return (now + timedelta(days=7)).date().isoformat()
        
        # Next month
        elif re.search(self.date_patterns['next_month'], text):
            return (now + timedelta(days=30)).date().isoformat()
        
        # In X days
        elif re.search(self.date_patterns['in_x_days'], text):
            match = re.search(self.date_patterns['in_x_days'], text)
            days = int(match.group(1))
            return (now + timedelta(days=days)).date().isoformat()
        
        # Specific date
        elif re.search(self.date_patterns['on_date'], text):
            match = re.search(self.date_patterns['on_date'], text)
            date_str = match.group(1)
            try:
                parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                return parsed_date.date().isoformat()
            except:
                try:
                    parsed_date = datetime.strptime(date_str, '%m-%d-%Y')
                    return parsed_date.date().isoformat()
                except:
                    pass
        
        return None

    def _extract_due_time(self, text: str) -> Optional[str]:
        """Extract due time from text."""
        # At specific time
        if re.search(self.time_patterns['at_time'], text):
            match = re.search(self.time_patterns['at_time'], text)
            return match.group(1)
        
        # In X hours
        elif re.search(self.time_patterns['in_hours'], text):
            match = re.search(self.time_patterns['in_hours'], text)
            hours = int(match.group(1))
            future_time = datetime.now() + timedelta(hours=hours)
            return future_time.strftime('%H:%M')
        
        # In X minutes
        elif re.search(self.time_patterns['in_minutes'], text):
            match = re.search(self.time_patterns['in_minutes'], text)
            minutes = int(match.group(1))
            future_time = datetime.now() + timedelta(minutes=minutes)
            return future_time.strftime('%H:%M')
        
        return None

    def _extract_assignee(self, text: str) -> Optional[str]:
        """Extract assignee from text."""
        # Look for "assign to X" or "for X" patterns
        assignee_patterns = [
            r'\bassign to (\w+)\b',
            r'\bfor (\w+)\b',
            r'\bby (\w+)\b'
        ]
        
        for pattern in assignee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def _extract_tags(self, text: str) -> List[str]:
        """Extract tags from text."""
        # Look for hashtags or keywords
        tags = []
        
        # Hashtags
        hashtag_matches = re.findall(r'#(\w+)', text)
        tags.extend(hashtag_matches)
        
        # Common keywords as tags
        keywords = ['urgent', 'important', 'follow-up', 'review', 'meeting']
        for keyword in keywords:
            if keyword in text.lower():
                tags.append(keyword)
        
        return tags

    def _extract_duration(self, text: str) -> Optional[int]:
        """Extract estimated duration in minutes."""
        # Hours
        match = re.search(self.duration_patterns['hours'], text)
        if match:
            return int(match.group(1)) * 60
        
        # Minutes
        match = re.search(self.duration_patterns['minutes'], text)
        if match:
            return int(match.group(1))
        
        return None

    def _extract_recurring(self, text: str) -> Tuple[bool, Optional[str]]:
        """Extract recurring pattern from text."""
        for pattern_name, pattern in self.recurring_patterns.items():
            if re.search(pattern, text):
                return True, pattern_name
        
        return False, None

    def get_task(self, task_id: str) -> Optional[ParsedTask]:
        """Get a parsed task by ID."""
        return self.tasks.get(task_id)

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[ParsedTask]:
        """Get tasks by priority."""
        return [task for task in self.tasks.values() if task.priority == priority]

    def get_tasks_by_category(self, category: TaskCategory) -> List[ParsedTask]:
        """Get tasks by category."""
        return [task for task in self.tasks.values() if task.category == category]

    def get_overdue_tasks(self) -> List[ParsedTask]:
        """Get overdue tasks."""
        now = datetime.now()
        
        overdue = []
        for task in self.tasks.values():
            if task.due_date:
                due_date = datetime.fromisoformat(task.due_date)
                if due_date < now:
                    overdue.append(task)
        
        return overdue

    def get_upcoming_tasks(self, days: int = 7) -> List[ParsedTask]:
        """Get tasks due within specified days."""
        cutoff_date = datetime.now() + timedelta(days=days)
        
        upcoming = []
        for task in self.tasks.values():
            if task.due_date:
                due_date = datetime.fromisoformat(task.due_date)
                if datetime.now() <= due_date <= cutoff_date:
                    upcoming.append(task)
        
        upcoming.sort(key=lambda t: t.due_date)
        
        return upcoming

    def delete_task(self, task_id: str) -> bool:
        """Delete a parsed task."""
        if task_id not in self.tasks:
            return False
        
        del self.tasks[task_id]
        self._save_tasks()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get task parsing statistics."""
        total_tasks = len(self.tasks)
        
        # Count by priority
        by_priority = {}
        for task in self.tasks.values():
            priority = task.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Count by category
        by_category = {}
        for task in self.tasks.values():
            category = task.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        return {
            'total_tasks': total_tasks,
            'by_priority': by_priority,
            'by_category': by_category
        }

    def export_tasks(self, export_path: str) -> Tuple[bool, str]:
        """Export parsed tasks to file."""
        try:
            export_data = {
                'tasks': {task_id: asdict(task) for task_id, task in self.tasks.items()},
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Tasks exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
