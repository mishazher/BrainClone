
import asyncio
import traceback
from dotenv import load_dotenv
from src.services.neo4j_service import Neo4jService
from src.models.entities import Entity, EntityType

load_dotenv()

async def test_write():
    service = Neo4jService()
    try:
        print("Connecting...", flush=True)
        await service.connect()
        print("Connected!", flush=True)
        
        entity = Entity(name="Test Node", type=EntityType.PERSON, description="A test node")
        print("Creating entity...", flush=True)
        eid = await service.create_entity(entity)
        print(f"Created entity: {eid}", flush=True)
        
    except Exception as e:
        print(f"Error caught: {e}", flush=True)
        traceback.print_exc()
    finally:
        await service.disconnect()

if __name__ == "__main__":
    asyncio.run(test_write())
