
import asyncio
import os
import random
from dotenv import load_dotenv
from src.database.neo4j import Neo4jDB
from src.services.neo4j_service import Neo4jService
from src.models.entities import Entity, EntityType
from src.models.relationships import Relationship, RelationType

# Load environment variables
load_dotenv()

async def init_db():
    print("Connecting to Neo4j...")
    service = Neo4jService()
    try:
        await service.connect()
        print("Connected!")
        
        # Initialize schema (indices)
        await service.create_indices()
        print("Schema initialized.")
        
        # Clear existing data to avoid duplicates
        # print("Clearing existing data...")
        # await service.execute_cypher("MATCH (n) DETACH DELETE n")
        
        # Create Entities
        print("Creating entities...")
        entities = []
        
        # People
        people_data = [
            {"name": "Sarah Chen", "description": "College roommate and best friend"},
            {"name": "Alex Kim", "description": "Study partner and CS lab partner"},
            {"name": "Mike Rodriguez", "description": "High school friend and hiking buddy"},
            {"name": "Grandma Rose", "description": "Beloved grandmother who taught me to cook"},
            {"name": "Lisa Tran", "description": "Colleague and coding mentor"}
        ]
        
        people_ids = {}
        for p in people_data:
            entity = Entity(
                name=p["name"],
                type=EntityType.PERSON,
                description=p["description"]
            )
            eid = await service.create_entity(entity)
            people_ids[p["name"]] = eid
            entities.append(eid)
            print(f"Created person: {p['name']}")

        # Locations
        location_data = [
            {"name": "Stanford University", "description": "Alma mater where I studied computer science"},
            {"name": "Yosemite National Park", "description": "Breathtaking national park with granite cliffs"},
            {"name": "Family Home", "description": "Childhood home in Chicago suburbs"},
            {"name": "San Francisco", "description": "City where I had my first tech internship"},
            {"name": "Paris", "description": "Summer holiday destination"}
        ]
        
        location_ids = {}
        for l in location_data:
            entity = Entity(
                name=l["name"],
                type=EntityType.LOCATION,
                description=l["description"]
            )
            eid = await service.create_entity(entity)
            location_ids[l["name"]] = eid
            entities.append(eid)
            print(f"Created location: {l['name']}")

        # Events
        event_data = [
            {"name": "College Graduation", "description": "Proud moment walking across the stage"},
            {"name": "Half Dome Hike", "description": "Challenging 16-mile hike to the top of Half Dome"},
            {"name": "Learning Grandma's Recipes", "description": "Special time learning family recipes"},
            {"name": "Local Hackathon", "description": "24-hour coding competition with friends"},
            {"name": "Tech Conference 2025", "description": "Annual conference about future tech trends"}
        ]
        
        event_ids = {}
        for e in event_data:
            entity = Entity(
                name=e["name"],
                type=EntityType.EVENT,
                description=e["description"]
            )
            eid = await service.create_entity(entity)
            event_ids[e["name"]] = eid
            entities.append(eid)
            print(f"Created event: {e['name']}")

        # Create Relationships
        print("Creating relationships...")
        
        relationships = [
            (people_ids["Sarah Chen"], event_ids["College Graduation"], RelationType.ATTENDED),
            (people_ids["Alex Kim"], location_ids["Stanford University"], RelationType.LOCATED_AT),
            (event_ids["College Graduation"], location_ids["Stanford University"], RelationType.OCCURRED_AT),
            (people_ids["Mike Rodriguez"], event_ids["Half Dome Hike"], RelationType.ATTENDED),
            (event_ids["Half Dome Hike"], location_ids["Yosemite National Park"], RelationType.OCCURRED_AT),
            (people_ids["Grandma Rose"], event_ids["Learning Grandma's Recipes"], RelationType.ATTENDED),
            (event_ids["Learning Grandma's Recipes"], location_ids["Family Home"], RelationType.OCCURRED_AT),
            (people_ids["Sarah Chen"], people_ids["Alex Kim"], RelationType.KNOWS),
            (people_ids["Grandma Rose"], people_ids["Sarah Chen"], RelationType.KNOWS),
            (people_ids["Lisa Tran"], event_ids["Local Hackathon"], RelationType.ATTENDED),
            (people_ids["Lisa Tran"], event_ids["Tech Conference 2025"], RelationType.ATTENDED),
            (event_ids["Local Hackathon"], location_ids["San Francisco"], RelationType.OCCURRED_AT)
        ]

        for source, target, rel_type in relationships:
            rel = Relationship(
                source_id=source,
                target_id=target,
                type=rel_type,
                confidence_score=1.0
            )
            await service.create_relationship(rel)
            print(f"Created relationship: {rel_type}")

        print("Done! Database populated.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await service.disconnect()

if __name__ == "__main__":
    asyncio.run(init_db())
