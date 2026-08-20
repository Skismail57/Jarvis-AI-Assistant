"""
Database Query Optimization
Provides query optimization and database performance improvements.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class QueryType(Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    JOIN = "join"
    AGGREGATE = "aggregate"


class OptimizationStatus(Enum):
    OPTIMIZED = "optimized"
    NEEDS_INDEX = "needs_index"
    NEEDS_REWRITE = "needs_rewrite"
    OK = "ok"


@dataclass
class QueryMetrics:
    query_id: str
    query: str
    query_type: QueryType
    execution_time_ms: float
    rows_affected: int
    execution_date: str
    optimization_status: OptimizationStatus
    suggestions: List[str]


@dataclass
class IndexRecommendation:
    index_id: str
    table_name: str
    column_name: str
    index_type: str  # 'btree', 'hash', 'gin', 'gist'
    estimated_improvement: float
    created_at: str


class QueryOptimizer:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.performance_dir = os.path.join(self.base_dir, "data", "performance")
        self.metrics_file = os.path.join(self.performance_dir, "query_metrics.json")
        self.indexes_file = os.path.join(self.performance_dir, "index_recommendations.json")
        
        os.makedirs(self.performance_dir, exist_ok=True)
        
        # Load data
        self.metrics = self._load_metrics()
        self.indexes = self._load_indexes()

    def _load_metrics(self) -> Dict[str, QueryMetrics]:
        """Load query metrics from disk."""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {query_id: QueryMetrics(**metric) for query_id, metric in data.items()}
            except Exception:
                pass
        return {}

    def _save_metrics(self):
        """Save query metrics to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {query_id: asdict(metric) for query_id, metric in self.metrics.items()}
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[QueryOptimizer] Failed to save metrics: {e}")

    def _load_indexes(self) -> Dict[str, IndexRecommendation]:
        """Load index recommendations from disk."""
        if os.path.exists(self.indexes_file):
            try:
                with open(self.indexes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {index_id: IndexRecommendation(**index) for index_id, index in data.items()}
            except Exception:
                pass
        return {}

    def _save_indexes(self):
        """Save index recommendations to disk."""
        try:
            data = {index_id: asdict(index) for index_id, index in self.indexes.items()}
            with open(self.indexes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[QueryOptimizer] Failed to save indexes: {e}")

    def analyze_query(self, query: str, execution_time_ms: float, 
                     rows_affected: int = 0) -> QueryMetrics:
        """
        Analyze a query for optimization opportunities.
        
        Args:
            query: SQL query
            execution_time_ms: Execution time in milliseconds
            rows_affected: Number of rows affected
            
        Returns:
            QueryMetrics
        """
        query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Determine query type
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            query_type = QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            query_type = QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            query_type = QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            query_type = QueryType.DELETE
        elif 'JOIN' in query_upper:
            query_type = QueryType.JOIN
        elif any(kw in query_upper for kw in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'GROUP BY']):
            query_type = QueryType.AGGREGATE
        else:
            query_type = QueryType.SELECT
        
        # Analyze and generate suggestions
        suggestions = self._generate_suggestions(query, query_type, execution_time_ms)
        
        # Determine optimization status
        if execution_time_ms > 1000:
            status = OptimizationStatus.NEEDS_REWRITE
        elif 'WHERE' not in query_upper and query_type == QueryType.SELECT:
            status = OptimizationStatus.NEEDS_INDEX
        elif suggestions:
            status = OptimizationStatus.NEEDS_INDEX
        else:
            status = OptimizationStatus.OK
        
        metrics = QueryMetrics(
            query_id=query_id,
            query=query,
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            rows_affected=rows_affected,
            execution_date=datetime.now().isoformat(),
            optimization_status=status,
            suggestions=suggestions
        )
        
        self.metrics[query_id] = metrics
        self._save_metrics()
        
        return metrics

    def _generate_suggestions(self, query: str, query_type: QueryType, 
                            execution_time_ms: float) -> List[str]:
        """Generate optimization suggestions."""
        suggestions = []
        query_upper = query.upper()
        
        # Check for SELECT *
        if 'SELECT *' in query_upper:
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        # Check for missing WHERE clause
        if query_type == QueryType.SELECT and 'WHERE' not in query_upper:
            suggestions.append("Add WHERE clause to filter results")
        
        # Check for missing LIMIT
        if query_type == QueryType.SELECT and 'LIMIT' not in query_upper:
            suggestions.append("Add LIMIT clause to prevent large result sets")
        
        # Check for slow joins
        if query_type == QueryType.JOIN and execution_time_ms > 100:
            suggestions.append("Consider adding indexes on join columns")
        
        # Check for subqueries
        if 'SELECT' in query_upper and query_upper.count('SELECT') > 1:
            suggestions.append("Consider rewriting subqueries as joins")
        
        # Check for ORDER BY without index
        if 'ORDER BY' in query_upper and execution_time_ms > 50:
            suggestions.append("Consider adding index on ORDER BY columns")
        
        # Check for LIKE patterns
        if 'LIKE' in query_upper and '%_' in query_upper:
            suggestions.append("Avoid leading wildcards in LIKE patterns")
        
        # Check for OR conditions
        if ' OR ' in query_upper:
            suggestions.append("Consider using UNION instead of OR for better index usage")
        
        return suggestions

    def recommend_index(self, table_name: str, column_name: str, 
                      index_type: str = 'btree', estimated_improvement: float = 0.5) -> IndexRecommendation:
        """
        Create an index recommendation.
        
        Args:
            table_name: Table name
            column_name: Column name
            index_type: Index type
            estimated_improvement: Estimated performance improvement (0-1)
            
        Returns:
            IndexRecommendation
        """
        index_id = f"index_{table_name}_{column_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        index = IndexRecommendation(
            index_id=index_id,
            table_name=table_name,
            column_name=column_name,
            index_type=index_type,
            estimated_improvement=estimated_improvement,
            created_at=datetime.now().isoformat()
        )
        
        self.indexes[index_id] = index
        self._save_indexes()
        
        return index

    def generate_index_sql(self, index_id: str) -> Optional[str]:
        """Generate SQL to create an index."""
        index = self.indexes.get(index_id)
        if not index:
            return None
        
        return f"CREATE INDEX idx_{index.table_name}_{index.column_name} ON {index.table_name} ({index.column_name}) USING {index.index_type};"

    def get_slow_queries(self, threshold_ms: float = 100) -> List[QueryMetrics]:
        """Get queries slower than threshold.""" 
        return [m for m in self.metrics.values() if m.execution_time_ms > threshold_ms]

    def get_query_metrics_by_type(self, query_type: QueryType) -> List[QueryMetrics]:
        """Get metrics by query type."""
        return [m for m in self.metrics.values() if m.query_type == query_type]

    def get_average_execution_time(self, query_type: QueryType = None) -> float:
        """Get average execution time."""
        metrics = self.get_query_metrics_by_type(query_type) if query_type else list(self.metrics.values())
        
        if not metrics:
            return 0.0
        
        return sum(m.execution_time_ms for m in metrics) / len(metrics)

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate optimization report."""
        total_queries = len(self.metrics)
        slow_queries = len(self.get_slow_queries())
        
        # Count by status
        by_status = {}
        for metric in self.metrics.values():
            status = metric.optimization_status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        # Count by type
        by_type = {}
        for metric in self.metrics.values():
            qtype = metric.query_type.value
            by_type[qtype] = by_type.get(qtype, 0) + 1
        
        # Index recommendations
        total_indexes = len(self.indexes)
        
        return {
            'total_queries': total_queries,
            'slow_queries': slow_queries,
            'by_status': by_status,
            'by_type': by_type,
            'total_index_recommendations': total_indexes,
            'average_execution_time_ms': round(self.get_average_execution_time(), 2)
        }

    def delete_metric(self, query_id: str) -> bool:
        """Delete a query metric."""
        if query_id not in self.metrics:
            return False
        
        del self.metrics[query_id]
        self._save_metrics()
        
        return True

    def delete_index(self, index_id: str) -> bool:
        """Delete an index recommendation."""
        if index_id not in self.indexes:
            return False
        
        del self.indexes[index_id]
        self._save_indexes()
        
        return True

    def clear_old_metrics(self, days: int = 30) -> int:
        """Clear metrics older than specified days."""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            query_id for query_id, metric in self.metrics.items()
            if datetime.fromisoformat(metric.execution_date) < cutoff_date
        ]
        
        for query_id in to_remove:
            del self.metrics[query_id]
        
        if to_remove:
            self._save_metrics()
        
        return len(to_remove)

    def export_report(self, export_path: str) -> Tuple[bool, str]:
        """Export optimization report to file."""
        try:
            report = {
                'report': self.get_optimization_report(),
                'slow_queries': [asdict(m) for m in self.get_slow_queries()],
                'index_recommendations': [asdict(i) for i in self.indexes.values()],
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            return True, f"Report exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
