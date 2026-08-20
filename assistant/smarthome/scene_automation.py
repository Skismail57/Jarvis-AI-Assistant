"""
Scene Automation and Routines
Implements scene automation and routine management for smart home.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, time
from enum import Enum


class TriggerType(Enum):
    TIME = "time"
    DEVICE_STATE = "device_state"
    PRESENCE = "presence"
    MANUAL = "manual"
    VOICE = "voice"


class ActionType(Enum):
    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"
    SET_VALUE = "set_value"
    SET_COLOR = "set_color"
    SET_BRIGHTNESS = "set_brightness"
    SET_TEMPERATURE = "set_temperature"
    RUN_SCENE = "run_scene"
    SEND_NOTIFICATION = "send_notification"


@dataclass
class DeviceAction:
    action_id: str
    device_id: str
    action_type: ActionType
    parameters: Dict[str, Any]
    delay: float = 0.0


@dataclass
class SceneTrigger:
    trigger_id: str
    trigger_type: TriggerType
    conditions: Dict[str, Any]
    enabled: bool = True


@dataclass
class Scene:
    scene_id: str
    name: str
    description: str
    actions: List[DeviceAction]
    triggers: List[SceneTrigger]
    created_at: str
    is_active: bool = True
    last_executed: Optional[str] = None


class SceneAutomationManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.smarthome_dir = os.path.join(self.base_dir, "data", "smarthome")
        self.scenes_file = os.path.join(self.smarthome_dir, "scenes.json")
        self.routines_file = os.path.join(self.smarthome_dir, "routines.json")
        
        os.makedirs(self.smarthome_dir, exist_ok=True)
        
        # Load data
        self.scenes = self._load_scenes()
        self.routines = self._load_routines()

    def _load_scenes(self) -> Dict[str, Scene]:
        """Load scenes from disk."""
        if os.path.exists(self.scenes_file):
            try:
                with open(self.scenes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {scene_id: Scene(**scene) for scene_id, scene in data.items()}
            except Exception:
                pass
        return {}

    def _save_scenes(self):
        """Save scenes to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {scene_id: asdict(scene) for scene_id, scene in self.scenes.items()}
            with open(self.scenes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[SceneAutomation] Failed to save scenes: {e}")

    def _load_routines(self) -> Dict[str, Dict]:
        """Load routines from disk."""
        if os.path.exists(self.routines_file):
            try:
                with open(self.routines_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_routines(self):
        """Save routines to disk."""
        try:
            with open(self.routines_file, 'w', encoding='utf-8') as f:
                json.dump(self.routines, f, indent=2)
        except Exception as e:
            print(f"[SceneAutomation] Failed to save routines: {e}")

    def create_scene(self, name: str, description: str = "") -> Scene:
        """
        Create a new scene.
        
        Args:
            name: Scene name
            description: Scene description
            
        Returns:
            Scene
        """
        scene_id = f"scene_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        scene = Scene(
            scene_id=scene_id,
            name=name,
            description=description,
            actions=[],
            triggers=[],
            is_active=True,
            created_at=datetime.now().isoformat()
        )
        
        self.scenes[scene_id] = scene
        self._save_scenes()
        
        return scene

    def add_action_to_scene(self, scene_id: str, device_id: str, 
                           action_type: ActionType, parameters: Dict[str, Any],
                           delay: float = 0.0) -> DeviceAction:
        """
        Add an action to a scene.
        
        Args:
            scene_id: Scene ID
            device_id: Device ID
            action_type: Type of action
            parameters: Action parameters
            delay: Delay in seconds
            
        Returns:
            DeviceAction
        """
        if scene_id not in self.scenes:
            raise ValueError(f"Scene not found: {scene_id}")
        
        action_id = f"action_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        action = DeviceAction(
            action_id=action_id,
            device_id=device_id,
            action_type=action_type,
            parameters=parameters,
            delay=delay
        )
        
        self.scenes[scene_id].actions.append(action)
        self._save_scenes()
        
        return action

    def add_trigger_to_scene(self, scene_id: str, trigger_type: TriggerType,
                            conditions: Dict[str, Any]) -> SceneTrigger:
        """
        Add a trigger to a scene.
        
        Args:
            scene_id: Scene ID
            trigger_type: Type of trigger
            conditions: Trigger conditions
            
        Returns:
            SceneTrigger
        """
        if scene_id not in self.scenes:
            raise ValueError(f"Scene not found: {scene_id}")
        
        trigger_id = f"trigger_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        trigger = SceneTrigger(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            conditions=conditions,
            enabled=True
        )
        
        self.scenes[scene_id].triggers.append(trigger)
        self._save_scenes()
        
        return trigger

    def execute_scene(self, scene_id: str) -> Tuple[bool, str]:
        """
        Execute a scene.
        
        Args:
            scene_id: Scene ID
            
        Returns:
            (success, message)
        """
        if scene_id not in self.scenes:
            return False, "Scene not found"
        
        scene = self.scenes[scene_id]
        
        if not scene.is_active:
            return False, "Scene is not active"
        
        # Execute actions
        import asyncio
        
        async def execute_actions():
            for action in scene.actions:
                if action.delay > 0:
                    await asyncio.sleep(action.delay)
                
                # In production, execute actual device commands
                # For now, simulate
                print(f"Executing {action.action_type.value} on {action.device_id}")
        
        # Run async execution
        try:
            asyncio.run(execute_actions())
            
            scene.last_executed = datetime.now().isoformat()
            self._save_scenes()
            
            return True, f"Scene '{scene.name}' executed successfully"
        except Exception as e:
            return False, f"Scene execution failed: {str(e)}"

    def create_routine(self, name: str, scene_ids: List[str], 
                      schedule: Dict[str, Any] = None) -> str:
        """
        Create a routine (sequence of scenes).
        
        Args:
            name: Routine name
            scene_ids: List of scene IDs to execute in order
            schedule: Schedule information
            
        Returns:
            Routine ID
        """
        routine_id = f"routine_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.routines[routine_id] = {
            'routine_id': routine_id,
            'name': name,
            'scene_ids': scene_ids,
            'schedule': schedule or {},
            'created_at': datetime.now().isoformat()
        }
        
        self._save_routines()
        
        return routine_id

    def execute_routine(self, routine_id: str) -> Tuple[bool, str]:
        """
        Execute a routine.
        
        Args:
            routine_id: Routine ID
            
        Returns:
            (success, message)
        """
        if routine_id not in self.routines:
            return False, "Routine not found"
        
        routine = self.routines[routine_id]
        
        # Execute scenes in order
        results = []
        for scene_id in routine['scene_ids']:
            success, message = self.execute_scene(scene_id)
            results.append((success, message))
        
        failed = sum(1 for success, _ in results if not success)
        
        if failed == 0:
            return True, f"Routine '{routine['name']}' executed successfully"
        else:
            return False, f"Routine completed with {failed} failures"

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get a scene by ID."""
        return self.scenes.get(scene_id)

    def get_all_scenes(self) -> List[Scene]:
        """Get all scenes."""
        return list(self.scenes.values())

    def get_scenes_by_trigger(self, trigger_type: TriggerType) -> List[Scene]:
        """Get scenes with a specific trigger type."""
        return [scene for scene in self.scenes.values()
                if any(t.trigger_type == trigger_type for t in scene.triggers)]

    def activate_scene(self, scene_id: str) -> bool:
        """Activate a scene."""
        if scene_id not in self.scenes:
            return False
        
        self.scenes[scene_id].is_active = True
        self._save_scenes()
        return True

    def deactivate_scene(self, scene_id: str) -> bool:
        """Deactivate a scene."""
        if scene_id not in self.scenes:
            return False
        
        self.scenes[scene_id].is_active = False
        self._save_scenes()
        return True

    def delete_scene(self, scene_id: str) -> bool:
        """Delete a scene."""
        if scene_id not in self.scenes:
            return False
        
        del self.scenes[scene_id]
        self._save_scenes()
        return True

    def delete_routine(self, routine_id: str) -> bool:
        """Delete a routine."""
        if routine_id not in self.routines:
            return False
        
        del self.routines[routine_id]
        self._save_routines()
        return True

    def check_triggers(self) -> List[str]:
        """
        Check all scene triggers and return triggered scene IDs.
        
        Returns:
            List of scene IDs that should be executed
        """
        triggered_scenes = []
        
        for scene_id, scene in self.scenes.items():
            if not scene.is_active:
                continue
            
            for trigger in scene.triggers:
                if not trigger.enabled:
                    continue
                
                # Check if trigger conditions are met
                if self._evaluate_trigger(trigger):
                    triggered_scenes.append(scene_id)
        
        return triggered_scenes

    def _evaluate_trigger(self, trigger: SceneTrigger) -> bool:
        """Evaluate if a trigger condition is met."""
        # In production, this would check actual conditions
        # For now, return False (manual triggers only)
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get scene automation statistics."""
        total_scenes = len(self.scenes)
        total_routines = len(self.routines)
        
        active_scenes = sum(1 for s in self.scenes.values() if s.is_active)
        
        # Count by trigger type
        trigger_counts = {}
        for scene in self.scenes.values():
            for trigger in scene.triggers:
                ttype = trigger.trigger_type.value
                trigger_counts[ttype] = trigger_counts.get(ttype, 0) + 1
        
        return {
            'total_scenes': total_scenes,
            'active_scenes': active_scenes,
            'total_routines': total_routines,
            'trigger_counts': trigger_counts
        }

    def export_scenes(self, export_path: str) -> Tuple[bool, str]:
        """Export scenes to file."""
        try:
            export_data = {
                'scenes': {scene_id: asdict(scene) for scene_id, scene in self.scenes.items()},
                'routines': self.routines,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Scenes exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
