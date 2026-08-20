"""
Docker Containerization and CI/CD Pipelines
Provides Docker configuration and CI/CD pipeline setup for deployment.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class DeploymentEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DockerConfig:
    config_id: str
    app_name: str
    image_name: str
    tag: str
    base_image: str
    expose_ports: List[int]
    environment_variables: Dict[str, str]
    volumes: List[Dict[str, str]]
    health_check: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str


@dataclass
class PipelineConfig:
    pipeline_id: str
    name: str
    environment: DeploymentEnvironment
    stages: List[str]
    triggers: List[str]
    created_at: str


@dataclass
class PipelineRun:
    run_id: str
    pipeline_id: str
    status: PipelineStatus
    started_at: str
    completed_at: Optional[str]
    duration_seconds: float
    logs: List[str]
    artifacts: List[str]


class DeploymentManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.deployment_dir = os.path.join(self.base_dir, "deployment")
        self.docker_file = os.path.join(self.deployment_dir, "docker_configs.json")
        self.pipelines_file = os.path.join(self.deployment_dir, "pipeline_configs.json")
        self.pipeline_runs_file = os.path.join(self.deployment_dir, "pipeline_runs.json")
        
        os.makedirs(self.deployment_dir, exist_ok=True)
        
        # Load data
        self.docker_configs = self._load_docker_configs()
        self.pipeline_configs = self._load_pipeline_configs()
        self.pipeline_runs = self._load_pipeline_runs()

    def _load_docker_configs(self) -> Dict[str, DockerConfig]:
        """Load Docker configurations from disk."""
        if os.path.exists(self.docker_file):
            try:
                with open(self.docker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {config_id: DockerConfig(**config) for config_id, config in data.items()}
            except Exception:
                pass
        return {}

    def _save_docker_configs(self):
        """Save Docker configurations to disk."""
        try:
            data = {config_id: asdict(config) for config_id, config in self.docker_configs.items()}
            with open(self.docker_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DeploymentManager] Failed to save docker configs: {e}")

    def _load_pipeline_configs(self) -> Dict[str, PipelineConfig]:
        """Load pipeline configurations from disk."""
        if os.path.exists(self.pipelines_file):
            try:
                with open(self.pipelines_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {pipeline_id: PipelineConfig(**pipeline) for pipeline_id, pipeline in data.items()}
            except Exception:
                pass
        return {}

    def _save_pipeline_configs(self):
        """Save pipeline configurations to disk."""
        try:
            data = {pipeline_id: asdict(pipeline) for pipeline_id, pipeline in self.pipeline_configs.items()}
            with open(self.pipelines_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DeploymentManager] Failed to save pipeline configs: {e}")

    def _load_pipeline_runs(self) -> Dict[str, PipelineRun]:
        """Load pipeline runs from disk."""
        if os.path.exists(self.pipeline_runs_file):
            try:
                with open(self.pipeline_runs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {run_id: PipelineRun(**run) for run_id, run in data.items()}
            except Exception:
                pass
        return {}

    def _save_pipeline_runs(self):
        """Save pipeline runs to disk."""
        try:
            data = {run_id: asdict(run) for run_id, run in self.pipeline_runs.items()}
            with open(self.pipeline_runs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DeploymentManager] Failed to save pipeline runs: {e}")

    def create_docker_config(self, app_name: str, image_name: str, tag: str = "latest",
                           base_image: str = "python:3.11-slim",
                           expose_ports: List[int] = None) -> DockerConfig:
        """
        Create a Docker configuration.
        
        Args:
            app_name: Application name
            image_name: Docker image name
            tag: Image tag
            base_image: Base Docker image
            expose_ports: Ports to expose
            
        Returns:
            DockerConfig
        """
        config_id = f"docker_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        config = DockerConfig(
            config_id=config_id,
            app_name=app_name,
            image_name=image_name,
            tag=tag,
            base_image=base_image,
            expose_ports=expose_ports or [8000],
            environment_variables={},
            volumes=[],
            health_check={
                'test': ['CMD-SHELL', 'curl -f http://localhost:8000/health || exit 1'],
                'interval': 30,
                'timeout': 10,
                'retries': 3
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.docker_configs[config_id] = config
        self._save_docker_configs()
        
        return config

    def generate_dockerfile(self, config_id: str) -> str:
        """Generate Dockerfile content."""
        config = self.docker_configs.get(config_id)
        if not config:
            return ""
        
        dockerfile = f"""
