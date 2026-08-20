"""
GraphQL API and Webhooks
Provides GraphQL API for flexible queries and webhook support for event-driven integrations.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class WebhookEvent(Enum):
    USER_MESSAGE = "user_message"
    ASSISTANT_RESPONSE = "assistant_response"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    ERROR_OCCURRED = "error_occurred"
    CUSTOM = "custom"


class WebhookStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


@dataclass
class GraphQLSchema:
    schema_id: str
    name: str
    types: List[Dict[str, Any]]
    queries: List[Dict[str, Any]]
    mutations: List[Dict[str, Any]]
    subscriptions: List[Dict[str, Any]]
    created_at: str


@dataclass
class Webhook:
    webhook_id: str
    name: str
    event_type: WebhookEvent
    url: str
    secret: str
    status: WebhookStatus
    headers: Dict[str, str]
    retry_count: int
    last_triggered: Optional[str]
    created_at: str


class GraphQLWebhookManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.dev_dir = os.path.join(self.base_dir, "data", "developer")
        self.schemas_file = os.path.join(self.dev_dir, "graphql_schemas.json")
        self.webhooks_file = os.path.join(self.dev_dir, "webhooks.json")
        
        os.makedirs(self.dev_dir, exist_ok=True)
        
        # Load data
        self.schemas = self._load_schemas()
        self.webhooks = self._load_webhooks()

    def _load_schemas(self) -> Dict[str, GraphQLSchema]:
        """Load GraphQL schemas from disk."""
        if os.path.exists(self.schemas_file):
            try:
                with open(self.schemas_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {schema_id: GraphQLSchema(**schema) for schema_id, schema in data.items()}
            except Exception:
                pass
        return {}

    def _save_schemas(self):
        """Save GraphQL schemas to disk."""
        try:
            data = {schema_id: asdict(schema) for schema_id, schema in self.schemas.items()}
            with open(self.schemas_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[GraphQLWebhook] Failed to save schemas: {e}")

    def _load_webhooks(self) -> Dict[str, Webhook]:
        """Load webhooks from disk."""
        if os.path.exists(self.webhooks_file):
            try:
                with open(self.webhooks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {webhook_id: Webhook(**webhook) for webhook_id, webhook in data.items()}
            except Exception:
                pass
        return {}

    def _save_webhooks(self):
        """Save webhooks to disk."""
        try:
            data = {webhook_id: asdict(webhook) for webhook_id, webhook in self.webhooks.items()}
            with open(self.webhooks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[GraphQLWebhook] Failed to save webhooks: {e}")

    def create_schema(self, name: str) -> GraphQLSchema:
        """
        Create a GraphQL schema.
        
        Args:
            name: Schema name
            
        Returns:
            GraphQLSchema
        """
        schema_id = f"schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        schema = GraphQLSchema(
            schema_id=schema_id,
            name=name,
            types=[
                {
                    "name": "Query",
                    "fields": [
                        {"name": "user", "type": "User"},
                        {"name": "tasks", "type": "[Task]"},
                        {"name": "conversations", "type": "[Conversation]"}
                    ]
                },
                {
                    "name": "User",
                    "fields": [
                        {"name": "id", "type": "ID"},
                        {"name": "name", "type": "String"},
                        {"name": "preferences", "type": "Preferences"}
                    ]
                },
                {
                    "name": "Task",
                    "fields": [
                        {"name": "id", "type": "ID"},
                        {"name": "title", "type": "String"},
                        {"name": "status", "type": "String"},
                        {"name": "dueDate", "type": "String"}
                    ]
                }
            ],
            queries=[
                {
                    "name": "getUser",
                    "description": "Get user by ID",
                    "parameters": [{"name": "id", "type": "ID"}],
                    "returnType": "User"
                },
                {
                    "name": "getTasks",
                    "description": "Get all tasks",
                    "parameters": [],
                    "returnType": "[Task]"
                }
            ],
            mutations=[
                {
                    "name": "createTask",
                    "description": "Create a new task",
                    "parameters": [
                        {"name": "title", "type": "String"},
                        {"name": "description", "type": "String"}
                    ],
                    "returnType": "Task"
                },
                {
                    "name": "updateTask",
                    "description": "Update an existing task",
                    "parameters": [
                        {"name": "id", "type": "ID"},
                        {"name": "status", "type": "String"}
                    ],
                    "returnType": "Task"
                }
            ],
            subscriptions=[
                {
                    "name": "taskUpdated",
                    "description": "Subscribe to task updates",
                    "parameters": [{"name": "taskId", "type": "ID"}],
                    "returnType": "Task"
                }
            ],
            created_at=datetime.now().isoformat()
        )
        
        self.schemas[schema_id] = schema
        self._save_schemas()
        
        return schema

    def generate_schema_string(self, schema_id: str) -> Optional[str]:
        """Generate GraphQL schema string."""
        schema = self.schemas.get(schema_id)
        if not schema:
            return None
        
        schema_str = f"""
