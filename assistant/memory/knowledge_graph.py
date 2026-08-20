"""
Knowledge Graph for Entity Relationships
Maintains a graph of entities and their relationships for enhanced context understanding.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import re


@dataclass
class Entity:
    entity_id: str
    name: str
    entity_type: str  # 'person', 'location', 'organization', 'concept', 'object', 'event'
    attributes: Dict[str, Any]
    created_at: str
    last_accessed: str
    access_count: int = 0


@dataclass
class Relationship:
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str  # 'is_a', 'part_of', 'related_to', 'located_at', 'works_for', etc.
    confidence: float
    created_at: str
    last_verified: str
    metadata: Dict[str, Any] = None


@dataclass
class GraphQuery:
    query_id: str
    query_text: str
    entities_found: List[str]
    relationships_found: List[str]
    executed_at: str
    result: Any = None


class KnowledgeGraph:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.graph_dir = os.path.join(self.base_dir, "data", "knowledge_graph")
        self.entities_file = os.path.join(self.graph_dir, "entities.json")
        self.relationships_file = os.path.join(self.graph_dir, "relationships.json")
        self.queries_file = os.path.join(self.graph_dir, "queries.json")
        
        os.makedirs(self.graph_dir, exist_ok=True)
        
        # Load graph data
        self.entities = self._load_entities()
        self.relationships = self._load_relationships()
        self.queries = self._load_queries()
        
        # Build adjacency lists for efficient traversal
        self.adjacency_list = self._build_adjacency_list()
        
        # Relationship type definitions
        self.relation_types = self._initialize_relation_types()
        
        # Entity extraction patterns
        self.entity_patterns = self._initialize_entity_patterns()

    def _load_entities(self) -> Dict[str, Entity]:
        """Load entities from disk."""
        if os.path.exists(self.entities_file):
            try:
                with open(self.entities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {entity_id: Entity(**entity) for entity_id, entity in data.items()}
            except Exception:
                pass
        return {}

    def _save_entities(self):
        """Save entities to disk."""
        try:
            data = {entity_id: asdict(entity) for entity_id, entity in self.entities.items()}
            with open(self.entities_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[KnowledgeGraph] Failed to save entities: {e}")

    def _load_relationships(self) -> Dict[str, Relationship]:
        """Load relationships from disk."""
        if os.path.exists(self.relationships_file):
            try:
                with open(self.relationships_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {rel_id: Relationship(**rel) for rel_id, rel in data.items()}
            except Exception:
                pass
        return {}

    def _save_relationships(self):
        """Save relationships to disk."""
        try:
            data = {rel_id: asdict(rel) for rel_id, rel in self.relationships.items()}
            with open(self.relationships_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[KnowledgeGraph] Failed to save relationships: {e}")

    def _load_queries(self) -> Dict[str, GraphQuery]:
        """Load query history from disk."""
        if os.path.exists(self.queries_file):
            try:
                with open(self.queries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {query_id: GraphQuery(**query) for query_id, query in data.items()}
            except Exception:
                pass
        return {}

    def _save_queries(self):
        """Save query history to disk."""
        try:
            data = {query_id: asdict(query) for query_id, query in self.queries.items()}
            with open(self.queries_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[KnowledgeGraph] Failed to save queries: {e}")

    def _build_adjacency_list(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build adjacency list for efficient graph traversal."""
        adjacency = defaultdict(list)
        
        for rel in self.relationships.values():
            adjacency[rel.source_entity_id].append((rel.target_entity_id, rel.relation_type))
        
        return dict(adjacency)

    def _initialize_relation_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize valid relationship types with their properties."""
        return {
            'is_a': {'inverse': 'instance_of', 'transitive': False, 'symmetric': False},
            'instance_of': {'inverse': 'is_a', 'transitive': True, 'symmetric': False},
            'part_of': {'inverse': 'has_part', 'transitive': True, 'symmetric': False},
            'has_part': {'inverse': 'part_of', 'transitive': False, 'symmetric': False},
            'related_to': {'inverse': 'related_to', 'transitive': False, 'symmetric': True},
            'located_at': {'inverse': 'contains', 'transitive': False, 'symmetric': False},
            'contains': {'inverse': 'located_at', 'transitive': True, 'symmetric': False},
            'works_for': {'inverse': 'employs', 'transitive': False, 'symmetric': False},
            'employs': {'inverse': 'works_for', 'transitive': False, 'symmetric': False},
            'knows': {'inverse': 'known_by', 'transitive': False, 'symmetric': True},
            'known_by': {'inverse': 'knows', 'transitive': False, 'symmetric': True},
            'friend_of': {'inverse': 'friend_of', 'transitive': False, 'symmetric': True},
            'member_of': {'inverse': 'has_member', 'transitive': False, 'symmetric': False},
            'has_member': {'inverse': 'member_of', 'transitive': True, 'symmetric': False},
            'owns': {'inverse': 'owned_by', 'transitive': False, 'symmetric': False},
            'owned_by': {'inverse': 'owns', 'transitive': False, 'symmetric': False},
            'created_by': {'inverse': 'created', 'transitive': False, 'symmetric': False},
            'created': {'inverse': 'created_by', 'transitive': False, 'symmetric': False},
        }

    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for entity extraction."""
        return {
            'person': [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Full names
                r'\b(Mr|Mrs|Ms|Dr|Prof)\. [A-Z][a-z]+\b',  # Titles
            ],
            'location': [
                r'\b[A-Z][a-z]+(?:, [A-Z][a-z]+)?\b',  # City, State
                r'\b\d+ .+ Street\b',  # Addresses
            ],
            'organization': [
                r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Ltd|Company)\b',
                r'\b[A-Z][a-z]+ University\b',
            ],
            'date': [
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b',
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            ],
            'time': [
                r'\b\d{1,2}:\d{2} (?:AM|PM|am|pm)\b',
            ],
        }

    def add_entity(self, name: str, entity_type: str, 
                  attributes: Dict[str, Any] = None) -> Entity:
        """
        Add a new entity to the knowledge graph.
        
        Args:
            name: Entity name
            entity_type: Type of entity
            attributes: Additional attributes
            
        Returns:
            Created Entity
        """
        entity_id = f"{entity_type}_{name.lower().replace(' ', '_')}"
        
        entity = Entity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            attributes=attributes or {},
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat()
        )
        
        self.entities[entity_id] = entity
        self._save_entities()
        
        return entity

    def add_relationship(self, source_entity_id: str, target_entity_id: str,
                       relation_type: str, confidence: float = 1.0,
                       metadata: Dict[str, Any] = None) -> Relationship:
        """
        Add a relationship between two entities.
        
        Args:
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID
            relation_type: Type of relationship
            confidence: Confidence score
            metadata: Additional metadata
            
        Returns:
            Created Relationship
        """
        if relation_type not in self.relation_types:
            raise ValueError(f"Unknown relation type: {relation_type}")
        
        if source_entity_id not in self.entities:
            raise ValueError(f"Source entity not found: {source_entity_id}")
        
        if target_entity_id not in self.entities:
            raise ValueError(f"Target entity not found: {target_entity_id}")
        
        relationship_id = f"{source_entity_id}_{relation_type}_{target_entity_id}"
        
        relationship = Relationship(
            relationship_id=relationship_id,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation_type=relation_type,
            confidence=confidence,
            created_at=datetime.now().isoformat(),
            last_verified=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        self.relationships[relationship_id] = relationship
        
        # Update adjacency list
        self.adjacency_list[source_entity_id].append((target_entity_id, relation_type))
        
        # Add inverse relationship if symmetric
        if self.relation_types[relation_type]['symmetric']:
            inverse_id = f"{target_entity_id}_{relation_type}_{source_entity_id}"
            inverse_rel = Relationship(
                relationship_id=inverse_id,
                source_entity_id=target_entity_id,
                target_entity_id=source_entity_id,
                relation_type=relation_type,
                confidence=confidence,
                created_at=datetime.now().isoformat(),
                last_verified=datetime.now().isoformat(),
                metadata=metadata
            )
            self.relationships[inverse_id] = inverse_rel
            self.adjacency_list[target_entity_id].append((source_entity_id, relation_type))
        
        self._save_relationships()
        
        return relationship

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using pattern matching.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities with their types
        """
        extracted = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity_name = match.group()
                    extracted.append({
                        'name': entity_name,
                        'type': entity_type,
                        'position': match.span(),
                        'confidence': 0.8
                    })
        
        return extracted

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        if entity_id in self.entities:
            # Update access statistics
            self.entities[entity_id].last_accessed = datetime.now().isoformat()
            self.entities[entity_id].access_count += 1
            self._save_entities()
            return self.entities[entity_id]
        return None

    def find_entity_by_name(self, name: str, entity_type: str = None) -> List[Entity]:
        """Find entities by name (fuzzy match)."""
        name_lower = name.lower()
        matches = []
        
        for entity in self.entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue
            
            if name_lower in entity.name.lower():
                matches.append(entity)
        
        return matches

    def get_neighbors(self, entity_id: str, relation_type: str = None,
                    max_depth: int = 1) -> List[Entity]:
        """
        Get neighboring entities in the graph.
        
        Args:
            entity_id: Starting entity ID
            relation_type: Filter by relationship type
            max_depth: Maximum traversal depth
            
        Returns:
            List of neighboring entities
        """
        if entity_id not in self.entities:
            return []
        
        visited = set()
        neighbors = []
        queue = [(entity_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth > max_depth or current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id in self.adjacency_list:
                for neighbor_id, rel_type in self.adjacency_list[current_id]:
                    if relation_type is None or rel_type == relation_type:
                        if neighbor_id in self.entities:
                            neighbors.append(self.entities[neighbor_id])
                            queue.append((neighbor_id, depth + 1))
        
        return neighbors

    def get_path(self, source_entity_id: str, target_entity_id: str,
                max_length: int = 5) -> List[str]:
        """
        Find a path between two entities using BFS.
        
        Args:
            source_entity_id: Starting entity ID
            target_entity_id: Target entity ID
            max_length: Maximum path length
            
        Returns:
            List of entity IDs forming the path
        """
        if source_entity_id not in self.entities or target_entity_id not in self.entities:
            return []
        
        if source_entity_id == target_entity_id:
            return [source_entity_id]
        
        queue = [(source_entity_id, [source_entity_id])]
        visited = {source_entity_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_length:
                continue
            
            if current_id in self.adjacency_list:
                for neighbor_id, _ in self.adjacency_list[current_id]:
                    if neighbor_id == target_entity_id:
                        return path + [neighbor_id]
                    
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append((neighbor_id, path + [neighbor_id]))
        
        return []

    def query_graph(self, query_text: str, entity_filter: str = None,
                  relation_filter: str = None) -> GraphQuery:
        """
        Query the knowledge graph.
        
        Args:
            query_text: Natural language query
            entity_filter: Filter by entity type
            relation_filter: Filter by relationship type
            
        Returns:
            GraphQuery with results
        """
        query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Extract entities from query
        extracted_entities = self.extract_entities(query_text)
        entities_found = []
        
        for extracted in extracted_entities:
            matches = self.find_entity_by_name(extracted['name'], entity_filter)
            for match in matches:
                entities_found.append(match.entity_id)
        
        # Find relationships
        relationships_found = []
        for entity_id in entities_found:
            if entity_id in self.adjacency_list:
                for neighbor_id, rel_type in self.adjacency_list[entity_id]:
                    if relation_filter is None or rel_type == relation_filter:
                        rel_id = f"{entity_id}_{rel_type}_{neighbor_id}"
                        if rel_id in self.relationships:
                            relationships_found.append(rel_id)
        
        query = GraphQuery(
            query_id=query_id,
            query_text=query_text,
            entities_found=entities_found,
            relationships_found=relationships_found,
            executed_at=datetime.now().isoformat()
        )
        
        self.queries[query_id] = query
        self._save_queries()
        
        return query

    def get_entity_context(self, entity_id: str, context_window: int = 2) -> Dict[str, Any]:
        """
        Get contextual information about an entity.
        
        Args:
            entity_id: Entity ID
            context_window: Number of hops for context
            
        Returns:
            Context information including related entities and relationships
        """
        if entity_id not in self.entities:
            return {}
        
        entity = self.entities[entity_id]
        neighbors = self.get_neighbors(entity_id, max_depth=context_window)
        
        # Get relationships
        relationships = []
        if entity_id in self.adjacency_list:
            for neighbor_id, rel_type in self.adjacency_list[entity_id]:
                rel_id = f"{entity_id}_{rel_type}_{neighbor_id}"
                if rel_id in self.relationships:
                    relationships.append(self.relationships[rel_id])
        
        return {
            'entity': asdict(entity),
            'neighbors': [asdict(n) for n in neighbors],
            'relationships': [asdict(r) for r in relationships],
            'total_connections': len(relationships)
        }

    def infer_relationships(self, entity_id: str, max_inferences: int = 5) -> List[Relationship]:
        """
        Infer potential relationships based on transitivity and patterns.
        
        Args:
            entity_id: Entity to infer relationships for
            max_inferences: Maximum number of inferences
            
        Returns:
            List of inferred relationships
        """
        if entity_id not in self.entities:
            return []
        
        inferences = []
        
        # Transitive inferences
        for rel_id, relationship in self.relationships.items():
            if relationship.source_entity_id == entity_id:
                rel_type = relationship.relation_type
                target_id = relationship.target_entity_id
                
                if self.relation_types[rel_type]['transitive']:
                    # Check if target has further relationships of same type
                    if target_id in self.adjacency_list:
                        for next_target_id, next_rel_type in self.adjacency_list[target_id]:
                            if next_rel_type == rel_type:
                                # Infer: entity_id -> rel_type -> next_target_id
                                inferred_rel_id = f"{entity_id}_{rel_type}_{next_target_id}"
                                if inferred_rel_id not in self.relationships:
                                    inferred = Relationship(
                                        relationship_id=inferred_rel_id,
                                        source_entity_id=entity_id,
                                        target_entity_id=next_target_id,
                                        relation_type=rel_type,
                                        confidence=relationship.confidence * 0.7,  # Lower confidence for inferences
                                        created_at=datetime.now().isoformat(),
                                        last_verified=datetime.now().isoformat(),
                                        metadata={'inferred': True, 'path': [entity_id, target_id, next_target_id]}
                                    )
                                    inferences.append(inferred)
                                    
                                    if len(inferences) >= max_inferences:
                                        return inferences
        
        return inferences

    def update_entity(self, entity_id: str, attributes: Dict[str, Any] = None) -> bool:
        """Update entity attributes."""
        if entity_id not in self.entities:
            return False
        
        if attributes:
            self.entities[entity_id].attributes.update(attributes)
        
        self.entities[entity_id].last_accessed = datetime.now().isoformat()
        self._save_entities()
        
        return True

    def remove_entity(self, entity_id: str) -> bool:
        """Remove an entity and its relationships."""
        if entity_id not in self.entities:
            return False
        
        # Remove all relationships involving this entity
        rels_to_remove = [rel_id for rel_id, rel in self.relationships.items()
                         if rel.source_entity_id == entity_id or rel.target_entity_id == entity_id]
        
        for rel_id in rels_to_remove:
            del self.relationships[rel_id]
        
        # Remove from adjacency list
        if entity_id in self.adjacency_list:
            del self.adjacency_list[entity_id]
        
        # Remove references from other adjacency lists
        for source_id in self.adjacency_list:
            self.adjacency_list[source_id] = [
                (target_id, rel_type) for target_id, rel_type in self.adjacency_list[source_id]
                if target_id != entity_id
            ]
        
        # Remove entity
        del self.entities[entity_id]
        
        self._save_entities()
        self._save_relationships()
        
        return True

    def remove_relationship(self, relationship_id: str) -> bool:
        """Remove a relationship."""
        if relationship_id not in self.relationships:
            return False
        
        relationship = self.relationships[relationship_id]
        
        # Remove from adjacency list
        if relationship.source_entity_id in self.adjacency_list:
            self.adjacency_list[relationship.source_entity_id] = [
                (target_id, rel_type) for target_id, rel_type in self.adjacency_list[relationship.source_entity_id]
                if not (target_id == relationship.target_entity_id and rel_type == relationship.relation_type)
            ]
        
        # Remove inverse if symmetric
        if self.relation_types[relationship.relation_type]['symmetric']:
            inverse_id = f"{relationship.target_entity_id}_{relationship.relation_type}_{relationship.source_entity_id}"
            if inverse_id in self.relationships:
                del self.relationships[inverse_id]
        
        del self.relationships[relationship_id]
        self._save_relationships()
        
        return True

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        total_entities = len(self.entities)
        total_relationships = len(self.relationships)
        
        # Count by entity type
        entity_types = defaultdict(int)
        for entity in self.entities.values():
            entity_types[entity.entity_type] += 1
        
        # Count by relationship type
        relation_types = defaultdict(int)
        for rel in self.relationships.values():
            relation_types[rel.relation_type] += 1
        
        # Calculate graph density
        max_possible_edges = total_entities * (total_entities - 1) / 2 if total_entities > 1 else 0
        density = total_relationships / max_possible_edges if max_possible_edges > 0 else 0
        
        return {
            'total_entities': total_entities,
            'total_relationships': total_relationships,
            'entity_types': dict(entity_types),
            'relation_types': dict(relation_types),
            'graph_density': round(density, 4),
            'total_queries': len(self.queries)
        }

    def export_graph(self, export_path: str) -> Tuple[bool, str]:
        """Export the knowledge graph to a file."""
        try:
            export_data = {
                'entities': {entity_id: asdict(entity) for entity_id, entity in self.entities.items()},
                'relationships': {rel_id: asdict(rel) for rel_id, rel in self.relationships.items()},
                'queries': {query_id: asdict(query) for query_id, query in self.queries.items()},
                'statistics': self.get_graph_statistics(),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Knowledge graph exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def import_graph(self, import_path: str) -> Tuple[bool, str]:
        """Import a knowledge graph from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Import entities
            for entity_id, entity_data in import_data['entities'].items():
                self.entities[entity_id] = Entity(**entity_data)
            
            # Import relationships
            for rel_id, rel_data in import_data['relationships'].items():
                self.relationships[rel_id] = Relationship(**rel_data)
            
            # Rebuild adjacency list
            self.adjacency_list = self._build_adjacency_list()
            
            self._save_entities()
            self._save_relationships()
            
            return True, f"Knowledge graph imported from {import_path}"
            
        except Exception as e:
            return False, f"Import failed: {str(e)}"

    def clear_graph(self) -> bool:
        """Clear all entities and relationships."""
        try:
            self.entities.clear()
            self.relationships.clear()
            self.queries.clear()
            self.adjacency_list.clear()
            
            self._save_entities()
            self._save_relationships()
            self._save_queries()
            
            return True
            
        except Exception as e:
            print(f"[KnowledgeGraph] Failed to clear graph: {e}")
            return False