FROM {config.base_image}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
{chr(10).join([f'EXPOSE {port}' for port in config.expose_ports])}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "main.py"]
"""
        return dockerfile.strip()

    def generate_docker_compose(self, config_id: str) -> str:
        """Generate docker-compose.yml content."""
        config = self.docker_configs.get(config_id)
        if not config:
            return ""
        
        env_vars = '\n'.join([f'      - {k}={v}' for k, v in config.environment_variables.items()])
        volumes = '\n'.join([f'      - {v["source"]}:{v["target"]}' for v in config.volumes])
        ports = '\n'.join([f'      - "{p}:{p}"' for p in config.expose_ports])
        
        compose = f"""
version: '3.8'

services:
  {config.app_name}:
    image: {config.image_name}:{config.tag}
    container_name: {config.app_name}
    build: .
    ports:
{ports}
    environment:
{env_vars}
    volumes:
{volumes}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

networks:
  default:
    name: jarvis-network
"""
        return compose.strip()

    def add_environment_variable(self, config_id: str, key: str, value: str) -> bool:
        """Add environment variable to Docker config."""
        if config_id not in self.docker_configs:
            return False
        
        self.docker_configs[config_id].environment_variables[key] = value
        self.docker_configs[config_id].updated_at = datetime.now().isoformat()
        self._save_docker_configs()
        
        return True

    def add_volume(self, config_id: str, source: str, target: str) -> bool:
        """Add volume to Docker config."""
        if config_id not in self.docker_configs:
            return False
        
        self.docker_configs[config_id].volumes.append({'source': source, 'target': target})
        self.docker_configs[config_id].updated_at = datetime.now().isoformat()
        self._save_docker_configs()
        
        return True

    def create_pipeline(self, name: str, environment: DeploymentEnvironment,
                      stages: List[str] = None, triggers: List[str] = None) -> PipelineConfig:
        """
        Create a CI/CD pipeline configuration.
        
        Args:
            name: Pipeline name
            environment: Deployment environment
            stages: Pipeline stages
            triggers: Pipeline triggers
            
        Returns:
            PipelineConfig
        """
        pipeline_id = f"pipeline_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pipeline = PipelineConfig(
            pipeline_id=pipeline_id,
            name=name,
            environment=environment,
            stages=stages or ['build', 'test', 'deploy'],
            triggers=triggers or ['push', 'pull_request'],
            created_at=datetime.now().isoformat()
        )
        
        self.pipeline_configs[pipeline_id] = pipeline
        self._save_pipeline_configs()
        
        return pipeline

    def generate_github_actions_workflow(self, pipeline_id: str) -> str:
        """Generate GitHub Actions workflow file."""
        pipeline = self.pipeline_configs.get(pipeline_id)
        if not pipeline:
            return ""
        
        stages_yaml = '\n'.join([f'      - name: {stage}\n        run: echo "Running {stage}"' for stage in pipeline.stages])
        triggers_yaml = '\n'.join([f'      - {trigger}' for trigger in pipeline.triggers])
        
        workflow = f"""
name: {pipeline.name}

on:
{triggers_yaml}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
{stages_yaml}
      
      - name: Build Docker image
        run: docker build -t jarvis-assistant:latest .
      
      - name: Deploy to {pipeline.environment.value}
        if: pipeline.environment.value == 'production'
        run: |
          echo "Deploying to {pipeline.environment.value}"
          # Add deployment commands here
"""
        return workflow.strip()

    def generate_gitlab_ci(self, pipeline_id: str) -> str:
        """Generate GitLab CI configuration."""
        pipeline = self.pipeline_configs.get(pipeline_id)
        if not pipeline:
            return ""
        
        stages_yaml = '\n'.join([f'  - {stage}' for stage in pipeline.stages])
        
        gitlab_ci = f"""
stages:
{stages_yaml}

variables:
  DOCKER_IMAGE: jarvis-assistant:latest
  DEPLOY_ENVIRONMENT: {pipeline.environment.value}

before_script:
  - python -m pip install -r requirements.txt

build:
  stage: build
  script:
    - echo "Building application"
    - docker build -t $DOCKER_IMAGE .
  artifacts:
    paths:
      - dist/

test:
  stage: test
  script:
    - echo "Running tests"
    - pytest tests/

