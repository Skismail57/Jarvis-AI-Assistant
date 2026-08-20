"""
Workflow Automation Triggers
Provides workflow automation capabilities with triggers and actions.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


class TriggerType(Enum):
    TIME = "time"
    EVENT = "event"
    CONDITION = "condition"
    WEBHOOK = "webhook"
    MANUAL = "manual"


class ActionType(Enum):
    SEND_NOTIFICATION = "send_notification"
    CREATE_TASK = "create_task"
    UPDATE_STATUS = "update_status"
    SEND_EMAIL = "send_email"
    CALL_API = "call_api"
    EXECUTE_SCRIPT = "execute_script"
    TRIGGER_SCENE = "trigger_scene"


class TriggerStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class AutomationTrigger:
    trigger_id: str
    trigger_type: TriggerType
    conditions: Dict[str, Any]
    status: TriggerStatus
    created_at: str
    last_triggered: Optional[str] = None
    trigger_count: int = 0


@dataclass
class AutomationAction:
    action_id: str
    action_type: ActionType
    parameters: Dict[str, Any]
    delay: float = 0.0


@dataclass
class Workflow:
    workflow_id: str
    name: str
    description: str
    triggers: List[AutomationTrigger]
    actions: List[AutomationAction]
    is_active: bool
    created_at: str
    last_executed: Optional[str] = None
    execution_count: int = 0


class WorkflowAutomationManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.productivity_dir = os.path.join(self.base_dir, "data", "productivity")
        self.workflows_file = os.path.join(self.productivity_dir, "workflows.json")
        self.execution_log_file = os.path.join(self.productivity_dir, "workflow_executions.json")
        
        os.makedirs(self.productivity_dir, exist_ok=True)
        
        # Load data
        self.workflows = self._load_workflows()
        self.execution_log = self._load_execution_log()
        
        # Action handlers
        self.action_handlers = {
            ActionType.SEND_NOTIFICATION: self._send_notification,
            ActionType.CREATE_TASK: self._create_task,
            ActionType.UPDATE_STATUS: self._update_status,
            ActionType.SEND_EMAIL: self._send_email,
            ActionType.CALL_API: self._call_api,
            ActionType.EXECUTE_SCRIPT: self._execute_script,
            ActionType.TRIGGER_SCENE: self._trigger_scene
        }

    def _load_workflows(self) -> Dict[str, Workflow]:
        """Load workflows from disk."""
        if os.path.exists(self.workflows_file):
            try:
                with open(self.workflows_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {workflow_id: Workflow(**workflow) for workflow_id, workflow in data.items()}
            except Exception:
                pass
        return {}

    def _save_workflows(self):
        """Save workflows to disk."""
        try:
            data = {workflow_id: asdict(workflow) for workflow_id, workflow in self.workflows.items()}
            with open(self.workflows_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WorkflowAutomation] Failed to save workflows: {e}")

    def _load_execution_log(self) -> Dict[str, Dict]:
        """Load execution log from disk."""
        if os.path.exists(self.execution_log_file):
            try:
                with open(self.execution_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_execution_log(self):
        """Save execution log to disk."""
        try:
            with open(self.execution_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.execution_log, f, indent=2)
        except Exception as e:
            print(f"[WorkflowAutomation] Failed to save execution log: {e}")

    def create_workflow(self, name: str, description: str = "") -> Workflow:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            description: Workflow description
            
        Returns:
            Workflow
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            triggers=[],
            actions=[],
            is_active=True,
            created_at=datetime.now().isoformat()
        )
        
        self.workflows[workflow_id] = workflow
        self._save_workflows()
        
        return workflow

    def add_trigger(self, workflow_id: str, trigger_type: TriggerType,
                   conditions: Dict[str, Any]) -> AutomationTrigger:
        """
        Add a trigger to a workflow.
        
        Args:
            workflow_id: Workflow ID
            trigger_type: Type of trigger
            conditions: Trigger conditions
            
        Returns:
            AutomationTrigger
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        trigger_id = f"trigger_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        trigger = AutomationTrigger(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            conditions=conditions,
            status=TriggerStatus.ACTIVE,
            created_at=datetime.now().isoformat()
        )
        
        self.workflows[workflow_id].triggers.append(trigger)
        self._save_workflows()
        
        return trigger

    def add_action(self, workflow_id: str, action_type: ActionType,
                  parameters: Dict[str, Any], delay: float = 0.0) -> AutomationAction:
        """
        Add an action to a workflow.
        
        Args:
            workflow_id: Workflow ID
            action_type: Type of action
            parameters: Action parameters
            delay: Delay in seconds
            
        Returns:
            AutomationAction
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        action_id = f"action_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        action = AutomationAction(
            action_id=action_id,
            action_type=action_type,
            parameters=parameters,
            delay=delay
        )
        
        self.workflows[workflow_id].actions.append(action)
        self._save_workflows()
        
        return action

    def execute_workflow(self, workflow_id: str) -> Tuple[bool, str]:
        """
        Execute a workflow manually.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            (success, message)
        """
        if workflow_id not in self.workflows:
            return False, "Workflow not found"
        
        workflow = self.workflows[workflow_id]
        
        if not workflow.is_active:
            return False, "Workflow is not active"
        
        # Execute actions
        import asyncio
        
        async def execute_actions():
            results = []
            for action in workflow.actions:
                if action.delay > 0:
                    await asyncio.sleep(action.delay)
                
                handler = self.action_handlers.get(action.action_type)
                if handler:
                    result = handler(action.parameters)
                    results.append(result)
            
            return results
        
        try:
            asyncio.run(execute_actions())
            
            workflow.last_executed = datetime.now().isoformat()
            workflow.execution_count += 1
            self._save_workflows()
            
            # Log execution
            self._log_execution(workflow_id, True, "Manual execution")
            
            return True, f"Workflow '{workflow.name}' executed successfully"
        except Exception as e:
            self._log_execution(workflow_id, False, str(e))
            return False, f"Workflow execution failed: {str(e)}"

    def check_triggers(self) -> List[str]:
        """
        Check all workflow triggers and return triggered workflow IDs.
        
        Returns:
            List of workflow IDs that should be executed
        """
        triggered_workflows = []
        
        for workflow_id, workflow in self.workflows.items():
            if not workflow.is_active:
                continue
            
            for trigger in workflow.triggers:
                if trigger.status != TriggerStatus.ACTIVE:
                    continue
                
                if self._evaluate_trigger(trigger):
                    triggered_workflows.append(workflow_id)
                    
                    # Update trigger
                    trigger.last_triggered = datetime.now().isoformat()
                    trigger.trigger_count += 1
        
        if triggered_workflows:
            self._save_workflows()
        
        return triggered_workflows

    def _evaluate_trigger(self, trigger: AutomationTrigger) -> bool:
        """Evaluate if a trigger condition is met."""
        # Time-based trigger
        if trigger.trigger_type == TriggerType.TIME:
            if 'time' in trigger.conditions:
                trigger_time = trigger.conditions['time']
                current_time = datetime.now().strftime('%H:%M')
                return current_time == trigger_time
        
        # Event-based trigger (placeholder)
        elif trigger.trigger_type == TriggerType.EVENT:
            return False
        
        # Condition-based trigger
        elif trigger.trigger_type == TriggerType.CONDITION:
            # In production, evaluate actual conditions
            return False
        
        return False

    def _log_execution(self, workflow_id: str, success: bool, message: str):
        """Log workflow execution."""
        log_entry = {
            'workflow_id': workflow_id,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        log_id = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.execution_log[log_id] = log_entry
        self._save_execution_log()

    # Action handlers
    def _send_notification(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Send notification action."""
        # In production, send actual notification
        return True, f"Notification sent: {parameters.get('message', '')}"

    def _create_task(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Create task action."""
        # In production, create actual task
        return True, f"Task created: {parameters.get('title', '')}"

    def _update_status(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Update status action."""
        # In production, update actual status
        return True, f"Status updated: {parameters.get('status', '')}"

    def _send_email(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Send email action."""
        # In production, send actual email
        return True, f"Email sent to {parameters.get('to', '')}"

    def _call_api(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Call API action."""
        # In production, make actual API call
        return True, f"API called: {parameters.get('url', '')}"

    def _execute_script(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute script action."""
        # In production, execute actual script
        return True, f"Script executed: {parameters.get('script', '')}"

    def _trigger_scene(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Trigger smart home scene action."""
        # In production, trigger actual scene
        return True, f"Scene triggered: {parameters.get('scene_id', '')}"

    def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow."""
        if workflow_id not in self.workflows:
            return False
        
        self.workflows[workflow_id].is_active = True
        self._save_workflows()
        return True

    def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow."""
        if workflow_id not in self.workflows:
            return False
        
        self.workflows[workflow_id].is_active = False
        self._save_workflows()
        return True

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def get_all_workflows(self) -> List[Workflow]:
        """Get all workflows."""
        return list(self.workflows.values())

    def get_active_workflows(self) -> List[Workflow]:
        """Get all active workflows."""
        return [w for w in self.workflows.values() if w.is_active]

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id not in self.workflows:
            return False
        
        del self.workflows[workflow_id]
        self._save_workflows()
        return True

    def get_execution_log(self, workflow_id: str = None, limit: int = 100) -> List[Dict]:
        """Get execution log, optionally filtered by workflow."""
        logs = list(self.execution_log.values())
        
        if workflow_id:
            logs = [log for log in logs if log['workflow_id'] == workflow_id]
        
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return logs[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get workflow automation statistics."""
        total_workflows = len(self.workflows)
        active_workflows = len(self.get_active_workflows())
        
        # Count by trigger type
        trigger_counts = {}
        for workflow in self.workflows.values():
            for trigger in workflow.triggers:
                ttype = trigger.trigger_type.value
                trigger_counts[ttype] = trigger_counts.get(ttype, 0) + 1
        
        # Count by action type
        action_counts = {}
        for workflow in self.workflows.values():
            for action in workflow.actions:
                atype = action.action_type.value
                action_counts[atype] = action_counts.get(atype, 0) + 1
        
        return {
            'total_workflows': total_workflows,
            'active_workflows': active_workflows,
            'trigger_counts': trigger_counts,
            'action_counts': action_counts
        }

    def export_workflows(self, export_path: str) -> Tuple[bool, str]:
        """Export workflows to file."""
        try:
            export_data = {
                'workflows': {workflow_id: asdict(workflow) for workflow_id, workflow in self.workflows.items()},
                'execution_log': self.execution_log,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Workflows exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