type {schema.types[1]['name']} {{
  {schema.types[1]['fields'][0]['name']}: {schema.types[1]['fields'][0]['type']}
  {schema.types[1]['fields'][1]['name']}: {schema.types[1]['fields'][1]['type']}
  {schema.types[1]['fields'][2]['name']}: {schema.types[1]['fields'][2]['type']}
}}

type {schema.types[2]['name']} {{
  {schema.types[2]['fields'][0]['name']}: {schema.types[2]['fields'][0]['type']}
  {schema.types[2]['fields'][1]['name']}: {schema.types[2]['fields'][1]['type']}
  {schema.types[2]['fields'][2]['name']}: {schema.types[2]['fields'][2]['type']}
  {schema.types[2]['fields'][3]['name']}: {schema.types[2]['fields'][3]['type']}
}}

type Query {{
  {schema.queries[0]['name']}(id: ID): {schema.queries[0]['returnType']}
  {schema.queries[1]['name']}: {schema.queries[1]['returnType']}
}}

type Mutation {{
  {schema.mutations[0]['name']}(title: String, description: String): {schema.mutations[0]['returnType']}
  {schema.mutations[1]['name']}(id: ID, status: String): {schema.mutations[1]['returnType']}
}}

type Subscription {{
  {schema.subscriptions[0]['name']}(taskId: ID): {schema.subscriptions[0]['returnType']}
}}
"""
        return schema_str

    def add_type(self, schema_id: str, type_def: Dict[str, Any]) -> bool:
        """Add a type to the schema."""
        if schema_id not in self.schemas:
            return False
        
        self.schemas[schema_id].types.append(type_def)
        self._save_schemas()
        
        return True

    def add_query(self, schema_id: str, query_def: Dict[str, Any]) -> bool:
        """Add a query to the schema."""
        if schema_id not in self.schemas:
            return False
        
        self.schemas[schema_id].queries.append(query_def)
        self._save_schemas()
        
        return True

    def add_mutation(self, schema_id: str, mutation_def: Dict[str, Any]) -> bool:
        """Add a mutation to the schema."""
        if schema_id not in self.schemas:
            return False
        
        self.schemas[schema_id].mutations.append(mutation_def)
        self._save_schemas()
        
        return True

    def create_webhook(self, name: str, event_type: WebhookEvent, url: str,
                     secret: str = None, headers: Dict[str, str] = None) -> Webhook:
        """
        Create a webhook.
        
        Args:
            name: Webhook name
            event_type: Event type
            url: Webhook URL
            secret: Webhook secret for verification
            headers: Custom headers
            
        Returns:
            Webhook
        """
        import secrets
        
        webhook_id = f"webhook_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not secret:
            secret = secrets.token_urlsafe(32)
        
        webhook = Webhook(
            webhook_id=webhook_id,
            name=name,
            event_type=event_type,
            url=url,
            secret=secret,
            status=WebhookStatus.ACTIVE,
            headers=headers or {},
            retry_count=0,
            last_triggered=None,
            created_at=datetime.now().isoformat()
        )
        
        self.webhooks[webhook_id] = webhook
        self._save_webhooks()
        
        return webhook

    def trigger_webhook(self, webhook_id: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Trigger a webhook.
        
        Args:
            webhook_id: Webhook ID
            payload: Payload to send
            
        Returns:
            (success, message)
        """
        if webhook_id not in self.webhooks:
            return False, "Webhook not found"
        
        webhook = self.webhooks[webhook_id]
        
        if webhook.status != WebhookStatus.ACTIVE:
            return False, f"Webhook is {webhook.status.value}"
        
        # In production, this would make an actual HTTP request
        # For now, simulate webhook trigger
        webhook.last_triggered = datetime.now().isoformat()
        webhook.retry_count += 1
        self._save_webhooks()
        
        return True, f"Webhook triggered: {webhook.url}"

    def trigger_event(self, event_type: WebhookEvent, payload: Dict[str, Any]) -> List[Tuple[bool, str]]:
        """
        Trigger all webhooks for an event type.
        
        Args:
            event_type: Event type
            payload: Payload to send
            
        Returns:
            List of (success, message) tuples
        """
        results = []
        
        for webhook in self.webhooks.values():
            if webhook.event_type == event_type and webhook.status == WebhookStatus.ACTIVE:
                success, message = self.trigger_webhook(webhook.webhook_id, payload)
                results.append((success, message))
        
        return results

    def deactivate_webhook(self, webhook_id: str) -> bool:
        """Deactivate a webhook."""
        if webhook_id not in self.webhooks:
            return False
        
        self.webhooks[webhook_id].status = WebhookStatus.INACTIVE
        self._save_webhooks()
        
        return True

    def activate_webhook(self, webhook_id: str) -> bool:
        """Activate a webhook."""
        if webhook_id not in self.webhooks:
            return False
        
        self.webhooks[webhook_id].status = WebhookStatus.ACTIVE
        self._save_webhooks()
        
        return True

    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a webhook by ID."""
        return self.webhooks.get(webhook_id)

    def get_webhooks_by_event(self, event_type: WebhookEvent) -> List[Webhook]:
        """Get all webhooks for an event type."""
        return [w for w in self.webhooks.values() if w.event_type == event_type]

    def get_schema(self, schema_id: str) -> Optional[GraphQLSchema]:
        """Get a GraphQL schema by ID."""
        return self.schemas.get(schema_id)

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        if webhook_id not in self.webhooks:
            return False
        
        del self.webhooks[webhook_id]
        self._save_webhooks()
        
        return True

    def delete_schema(self, schema_id: str) -> bool:
        """Delete a GraphQL schema."""
        if schema_id not in self.schemas:
            return False
        
        del self.schemas[schema_id]
        self._save_schemas()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get GraphQL and webhook statistics."""
        total_schemas = len(self.schemas)
        total_webhooks = len(self.webhooks)
        
        # Count by webhook event type
        by_event_type = {}
        for webhook in self.webhooks.values():
            event = webhook.event_type.value
            by_event_type[event] = by_event_type.get(event, 0) + 1
        
        # Count by webhook status
        by_status = {}
        for webhook in self.webhooks.values():
            status = webhook.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_schemas': total_schemas,
            'total_webhooks': total_webhooks,
            'by_event_type': by_event_type,
            'by_status': by_status
        }

    def export_schema(self, schema_id: str, export_path: str) -> Tuple[bool, str]:
        """Export GraphQL schema to file."""
        schema = self.get_schema(schema_id)
        if not schema:
            return False, "Schema not found"
        
        try:
            schema_str = self.generate_schema_string(schema_id)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(schema_str)
            return True, f"Schema exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
