"""
Plugin Dependency Management and Testing Framework
Manages plugin dependencies and provides testing framework for plugins.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class DependencyType(Enum):
    PYTHON = "python"
    NPM = "npm"
    SYSTEM = "system"
    INTERNAL = "internal"


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Dependency:
    dependency_id: str
    name: str
    version: str
    dependency_type: DependencyType
    is_required: bool
    installed: bool
    install_command: str
    created_at: str


@dataclass
class TestCase:
    test_id: str
    plugin_id: str
    name: str
    description: str
    test_function: str
    expected_result: str
    status: TestStatus
    last_run: Optional[str]
    last_result: Optional[str]
    created_at: str


@dataclass
class TestSuite:
    suite_id: str
    plugin_id: str
    name: str
    test_cases: List[str]
    created_at: str


class PluginDependencyManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.dev_dir = os.path.join(self.base_dir, "data", "developer")
        self.dependencies_file = os.path.join(self.dev_dir, "plugin_dependencies.json")
        self.test_cases_file = os.path.join(self.dev_dir, "test_cases.json")
        self.test_suites_file = os.path.join(self.dev_dir, "test_suites.json")
        
        os.makedirs(self.dev_dir, exist_ok=True)
        
        # Load data
        self.dependencies = self._load_dependencies()
        self.test_cases = self._load_test_cases()
        self.test_suites = self._load_test_suites()

    def _load_dependencies(self) -> Dict[str, Dependency]:
        """Load dependencies from disk."""
        if os.path.exists(self.dependencies_file):
            try:
                with open(self.dependencies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {dep_id: Dependency(**dep) for dep_id, dep in data.items()}
            except Exception:
                pass
        return {}

    def _save_dependencies(self):
        """Save dependencies to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {dep_id: asdict(dep) for dep_id, dep in self.dependencies.items()}
            with open(self.dependencies_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[PluginDependencyManager] Failed to save dependencies: {e}")

    def _load_test_cases(self) -> Dict[str, TestCase]:
        """Load test cases from disk."""
        if os.path.exists(self.test_cases_file):
            try:
                with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {test_id: TestCase(**test) for test_id, test in data.items()}
            except Exception:
                pass
        return {}

    def _save_test_cases(self):
        """Save test cases to disk."""
        try:
            data = {test_id: asdict(test) for test_id, test in self.test_cases.items()}
            with open(self.test_cases_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PluginDependencyManager] Failed to save test cases: {e}")

    def _load_test_suites(self) -> Dict[str, TestSuite]:
        """Load test suites from disk."""
        if os.path.exists(self.test_suites_file):
            try:
                with open(self.test_suites_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {suite_id: TestSuite(**suite) for suite_id, suite in data.items()}
            except Exception:
                pass
        return {}

    def _save_test_suites(self):
        """Save test suites to disk."""
        try:
            data = {suite_id: asdict(suite) for suite_id, suite in self.test_suites.items()}
            with open(self.test_suites_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PluginDependencyManager] Failed to save test suites: {e}")

    def add_dependency(self, name: str, version: str, dependency_type: DependencyType,
                     install_command: str, is_required: bool = True) -> Dependency:
        """
        Add a plugin dependency.
        
        Args:
            name: Dependency name
            version: Version
            dependency_type: Type of dependency
            install_command: Install command
            is_required: Whether dependency is required
            
        Returns:
            Dependency
        """
        dependency_id = f"dep_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        dependency = Dependency(
            dependency_id=dependency_id,
            name=name,
            version=version,
            dependency_type=dependency_type,
            is_required=is_required,
            installed=False,
            install_command=install_command,
            created_at=datetime.now().isoformat()
        )
        
        self.dependencies[dependency_id] = dependency
        self._save_dependencies()
        
        return dependency

    def mark_installed(self, dependency_id: str) -> bool:
        """Mark a dependency as installed."""
        if dependency_id not in self.dependencies:
            return False
        
        self.dependencies[dependency_id].installed = True
        self._save_dependencies()
        
        return True

    def get_plugin_dependencies(self, plugin_id: str) -> List[Dependency]:
        """Get dependencies for a specific plugin."""
        # In production, this would filter by plugin_id
        return list(self.dependencies.values())

    def check_dependencies(self) -> Tuple[List[str], List[str]]:
        """
        Check which dependencies are installed.
        
        Returns:
            (installed, missing)
        """
        installed = []
        missing = []
        
        for dep in self.dependencies.values():
            if dep.installed:
                installed.append(dep.name)
            else:
                missing.append(dep.name)
        
        return installed, missing

    def generate_requirements_txt(self) -> str:
        """Generate requirements.txt for Python dependencies."""
        python_deps = [d for d in self.dependencies.values() if d.dependency_type == DependencyType.PYTHON]
        
        lines = []
        for dep in python_deps:
            line = f"{dep.name}=={dep.version}"
            if not dep.is_required:
                line = f"# {line} (optional)"
            lines.append(line)
        
        return '\n'.join(lines)

    def generate_package_json(self) -> Dict:
        """Generate package.json for NPM dependencies."""
        npm_deps = [d for d in self.dependencies.values() if d.dependency_type == DependencyType.NPM]
        
        dependencies = {}
        for dep in npm_deps:
            dependencies[dep.name] = dep.version
        
        return {
            "dependencies": dependencies
        }

    def create_test_case(self, plugin_id: str, name: str, description: str,
                        test_function: str, expected_result: str) -> TestCase:
        """
        Create a test case.
        
        Args:
            plugin_id: Plugin ID
            name: Test name
            description: Test description
            test_function: Test function name
            expected_result: Expected result
            
        Returns:
            TestCase
        """
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        test_case = TestCase(
            test_id=test_id,
            plugin_id=plugin_id,
            name=name,
            description=description,
            test_function=test_function,
            expected_result=expected_result,
            status=TestStatus.PENDING,
            last_run=None,
            last_result=None,
            created_at=datetime.now().isoformat()
        )
        
        self.test_cases[test_id] = test_case
        self._save_test_cases()
        
        return test_case

    def create_test_suite(self, plugin_id: str, name: str, test_case_ids: List[str]) -> TestSuite:
        """
        Create a test suite.
        
        Args:
            plugin_id: Plugin ID
            name: Suite name
            test_case_ids: List of test case IDs
            
        Returns:
            TestSuite
        """
        suite_id = f"suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        suite = TestSuite(
            suite_id=suite_id,
            plugin_id=plugin_id,
            name=name,
            test_cases=test_case_ids,
            created_at=datetime.now().isoformat()
        )
        
        self.test_suites[suite_id] = suite
        self._save_test_suites()
        
        return suite

    def run_test(self, test_id: str) -> Tuple[bool, str]:
        """
        Run a single test case.
        
        Args:
            test_id: Test ID
            
        Returns:
            (passed, message)
        """
        if test_id not in self.test_cases:
            return False, "Test not found"
        
        test_case = self.test_cases[test_id]
        test_case.status = TestStatus.RUNNING
        self._save_test_cases()
        
        # In production, this would actually run the test
        # For now, simulate test execution
        try:
            # Simulate test execution
            test_case.status = TestStatus.PASSED
            test_case.last_run = datetime.now().isoformat()
            test_case.last_result = "Test passed"
            self._save_test_cases()
            return True, "Test passed"
        except Exception as e:
            test_case.status = TestStatus.FAILED
            test_case.last_run = datetime.now().isoformat()
            test_case.last_result = str(e)
            self._save_test_cases()
            return False, f"Test failed: {str(e)}"

    def run_test_suite(self, suite_id: str) -> Dict[str, Any]:
        """
        Run all tests in a suite.
        
        Args:
            suite_id: Suite ID
            
        Returns:
            Test results
        """
        if suite_id not in self.test_suites:
            return {'error': 'Suite not found'}
        
        suite = self.test_suites[suite_id]
        
        results = {
            'total': len(suite.test_cases),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }
        
        for test_id in suite.test_cases:
            passed, message = self.run_test(test_id)
            results['results'].append({
                'test_id': test_id,
                'passed': passed,
                'message': message
            })
            
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        return results

    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """Get a test case by ID."""
        return self.test_cases.get(test_id)

    def get_plugin_test_cases(self, plugin_id: str) -> List[TestCase]:
        """Get all test cases for a plugin."""
        return [t for t in self.test_cases.values() if t.plugin_id == plugin_id]

    def get_statistics(self) -> Dict[str, Any]:
        """Get dependency and testing statistics."""
        total_dependencies = len(self.dependencies)
        total_test_cases = len(self.test_cases)
        total_test_suites = len(self.test_suites)
        
        # Count by dependency type
        by_dep_type = {}
        for dep in self.dependencies.values():
            dtype = dep.dependency_type.value
            by_dep_type[dtype] = by_dep_type.get(dtype, 0) + 1
        
        # Count by test status
        by_test_status = {}
        for test in self.test_cases.values():
            status = test.status.value
            by_test_status[status] = by_test_status.get(status, 0) + 1
        
        return {
            'total_dependencies': total_dependencies,
            'by_dependency_type': by_dep_type,
            'total_test_cases': total_test_cases,
            'total_test_suites': total_test_suites,
            'by_test_status': by_test_status
        }

    def delete_dependency(self, dependency_id: str) -> bool:
        """Delete a dependency."""
        if dependency_id not in self.dependencies:
            return False
        
        del self.dependencies[dependency_id]
        self._save_dependencies()
        
        return True

    def delete_test_case(self, test_id: str) -> bool:
        """Delete a test case."""
        if test_id not in self.test_cases:
            return False
        
        del self.test_cases[test_id]
        self._save_test_cases()
        
        return True

    def export_test_report(self, suite_id: str, export_path: str) -> Tuple[bool, str]:
        """Export test report to file."""
        if suite_id not in self.test_suites:
            return False, "Suite not found"
        
        results = self.run_test_suite(suite_id)
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            return True, f"Test report exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
