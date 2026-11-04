"""
Graph store for entity-relationship storage using Neo4j.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import Neo4jError

from apps.backend.src.core.config import settings
from apps.backend.src.core.telemetry import record_rag_metrics
from apps.backend.src.core.exceptions import RAGError


class GraphStore:
    """Graph store for entity-relationship retrieval."""
    
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
    
    async def initialize(self):
        """Initialize the driver."""
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        await self.driver.verify_connectivity()
        
        # Create indexes
        await self._create_indexes()
    
    async def _create_indexes(self):
        """Create necessary indexes."""
        async with self.driver.session() as session:
            # Create constraints and indexes
            await session.run("""
                CREATE CONSTRAINT project_id IF NOT EXISTS
                FOR (p:Project) REQUIRE p.project_id IS UNIQUE
            """)
            await session.run("""
                CREATE INDEX entity_name IF NOT EXISTS
                FOR (e:Entity) ON (e.name)
            """)
            await session.run("""
                CREATE INDEX entity_type IF NOT EXISTS
                FOR (e:Entity) ON (e.type)
            """)
    
    async def add_documents(
        self,
        project_id: UUID,
        documents: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
    ) -> int:
        """Add documents and extract entities/relationships."""
        if not self.driver:
            await self.initialize()
        
        project_id_str = str(project_id)
        count = 0
        
        async with self.driver.session() as session:
            # Create project node
            await session.run("""
                MERGE (p:Project {project_id: $project_id})
                SET p.created_at = datetime()
            """, project_id=project_id_str)
            
            for doc in documents:
                content = doc.get("content", "")
                title = doc.get("title", "")
                doc_type = doc.get("type", "document")
                
                # Extract entities and relationships (placeholder)
                entities = await self._extract_entities(content)
                relationships = await self._extract_relationships(content, entities)
                
                # Store document
                await session.run("""
                    CREATE (d:Document {
                        id: $doc_id,
                        project_id: $project_id,
                        title: $title,
                        content: $content,
                        type: $doc_type,
                        source: $source,
                        metadata: $metadata,
                        created_at: datetime()
                    })
                    MERGE (p:Project {project_id: $project_id})
                    MERGE (p)-[:CONTAINS]->(d)
                """, 
                doc_id=doc.get("id", str(uuid4())),
                project_id=project_id_str,
                title=title,
                content=content,
                doc_type=doc_type,
                source=metadata.get("source", "unknown") if metadata else "unknown",
                metadata=str(doc.get("metadata", {})),
                )
                
                # Store entities
                for entity in entities:
                    await session.run("""
                        MERGE (e:Entity {name: $name, type: $type, project_id: $project_id})
                        SET e.description = $description,
                            e.updated_at = datetime()
                        MERGE (d:Document {id: $doc_id})
                        MERGE (d)-[:MENTIONS]->(e)
                    """,
                    name=entity["name"],
                    type=entity["type"],
                    project_id=project_id_str,
                    description=entity.get("description", ""),
                    doc_id=doc.get("id", str(uuid4())),
                    )
                
                # Store relationships
                for rel in relationships:
                    await session.run("""
                        MATCH (e1:Entity {name: $source, project_id: $project_id})
                        MATCH (e2:Entity {name: $target, project_id: $project_id})
                        MERGE (e1)-[r:RELATES {type: $rel_type}]->(e2)
                        SET r.description = $description,
                            r.updated_at = datetime()
                    """,
                    source=rel["source"],
                    target=rel["target"],
                    rel_type=rel["type"],
                    project_id=project_id_str,
                    description=rel.get("description", ""),
                    )
                
                count += 1
        
        return count
    
    async def search(
        self,
        project_id: UUID,
        query: str,
        top_k: int = 10,
        filters: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Search for relevant entities and relationships."""
        if not self.driver:
            await self.initialize()
        
        project_id_str = str(project_id)
        
        # Search entities by name/type matching query
        cypher = """
            MATCH (e:Entity {project_id: $project_id})
            WHERE toLower(e.name) CONTAINS toLower($query)
               OR toLower(e.description) CONTAINS toLower($query)
            OPTIONAL MATCH (e)-[r:RELATES]-(related:Entity)
            RETURN e, collect(r) as relationships, collect(related) as related_entities
            LIMIT $top_k
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, project_id=project_id_str, query=query, top_k=top_k)
                
                records = []
                async for record in result:
                    entity = record["e"]
                    relationships = record["relationships"]
                    related = record["related_entities"]
                    
                    records.append({
                        "entity": dict(entity),
                        "relationships": [dict(r) for r in relationships if r],
                        "related_entities": [dict(r) for r in related if r],
                    })
                
                return records
        except Exception as e:
            raise RAGError(f"Graph search failed: {str(e)}", stage="search", query=query)
    
    async def query_relationships(
        self,
        project_id: UUID,
        entity: str,
        relationship_type: str = None,
        max_depth: int = 3,
    ) -> List[Dict[str, Any]]:
        """Query relationships for an entity."""
        if not self.driver:
            await self.initialize()
        
        project_id_str = str(project_id)
        
        rel_filter = f":{relationship_type}" if relationship_type else ""
        
        cypher = f"""
            MATCH path = (e1:Entity {{name: $entity, project_id: $project_id}})
            -[r{rel_filter}*1..{max_depth}]-
            (e2:Entity {{project_id: $project_id}})
            RETURN path, e1, e2, r
            LIMIT 100
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, entity=entity, project_id=project_id_str)
                
                records = []
                async for record in result:
                    records.append({
                        "path": [dict(node) for node in record["path"].nodes],
                        "relationships": [dict(rel) for rel in record["path"].relationships],
                    })
                
                return records
        except Exception as e:
            raise RAGError(f"Relationship query failed: {str(e)}", stage="query_relationships")
    
    async def delete_project(self, project_id: UUID) -> bool:
        """Delete all graph data for a project."""
        if not self.driver:
            await self.initialize()
        
        project_id_str = str(project_id)
        
        try:
            async with self.driver.session() as session:
                await session.run("""
                    MATCH (p:Project {project_id: $project_id})
                    OPTIONAL MATCH (p)-[:CONTAINS]->(d:Document)
                    OPTIONAL MATCH (d)-[:MENTIONS]->(e:Entity)
                    OPTIONAL MATCH (e)-[r:RELATES]->()
                    DETACH DELETE p, d, e, r
                """, project_id=project_id_str)
            
            return True
        except Exception as e:
            raise RAGError(f"Failed to delete project: {str(e)}", stage="delete_project")
    
    async def get_project_stats(self, project_id: UUID) -> Dict[str, Any]:
        """Get statistics for a project's graph."""
        if not self.driver:
            await self.initialize()
        
        project_id_str = str(project_id)
        
        try:
            async with self.driver.session() as session:
                # Count entities
                entity_result = await session.run("""
                    MATCH (e:Entity {project_id: $project_id})
                    RETURN count(e) as count
                """, project_id=project_id_str)
                entity_count = (await entity_result.single())["count"]
                
                # Count relationships
                rel_result = await session.run("""
                    MATCH (e1:Entity {project_id: $project_id})-[r:RELATES]->(e2:Entity {project_id: $project_id})
                    RETURN count(r) as count
                """, project_id=project_id_str)
                rel_count = (await rel_result.single())["count"]
                
                # Count documents
                doc_result = await session.run("""
                    MATCH (d:Document {project_id: $project_id})
                    RETURN count(d) as count
                """, project_id=project_id_str)
                doc_count = (await doc_result.single())["count"]
                
                return {
                    "entities_count": entity_count,
                    "relationships_count": rel_count,
                    "documents_count": doc_count,
                }
        except Exception:
            return {"entities_count": 0, "relationships_count": 0, "documents_count": 0}
    
    async def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract entities from content (placeholder)."""
        # This would use NLP or LLM to extract entities
        # For now, return empty list
        return []
    
    async def _extract_relationships(
        self,
        content: str,
        entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract relationships from content (placeholder)."""
        return []
    
    async def close(self):
        """Close the driver."""
        if self.driver:
            await self.driver.close()


from uuid import uuid4

# Global instance
_graph_store: Optional[GraphStore] = None


def get_graph_store() -> GraphStore:
    """Get or create graph store instance."""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
    return _graph_store