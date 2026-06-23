
import asyncio
import os
from dotenv import load_dotenv
from src.services.neo4j_service import Neo4jService

load_dotenv()

async def check_count():
    service = Neo4jService()
    try:
        await service.connect()
        # Count all nodes
        nodes = await service.execute_cypher("MATCH (n) RETURN count(n) as count")
        print(f"Total Nodes: {nodes[0]['count']}")
        
        # Count relationships
        rels = await service.execute_cypher("MATCH ()-[r]->() RETURN count(r) as count")
        print(f"Total Relationships: {rels[0]['count']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await service.disconnect()

if __name__ == "__main__":
    asyncio.run(check_count())