deploy:
  stage: deploy
  script:
    - echo "Deploying to $DEPLOY_ENVIRONMENT"
    - docker push $DOCKER_IMAGE
  only:
    - main
  when: manual
"""
        return gitlab_ci.strip()

    def run_pipeline(self, pipeline_id: str) -> PipelineRun:
        """
        Run a pipeline.
        
        Args:
            pipeline_id: Pipeline ID
            
        Returns:
            PipelineRun
        """
        if pipeline_id not in self.pipeline_configs:
            raise ValueError("Pipeline not found")
        
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        started_at = datetime.now().isoformat()
        
        # Simulate pipeline execution
        import time
        start_time = time.time()
        
        pipeline_run = PipelineRun(
            run_id=run_id,
            pipeline_id=pipeline_id,
            status=PipelineStatus.RUNNING,
            started_at=started_at,
            completed_at=None,
            duration_seconds=0.0,
            logs=[],
            artifacts=[]
        )
        
        self.pipeline_runs[run_id] = pipeline_run
        self._save_pipeline_runs()
        
        # Simulate stages
        pipeline = self.pipeline_configs[pipeline_id]
        for stage in pipeline.stages:
            pipeline_run.logs.append(f"Running stage: {stage}")
            time.sleep(0.1)  # Simulate stage execution
            pipeline_run.logs.append(f"Completed stage: {stage}")
        
        duration = time.time() - start_time
        pipeline_run.status = PipelineStatus.SUCCESS
        pipeline_run.completed_at = datetime.now().isoformat()
        pipeline_run.duration_seconds = duration
        pipeline_run.artifacts = ['build_output', 'test_results']
        
        self._save_pipeline_runs()
        
        return pipeline_run

    def get_docker_config(self, config_id: str) -> Optional[DockerConfig]:
        """Get Docker configuration by ID."""
        return self.docker_configs.get(config_id)

    def get_pipeline_config(self, pipeline_id: str) -> Optional[PipelineConfig]:
        """Get pipeline configuration by ID."""
        return self.pipeline_configs.get(pipeline_id)

    def get_pipeline_run(self, run_id: str) -> Optional[PipelineRun]:
        """Get pipeline run by ID."""
        return self.pipeline_runs.get(run_id)

    def delete_docker_config(self, config_id: str) -> bool:
        """Delete Docker configuration."""
        if config_id not in self.docker_configs:
            return False
        
        del self.docker_configs[config_id]
        self._save_docker_configs()
        
        return True

    def delete_pipeline_config(self, pipeline_id: str) -> bool:
        """Delete pipeline configuration."""
        if pipeline_id not in self.pipeline_configs:
            return False
        
        del self.pipeline_configs[pipeline_id]
        self._save_pipeline_configs()
        
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get deployment statistics."""
        total_docker_configs = len(self.docker_configs)
        total_pipeline_configs = len(self.pipeline_configs)
        total_pipeline_runs = len(self.pipeline_runs)
        
        # Count by environment
        by_environment = {}
        for pipeline in self.pipeline_configs.values():
            env = pipeline.environment.value
            by_environment[env] = by_environment.get(env, 0) + 1
        
        # Count by pipeline status
        by_status = {}
        for run in self.pipeline_runs.values():
            status = run.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_docker_configs': total_docker_configs,
            'total_pipeline_configs': total_pipeline_configs,
            'total_pipeline_runs': total_pipeline_runs,
            'by_environment': by_environment,
            'by_status': by_status
        }

    def export_deployment_config(self, config_id: str, export_dir: str) -> Tuple[bool, str]:
        """Export Docker and pipeline configurations to directory."""
        config = self.get_docker_config(config_id)
        if not config:
            return False, "Docker config not found"
        
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate Dockerfile
            dockerfile = self.generate_dockerfile(config_id)
            with open(os.path.join(export_dir, 'Dockerfile'), 'w') as f:
                f.write(dockerfile)
            
            # Generate docker-compose.yml
            compose = self.generate_docker_compose(config_id)
            with open(os.path.join(export_dir, 'docker-compose.yml'), 'w') as f:
                f.write(compose)
            
            # Generate .dockerignore
            dockerignore = """
__pycache__
*.pyc
.venv
venv/
.env
.git
.gitignore
data/
logs/
*.log
"""
            with open(os.path.join(export_dir, '.dockerignore'), 'w') as f:
                f.write(dockerignore.strip())
            
            return True, f"Deployment configs exported to {export_dir}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
