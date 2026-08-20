"""
Hierarchical Task Decomposition Planner
Implements multi-step planning with hierarchical task decomposition for complex queries.
"""

import os
import json
import re
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import heapq


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    id: str
    description: str
    task_type: str  # 'information', 'action', 'computation', 'communication'
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    estimated_duration: int = 60  # seconds
    required_tools: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class Plan:
    id: str
    goal: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    root_tasks: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_order: List[str] = field(default_factory=list)
    progress: float = 0.0


@dataclass
class PlanningContext:
    user_query: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    available_tools: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    time_limit: Optional[int] = None


class HierarchicalPlanner:
    def __init__(self, assistant_ref=None):
        self.assistant = assistant_ref
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.plans_dir = os.path.join(self.base_dir, "data", "plans")
        os.makedirs(self.plans_dir, exist_ok=True)
        
        # Task templates for common patterns
        self.task_templates = self._initialize_task_templates()
        
        # Hierarchical decomposition rules
        self.decomposition_rules = self._initialize_decomposition_rules()

    def _initialize_task_templates(self) -> Dict[str, Dict]:
        """Initialize templates for common task types."""
        return {
            'web_research': {
                'task_type': 'information',
                'estimated_duration': 30,
                'required_tools': ['web_search', 'content_extraction'],
                'subtasks': ['search_query', 'extract_content', 'synthesize_results']
            },
            'data_analysis': {
                'task_type': 'computation',
                'estimated_duration': 45,
                'required_tools': ['calculator', 'data_processing'],
                'subtasks': ['collect_data', 'process_data', 'analyze_results', 'generate_report']
            },
            'communication': {
                'task_type': 'communication',
                'estimated_duration': 60,
                'required_tools': ['email', 'messaging'],
                'subtasks': ['draft_message', 'review_content', 'send_message']
            },
            'system_control': {
                'task_type': 'action',
                'estimated_duration': 20,
                'required_tools': ['pc_controller'],
                'subtasks': ['verify_permission', 'execute_action', 'confirm_result']
            },
            'information_retrieval': {
                'task_type': 'information',
                'estimated_duration': 15,
                'required_tools': ['data_provider', 'memory'],
                'subtasks': ['query_source', 'format_response']
            }
        }

    def _initialize_decomposition_rules(self) -> Dict[str, List[str]]:
        """Initialize rules for decomposing complex queries."""
        return {
            'research_project': [
                'define_scope',
                'gather_information',
                'analyze_data',
                'synthesize_findings',
                'create_report'
            ],
            'multi_step_action': [
                'plan_sequence',
                'execute_steps',
                'verify_results',
                'handle_errors'
            ],
            'complex_query': [
                'parse_query',
                'identify_components',
                'resolve_dependencies',
                'execute_components',
                'combine_results'
            ],
            'decision_making': [
                'gather_options',
                'evaluate_criteria',
                'compare_alternatives',
                'recommend_solution'
            ]
        }

    def create_plan(self, context: PlanningContext) -> Plan:
        """
        Create a hierarchical plan for the given context.
        
        Args:
            context: Planning context with user query and constraints
            
        Returns:
            Executable plan with hierarchical task decomposition
        """
        query = context.user_query.lower()
        
        # Analyze query complexity
        complexity = self._analyze_query_complexity(query)
        
        # Generate plan ID
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        plan = Plan(
            id=plan_id,
            goal=context.user_query,
            status=TaskStatus.PENDING
        )
        
        # Decompose query into tasks based on complexity
        if complexity == 'simple':
            tasks = self._decompose_simple_query(query, context)
        elif complexity == 'moderate':
            tasks = self._decompose_moderate_query(query, context)
        elif complexity == 'complex':
            tasks = self._decompose_complex_query(query, context)
        else:  # very complex
            tasks = self._decompose_very_complex_query(query, context)
        
        # Add tasks to plan
        for task in tasks:
            plan.tasks[task.id] = task
            if not task.dependencies:
                plan.root_tasks.append(task.id)
        
        # Calculate execution order
        plan.execution_order = self._calculate_execution_order(plan)
        
        # Save plan
        self._save_plan(plan)
        
        return plan

    def _analyze_query_complexity(self, query: str) -> str:
        """Analyze the complexity of a user query."""
        complexity_score = 0
        
        # Check for multiple intents
        if re.search(r'\b(and|then|after|before|while)\b', query):
            complexity_score += 2
        
        # Check for conditional logic
        if re.search(r'\b(if|when|unless|in case)\b', query):
            complexity_score += 2
        
        # Check for temporal sequences
        if re.search(r'\b(first|then|next|finally|last)\b', query):
            complexity_score += 1
        
        # Check for multiple information sources
        info_sources = ['search', 'find', 'look up', 'check', 'get', 'retrieve']
        source_count = sum(1 for source in info_sources if source in query)
        if source_count > 1:
            complexity_score += source_count
        
        # Check for complex actions
        complex_actions = ['compare', 'analyze', 'evaluate', 'synthesize', 'integrate']
        if any(action in query for action in complex_actions):
            complexity_score += 2
        
        # Check for calculations
        if re.search(r'[\d+\-*/().\^]', query):
            complexity_score += 1
        
        # Determine complexity level
        if complexity_score <= 1:
            return 'simple'
        elif complexity_score <= 3:
            return 'moderate'
        elif complexity_score <= 5:
            return 'complex'
        else:
            return 'very_complex'

    def _decompose_simple_query(self, query: str, context: PlanningContext) -> List[Task]:
        """Decompose a simple query into a single task."""
        task = Task(
            id=f"task_001",
            description=query,
            task_type=self._identify_task_type(query),
            priority=TaskPriority.HIGH,
            estimated_duration=30,
            required_tools=self._identify_required_tools(query)
        )
        return [task]

    def _decompose_moderate_query(self, query: str, context: PlanningContext) -> List[Task]:
        """Decompose a moderate query into 2-3 sequential tasks."""
        tasks = []
        
        # Identify main components
        if 'search' in query and 'then' in query:
            # Search then action pattern
            search_task = Task(
                id="task_001",
                description=f"Search for information: {query}",
                task_type="information",
                priority=TaskPriority.HIGH,
                estimated_duration=30,
                required_tools=['web_search']
            )
            
            action_task = Task(
                id="task_002",
                description="Perform action based on search results",
                task_type="action",
                priority=TaskPriority.HIGH,
                dependencies=["task_001"],
                estimated_duration=20,
                required_tools=['pc_controller']
            )
            
            tasks = [search_task, action_task]
            
        elif 'compare' in query:
            # Comparison pattern
            items = self._extract_comparison_items(query)
            
            for i, item in enumerate(items):
                task = Task(
                    id=f"task_{i+1:03d}",
                    description=f"Get information about: {item}",
                    task_type="information",
                    priority=TaskPriority.HIGH,
                    estimated_duration=20,
                    required_tools=['web_search', 'data_provider']
                )
                tasks.append(task)
            
            comparison_task = Task(
                id=f"task_{len(items)+1:03d}",
                description="Compare the gathered information",
                task_type="computation",
                priority=TaskPriority.HIGH,
                dependencies=[f"task_{i+1:03d}" for i in range(len(items))],
                estimated_duration=30,
                required_tools=['llm']
            )
            tasks.append(comparison_task)
            
        else:
            # Generic moderate decomposition
            info_task = Task(
                id="task_001",
                description="Gather required information",
                task_type="information",
                priority=TaskPriority.HIGH,
                estimated_duration=30,
                required_tools=['web_search', 'data_provider']
            )
            
            process_task = Task(
                id="task_002",
                description="Process the information",
                task_type="computation",
                priority=TaskPriority.HIGH,
                dependencies=["task_001"],
                estimated_duration=20,
                required_tools=['llm', 'calculator']
            )
            
            tasks = [info_task, process_task]
        
        return tasks

    def _decompose_complex_query(self, query: str, context: PlanningContext) -> List[Task]:
        """Decompose a complex query using hierarchical decomposition."""
        tasks = []
        
        # Identify the decomposition pattern
        pattern = self._identify_decomposition_pattern(query)
        
        if pattern == 'research_project':
            tasks = self._create_research_project_tasks(query, context)
        elif pattern == 'multi_step_action':
            tasks = self._create_multi_step_action_tasks(query, context)
        elif pattern == 'complex_query':
            tasks = self._create_complex_query_tasks(query, context)
        elif pattern == 'decision_making':
            tasks = self._create_decision_making_tasks(query, context)
        else:
            # Generic complex decomposition
            tasks = self._create_generic_complex_tasks(query, context)
        
        return tasks

    def _decompose_very_complex_query(self, query: str, context: PlanningContext) -> List[Task]:
        """Decompose a very complex query with full hierarchical planning."""
        # Break down into major phases
        phases = self._identify_query_phases(query)
        
        all_tasks = []
        task_counter = 1
        
        for phase in phases:
            phase_tasks = self._create_phase_tasks(phase, context, task_counter)
            all_tasks.extend(phase_tasks)
            task_counter += len(phase_tasks)
        
        # Add coordination task
        coordination_task = Task(
            id=f"task_{task_counter:03d}",
            description="Coordinate and synthesize results from all phases",
            task_type="computation",
            priority=TaskPriority.CRITICAL,
            dependencies=[task.id for task in all_tasks],
            estimated_duration=60,
            required_tools=['llm']
        )
        all_tasks.append(coordination_task)
        
        return all_tasks

    def _identify_task_type(self, query: str) -> str:
        """Identify the primary task type from query."""
        query_lower = query.lower()
        
        action_keywords = ['open', 'close', 'start', 'stop', 'create', 'delete', 'send', 'run']
        info_keywords = ['what', 'how', 'why', 'when', 'where', 'who', 'find', 'search', 'get']
        calc_keywords = ['calculate', 'compute', 'add', 'subtract', 'multiply', 'divide']
        
        if any(kw in query_lower for kw in action_keywords):
            return 'action'
        elif any(kw in query_lower for kw in calc_keywords):
            return 'computation'
        elif any(kw in query_lower for kw in info_keywords):
            return 'information'
        else:
            return 'communication'

    def _identify_required_tools(self, query: str) -> List[str]:
        """Identify required tools for a query."""
        tools = []
        query_lower = query.lower()
        
        tool_mapping = {
            'search': ['web_search'],
            'weather': ['weather_api'],
            'time': ['time_api'],
            'calculate': ['calculator'],
            'email': ['email'],
            'calendar': ['calendar'],
            'file': ['file_system'],
            'app': ['pc_controller'],
            'music': ['music_controller'],
            'smart home': ['home_assistant']
        }
        
        for keyword, tool_list in tool_mapping.items():
            if keyword in query_lower:
                tools.extend(tool_list)
        
        return list(set(tools))  # Remove duplicates

    def _extract_comparison_items(self, query: str) -> List[str]:
        """Extract items to be compared from query."""
        # Simple extraction - would be more sophisticated in production
        items = re.findall(r'compare\s+(.+?)\s+(?:and|with|to)\s+(.+)', query, re.IGNORECASE)
        if items:
            return list(items[0])
        return []

    def _identify_decomposition_pattern(self, query: str) -> str:
        """Identify the decomposition pattern for a query."""
        query_lower = query.lower()
        
        research_keywords = ['research', 'study', 'investigate', 'analyze in depth']
        action_sequence_keywords = ['then', 'after that', 'next', 'finally', 'sequence']
        decision_keywords = ['decide', 'choose', 'select', 'recommend', 'best option']
        
        if any(kw in query_lower for kw in research_keywords):
            return 'research_project'
        elif any(kw in query_lower for kw in action_sequence_keywords):
            return 'multi_step_action'
        elif any(kw in query_lower for kw in decision_keywords):
            return 'decision_making'
        else:
            return 'complex_query'

    def _create_research_project_tasks(self, query: str, context: PlanningContext) -> List[Task]:
        """Create tasks for a research project pattern."""
        tasks = []
        
        # Define scope
        scope_task = Task(
            id="task_001",
            description="Define research scope and objectives",
            task_type="information",
            priority=TaskPriority.HIGH,
            estimated_duration=15,
            required_tools=['llm']
        )
        tasks.append(scope_task)
        
        # Gather information
        gather_task = Task(
            id="task_002",
            description="Gather information from multiple sources",
            task_type="information",
            priority=TaskPriority.HIGH,
            dependencies=["task_001"],
            estimated_duration=60,
            required_tools=['web_search', 'data_provider']
        )
        tasks.append(gather_task)
        
        # Analyze data
        analyze_task = Task(
            id="task_003",
            description="Analyze and synthesize gathered data",
            task_type="computation",
            priority=TaskPriority.HIGH,
            dependencies=["task_002"],
            estimated_duration=45,
            required_tools=['llm']
        )
        tasks.append(analyze_task)
        
        # Create report
        report_task = Task(
            id="task_004",
            description="Create comprehensive report with findings",
            task_type="communication",
            priority=TaskPriority.HIGH,
            dependencies=["task_003"],
            estimated_duration=30,
            required_tools=['llm']
        )
        tasks.append(report_task)
        
        return tasks

    def _create_multi_step_action_tasks(self, query: str, context: PlanningContext) -> List[Task]:
        """Create tasks for a multi-step action pattern."""
        tasks = []
        
        # Plan sequence
        plan_task = Task(
            id="task_001",
            description="Plan the sequence of actions",
            task_type="information",
            priority=TaskPriority.CRITICAL,
            estimated_duration=20,
            required_tools=['llm']
        )
        tasks.append(plan_task)
        
        # Extract steps from query
        steps = self._extract_action_steps(query)
        
        for i, step in enumerate(steps):
            step_task = Task(
                id=f"task_{i+2:03d}",
                description=f"Execute step: {step}",
                task_type="action",
                priority=TaskPriority.HIGH,
                dependencies=["task_001"] + ([f"task_{i+1:03d}"] if i > 0 else []),
                estimated_duration=30,
                required_tools=['pc_controller']
            )
            tasks.append(step_task)
        
        # Verify results
        verify_task = Task(
            id=f"task_{len(steps)+2:03d}",
            description="Verify all actions completed successfully",
            task_type="information",
            priority=TaskPriority.HIGH,
            dependencies=[f"task_{i+2:03d}" for i in range(len(steps))],
            estimated_duration=15,
            required_tools=['pc_controller']
        )
        tasks.append(verify_task)
        
        return tasks

    def _create_complex_query_tasks(self, query: str, context: PlanningContext) -> List[Task]:
        """Create tasks for a complex query pattern."""
        tasks = []
        
        # Parse query
        parse_task = Task(
            id="task_001",
            description="Parse and understand the complex query",
            task_type="information",
            priority=TaskPriority.CRITICAL,
            estimated_duration=15,
            required_tools=['llm']
        )
        tasks.append(parse_task)
        
        # Identify components
        identify_task = Task(
            id="task_002",
            description="Identify query components and dependencies",
            task_type="information",
            priority=TaskPriority.HIGH,
            dependencies=["task_001"],
            estimated_duration=20,
            required_tools=['llm']
        )
        tasks.append(identify_task)
        
        # Resolve dependencies
        resolve_task = Task(
            id="task_003",
            description="Resolve dependencies between components",
            task_type="computation",
            priority=TaskPriority.HIGH,
            dependencies=["task_002"],
            estimated_duration=15,
            required_tools=['llm']
        )
        tasks.append(resolve_task)
        
        # Execute components
        execute_task = Task(
            id="task_004",
            description="Execute query components in dependency order",
            task_type="computation",
            priority=TaskPriority.HIGH,
            dependencies=["task_003"],
            estimated_duration=60,
            required_tools=['web_search', 'data_provider', 'calculator']
        )
        tasks.append(execute_task)
        
        # Combine results
        combine_task = Task(
            id="task_005",
            description="Combine and synthesize component results",
            task_type="computation",
            priority=TaskPriority.HIGH,
            dependencies=["task_004"],
            estimated_duration=30,
            required_tools=['llm']
        )
        tasks.append(combine_task)
        
        return tasks

    def _create_decision_making_tasks(self, query: str, context: PlanningContext) -> List[Task]:
        """Create tasks for a decision-making pattern."""
        tasks = []
        
        # Gather options
        options_task = Task(
            id="task_001",
            description="Gather available options",
            task_type="information",
            priority=TaskPriority.HIGH,
            estimated_duration=30,
            required_tools=['web_search', 'data_provider']
        )
        tasks.append(options_task)
        
        # Evaluate criteria
        criteria_task = Task(
            id="task_002",
            description="Define evaluation criteria",
            task_type="information",
            priority=TaskPriority.HIGH,
            dependencies=["task_001"],
            estimated_duration=20,
            required_tools=['llm']
        )
        tasks.append(criteria_task)
        
        # Compare alternatives
        compare_task = Task(
            id="task_003",
            description="Compare alternatives against criteria",
            task_type="computation",
            priority=TaskPriority.HIGH,
            dependencies=["task_002"],
            estimated_duration=45,
            required_tools=['llm', 'calculator']
        )
        tasks.append(compare_task)
        
        # Recommend solution
        recommend_task = Task(
            id="task_004",
            description="Recommend optimal solution with reasoning",
            task_type="communication",
            priority=TaskPriority.HIGH,
            dependencies=["task_003"],
            estimated_duration=30,
            required_tools=['llm']
        )
        tasks.append(recommend_task)
        
        return tasks

    def _create_generic_complex_tasks(self, query: str, context: PlanningContext) -> List[Task]:
        """Create generic complex tasks."""
        tasks = []
        
        # Information gathering
        info_task = Task(
            id="task_001",
            description="Gather comprehensive information",
            task_type="information",
            priority=TaskPriority.HIGH,
            estimated_duration=45,
            required_tools=['web_search', 'data_provider', 'memory']
        )
        tasks.append(info_task)
        
        # Processing
        process_task = Task(
            id="task_002",
            description="Process and analyze information",
            task_type="computation",
            priority=TaskPriority.HIGH,
            dependencies=["task_001"],
            estimated_duration=30,
            required_tools=['llm', 'calculator']
        )
        tasks.append(process_task)
        
        # Action if needed
        if self._identify_task_type(query) == 'action':
            action_task = Task(
                id="task_003",
                description="Execute required actions",
                task_type="action",
                priority=TaskPriority.HIGH,
                dependencies=["task_002"],
                estimated_duration=30,
                required_tools=['pc_controller']
            )
            tasks.append(action_task)
            
            # Response task
            response_task = Task(
                id="task_004",
                description="Provide response and confirmation",
                task_type="communication",
                priority=TaskPriority.HIGH,
                dependencies=["task_003"],
                estimated_duration=15,
                required_tools=['tts']
            )
            tasks.append(response_task)
        else:
            # Response task
            response_task = Task(
                id="task_003",
                description="Provide comprehensive response",
                task_type="communication",
                priority=TaskPriority.HIGH,
                dependencies=["task_002"],
                estimated_duration=20,
                required_tools=['tts']
            )
            tasks.append(response_task)
        
        return tasks

    def _identify_query_phases(self, query: str) -> List[str]:
        """Identify major phases in a very complex query."""
        # Simple phase identification based on conjunctions
        phases = re.split(r'\b(and|then|after|before|while)\b+', query, flags=re.IGNORECASE)
        return [phase.strip() for phase in phases if phase.strip()]

    def _create_phase_tasks(self, phase: str, context: PlanningContext, 
                          start_counter: int) -> List[Task]:
        """Create tasks for a specific phase."""
        # Treat each phase as a moderate query
        return self._decompose_moderate_query(phase, context)

    def _extract_action_steps(self, query: str) -> List[str]:
        """Extract action steps from a multi-step action query."""
        # Simple extraction based on common patterns
        steps = re.split(r'\b(then|next|after that|finally)\b+', query, flags=re.IGNORECASE)
        return [step.strip() for step in steps if step.strip()]

    def _calculate_execution_order(self, plan: Plan) -> List[str]:
        """Calculate optimal execution order using topological sort."""
        # Build dependency graph
        graph = {task_id: [] for task_id in plan.tasks}
        in_degree = {task_id: 0 for task_id in plan.tasks}
        
        for task_id, task in plan.tasks.items():
            for dep_id in task.dependencies:
                if dep_id in graph:
                    graph[dep_id].append(task_id)
                    in_degree[task_id] += 1
        
        # Topological sort using Kahn's algorithm
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            # Sort by priority
            queue.sort(key=lambda x: self._priority_value(plan.tasks[x].priority))
            current = queue.pop(0)
            execution_order.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return execution_order

    def _priority_value(self, priority: TaskPriority) -> int:
        """Convert priority to numeric value for sorting."""
        priority_map = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        return priority_map.get(priority, 2)

    def execute_plan(self, plan: Plan, context: PlanningContext) -> Dict[str, Any]:
        """
        Execute a plan with hierarchical task decomposition.
        
        Args:
            plan: The plan to execute
            context: Execution context
            
        Returns:
            Execution results with task outcomes
        """
        plan.status = TaskStatus.IN_PROGRESS
        self._save_plan(plan)
        
        results = {
            'plan_id': plan.id,
            'goal': plan.goal,
            'tasks_executed': 0,
            'tasks_failed': 0,
            'total_tasks': len(plan.tasks),
            'results': {},
            'final_answer': None
        }
        
        # Execute tasks in dependency order
        for task_id in plan.execution_order:
            task = plan.tasks[task_id]
            
            # Check if dependencies are satisfied
            if not self._check_dependencies(task, plan):
                task.status = TaskStatus.SKIPPED
                task.error = "Dependencies not satisfied"
                continue
            
            # Execute task
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now().isoformat()
            self._save_plan(plan)
            
            try:
                result = self._execute_task(task, context)
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                results['tasks_executed'] += 1
                results['results'][task_id] = result
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now().isoformat()
                results['tasks_failed'] += 1
                results['results'][task_id] = {'error': str(e)}
            
            self._save_plan(plan)
            
            # Update progress
            plan.progress = results['tasks_executed'] / results['total_tasks']
        
        # Determine final answer
        if results['tasks_failed'] == 0:
            plan.status = TaskStatus.COMPLETED
            results['final_answer'] = self._synthesize_final_answer(plan, results)
        else:
            plan.status = TaskStatus.FAILED
            results['final_answer'] = f"Plan execution failed with {results['tasks_failed']} errors"
        
        plan.completed_at = datetime.now().isoformat()
        self._save_plan(plan)
        
        return results

    def _check_dependencies(self, task: Task, plan: Plan) -> bool:
        """Check if task dependencies are satisfied."""
        for dep_id in task.dependencies:
            dep_task = plan.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def _execute_task(self, task: Task, context: PlanningContext) -> Any:
        """Execute a single task."""
        # This would delegate to appropriate tools based on task type
        # For now, return a placeholder result
        return {
            'task_id': task.id,
            'description': task.description,
            'status': 'completed',
            'result': f"Executed: {task.description}"
        }

    def _synthesize_final_answer(self, plan: Plan, results: Dict) -> str:
        """Synthesize final answer from task results."""
        # Combine results from all tasks
        if self.assistant and self.assistant.llm:
            context = "\n".join([
                f"Task {task_id}: {plan.tasks[task_id].description} -> {results['results'].get(task_id, 'No result')}"
                for task_id in plan.execution_order
            ])
            
            prompt = f"""
            Based on these task execution results, provide a comprehensive answer to the user's goal.
            
            Goal: {plan.goal}
            
            Task Results:
            {context}
            
            Provide a clear, concise final answer.
            """
            
            response = self.assistant.llm.answer(prompt)
            return response.text
        else:
            return f"Completed {results['tasks_executed']} tasks for: {plan.goal}"

    def _save_plan(self, plan: Plan):
        """Save plan to disk."""
        try:
            plan_file = os.path.join(self.plans_dir, f"{plan.id}.json")
            plan_data = {
                'id': plan.id,
                'goal': plan.goal,
                'status': plan.status.value,
                'created_at': plan.created_at,
                'completed_at': plan.completed_at,
                'progress': plan.progress,
                'tasks': {task_id: asdict(task) for task_id, task in plan.tasks.items()},
                'root_tasks': plan.root_tasks,
                'execution_order': plan.execution_order
            }
            
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2)
                
        except Exception as e:
            print(f"[HierarchicalPlanner] Failed to save plan: {e}")

    def load_plan(self, plan_id: str) -> Optional[Plan]:
        """Load a plan from disk."""
        plan_file = os.path.join(self.plans_dir, f"{plan_id}.json")
        
        if os.path.exists(plan_file):
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                plan = Plan(
                    id=data['id'],
                    goal=data['goal'],
                    status=TaskStatus(data['status']),
                    created_at=data['created_at'],
                    completed_at=data.get('completed_at'),
                    progress=data.get('progress', 0.0)
                )
                
                # Reconstruct tasks
                for task_id, task_data in data['tasks'].items():
                    task = Task(
                        id=task_data['id'],
                        description=task_data['description'],
                        task_type=task_data['task_type'],
                        status=TaskStatus(task_data['status']),
                        priority=TaskPriority(task_data['priority']),
                        dependencies=task_data['dependencies'],
                        subtasks=task_data['subtasks'],
                        estimated_duration=task_data['estimated_duration'],
                        required_tools=task_data['required_tools'],
                        context=task_data['context'],
                        result=task_data.get('result'),
                        error=task_data.get('error'),
                        created_at=task_data['created_at'],
                        started_at=task_data.get('started_at'),
                        completed_at=task_data.get('completed_at')
                    )
                    plan.tasks[task_id] = task
                
                plan.root_tasks = data['root_tasks']
                plan.execution_order = data['execution_order']
                
                return plan
                
            except Exception as e:
                print(f"[HierarchicalPlanner] Failed to load plan: {e}")
        
        return None

    def get_plan_statistics(self) -> Dict[str, Any]:
        """Get statistics about created plans."""
        if not os.path.exists(self.plans_dir):
            return {}
        
        plans = []
        for filename in os.listdir(self.plans_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.plans_dir, filename), 'r') as f:
                        data = json.load(f)
                    plans.append(data)
                except Exception:
                    continue
        
        if not plans:
            return {}
        
        total_plans = len(plans)
        completed = sum(1 for p in plans if p['status'] == 'completed')
        failed = sum(1 for p in plans if p['status'] == 'failed')
        in_progress = sum(1 for p in plans if p['status'] == 'in_progress')
        
        total_tasks = sum(len(p['tasks']) for p in plans)
        
        return {
            'total_plans': total_plans,
            'completed_plans': completed,
            'failed_plans': failed,
            'in_progress_plans': in_progress,
            'total_tasks': total_tasks,
            'success_rate': round(completed / total_plans * 100, 2) if total_plans > 0 else 0
        }
