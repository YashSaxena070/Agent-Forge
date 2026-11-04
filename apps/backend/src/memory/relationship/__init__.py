"""
Relationship memory using Neo4j for entity relationships.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from apps.backend.src.rag.graph.store import get_graph_store
from apps.backend.src.core.exceptions import MemoryError


class RelationshipMemory:
    """Relationship memory for entity-relationship tracking."""
    
    def __init__(self):
        self.graph_store = get_graph_store()
        self.max_depth = 3
    
    async def add_relationship(
        self,
        project_id: UUID,
        source: str,
        target: str,
        relationship_type: str,
        description: str = "",
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Add a relationship between entities."""
        try:
            await self.graph_store.driver.session().__aenter__()
            async with self.graph_store.driver.session() as session:
                await session.run("""
                    MERGE (e1:Entity {name: $source, project_id: $project_id})
                    MERGE (e2:Entity {name: $target, project_id: $project_id})
                    MERGE (e1)-[r:RELATES {type: $rel_type}]->(e2)
                    SET r.description = $description,
                        r.metadata = $metadata,
                        r.updated_at = datetime()
                """,
                source=source,
                target=target,
                rel_type=relationship_type,
                project_id=str(project_id),
                description=description,
                metadata=str(metadata or {}),
                )
            return True
        except Exception as e:
            raise MemoryError(f"Failed to add relationship: {str(e)}", memory_type="relationship", operation="add")
    
    async def query(
        self,
        project_id: UUID,
        entity: str,
        relationship_type: str = None,
        max_depth: int = None,
    ) -> List[Dict[str, Any]]:
        """Query relationships for an entity."""
        max_depth = max_depth or self.max_depth
        
        try:
            return await self.graph_store.query_relationships(
                project_id=project_id,
                entity=entity,
                relationship_type=relationship_type,
                max_depth=max_depth,
            )
        except Exception as e:
            raise MemoryError(f"Failed to query relationships: {str(e)}", memory_type="relationship", operation="query")
    
    async def get_entity(
        self,
        project_id: UUID,
        entity_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Get entity details."""
        try:
            async with self.graph_store.driver.session() as session:
                result = await session.run("""
                    MATCH (e:Entity {name: $name, project_id: $project_id})
                    OPTIONAL MATCH (e)-[r:RELATES]-(related:Entity)
                    RETURN e, collect(r) as relationships, collect(related) as related
                """, name=entity_name, project_id=str(project_id))
                
                record = await result.single()
                if record:
                    return {
                        "entity": dict(record["e"]),
                        "relationships": [dict(r) for r in record["relationships"] if r],
                        "related_entities": [dict(r) for r in record["related"] if r],
                    }
                return None
        except Exception as e:
            raise MemoryError(f"Failed to get entity: {str(e)}", memory_type="relationship", operation="get")
    
    async def find_path(
        self,
        project_id: UUID,
        source: str,
        target: str,
        max_depth: int = None,
    ) -> List[Dict[str, Any]]:
        """Find path between two entities."""
        max_depth = max_depth or self.max_depth
        
        try:
            async with self.graph_store.driver.session() as session:
                result = await session.run(f"""
                    MATCH path = shortestPath(
                        (e1:Entity {{name: $source, project_id: $project_id}})
                        -[r:RELATES*1..{max_depth}]-
                        (e2:Entity {{name: $target, project_id: $project_id}})
                    )
                    RETURN path
                """, source=source, target=target, project_id=str(project_id))
                
                paths = []
                async for record in result:
                    path = record["path"]
                    paths.append({
                        "nodes": [dict(n) for n in path.nodes],
                        "relationships": [dict(r) for r in path.relationships],
                    })
                
                return paths
        except Exception as e:
            raise MemoryError(f"Failed to find path: {str(e)}", memory_type="relationship", operation="find_path")
    
    async def get_subgraph(
        self,
        project_id: UUID,
        entity: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """Get subgraph around an entity."""
        try:
            async with self.graph_store.driver.session() as session:
                result = await session.run(f"""
                    MATCH (e:Entity {{name: $entity, project_id: $project_id}})
                    CALL apoc.path.subgraphAll(e, {{maxLevel: $depth}}) YIELD nodes, relationships
                    RETURN nodes, relationships
                """, entity=entity, project_id=str(project_id), depth=depth)
                
                record = await result.single()
                if record:
                    return {
                        "nodes": [dict(n) for n in record["nodes"]],
                        "relationships": [dict(r) for r in record["relationships"]],
                    }
                return {"nodes": [], "relationships": []}
        except Exception as e:
            raise MemoryError(f"Failed to get subgraph: {str(e)}", memory_type="relationship", operation="get_subgraph")


# Global instance
_relationship_memory: Optional[RelationshipMemory] = None


def get_relationship_memory() -> RelationshipMemory:
    """Get or create relationship memory instance."""
    global _relationship_memory
    if _relationship_memory is None:
        _relationship_memory = RelationshipMemory()
    return _relationship_memory