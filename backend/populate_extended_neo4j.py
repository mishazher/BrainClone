
import asyncio
import os
import random
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.database.neo4j import Neo4jDB
from src.services.neo4j_service import Neo4jService
from src.models.entities import Entity, EntityType, Person, Event, Location
from src.models.relationships import Relationship, RelationType

# Load environment variables
load_dotenv()

# Helper function to generate a random date within a range
def random_date(start_year=2020, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# Helper function to create a unique ID for our tracking maps
def generate_key(name):
    return name.lower().replace(" ", "_")

async def init_extended_db():
    print("Connecting to Neo4j for extended population...")
    service = Neo4jService()
    try:
        await service.connect()
        print("Connected!")

        # Initialize schema (indices) just in case
        await service.create_indices()
        
        # NOTE: We are NOT clearing existing data to simply append to it, 
        # or you could choose to clear if you want a fresh start.
        # Uncomment the line below to clear everything before starting:
        # await service.execute_cypher("MATCH (n) DETACH DELETE n")

        print("Generating extended dataset...")
        entities = []
        
        # --- 1. PEOPLE (25 Entities) ---
        people_names = [
            "Emma Thompson", "James Wilson", "Olivia Davies", "Liam Patel", "Sophia Garcia",
            "Noah Martinez", "Ava Robinson", "William Lee", "Isabella Clark", "Lucas Rodriguez",
            "Mia Lewis", "Benjamin Walker", "Charlotte Hall", "Henry Young", "Amelia Allen",
            "Alexander King", "Harper Scott", "Sebastian Green", "Evelyn Baker", "Jack Adams",
            "Abigail Nelson", "Daniel Carter", "Emily Mitchell", "Michael Perez", "Elizabeth Roberts"
        ]
        
        people_map = {} # name -> neo4j_id
        
        for name in people_names:
            person = Person(
                name=name,
                type=EntityType.PERSON,
                description=f"Synthetic person profile for {name}.",
                email=f"{name.lower().replace(' ', '.')}@example.com",
                occupation=random.choice(["Software Engineer", "Data Scientist", "Product Manager", "Designer", "Student", "Researcher"]),
                nationality=random.choice(["USA", "UK", "Canada", "Australia", "Germany", "France"]),
                birth_date=random_date(1980, 2000)
            )
            eid = await service.create_entity(person)
            people_map[name] = eid
            entities.append(eid)
            # print(f"Created person: {name}") # Reduce noise

        print(f"Created {len(people_names)} people.")

        # --- 2. LOCATIONS (20 Entities) ---
        location_names = [
            "Central Park", "Golden Gate Bridge", "Eiffel Tower", "Sydney Opera House", "Colosseum",
            "Statue of Liberty", "Louvre Museum", "Times Square", "Grand Canyon", "Great Wall of China",
            "Machu Picchu", "Taj Mahal", "Mount Fuji", "Santorini", "Petra",
            "Yellowstone National Park", "Disneyland", "Burj Khalifa", "Acropolis", "Stonehenge"
        ]
        
        locations_map = {} # name -> neo4j_id

        for name in location_names:
            location = Location(
                name=name,
                type=EntityType.LOCATION,
                description=f"Famous landmark: {name}",
                city=random.choice(["New York", "San Francisco", "Paris", "Sydney", "Rome", "London", "Tokyo"]),
                country="Unknown" # Simplified
            )
            eid = await service.create_entity(location)
            locations_map[name] = eid
            entities.append(eid)
        
        print(f"Created {len(location_names)} locations.")

        # --- 3. EVENTS (25 Entities) ---
        event_names = [
            "Tech Summit 2024", "AI Revolution Conference", "Global Hackathon", "Summer Music Festival", "Art Gallery Opening",
            "Marathon 2024", "Startup Pitch Night", "Science Fair", "Book Club Meeting", "Coding Bootcamp Graduation",
            "Product Launch", "Charity Gala", "Film Festival", "Food and Wine Expo", "Gaming Championship",
            "Yoga Retreat", "Photography Workshop", "Investment Summit", "Climate Change Conference", "Robotics Competition",
            "Cybersecurity Forum", "Web Development Workshop", "Data Science Meetup", "Blockchain Summit", "Cloud Computing Expo"
        ]
        
        events_map = {} # name -> neo4j_id

        for name in event_names:
            event = Event(
                name=name,
                type=EntityType.EVENT,
                description=f"An exciting event: {name}",
                start_date=random_date(2024, 2025),
                event_type=random.choice(["Conference", "Meetup", "Workshop", "Festival", "Competition"])
            )
            eid = await service.create_entity(event)
            events_map[name] = eid
            entities.append(eid)

        print(f"Created {len(event_names)} events.")

        # --- 4. RELATIONSHIPS ---
        print("Creating random relationships...")
        relationships_count = 0

        # Connect People to Events (ATTENDED)
        # Each person attends 2-5 random events
        for person_name, person_id in people_map.items():
            attended_events = random.sample(event_names, k=random.randint(2, 5))
            for event_name in attended_events:
                event_id = events_map[event_name]
                rel = Relationship(
                    source_id=person_id,
                    target_id=event_id,
                    type=RelationType.ATTENDED,
                    confidence_score=0.9
                )
                await service.create_relationship(rel)
                relationships_count += 1

        # Connect Events to Locations (OCCURRED_AT)
        # Each event happens at 1 random location
        for event_name, event_id in events_map.items():
            location_name = random.choice(location_names)
            location_id = locations_map[location_name]
            rel = Relationship(
                source_id=event_id,
                target_id=location_id,
                type=RelationType.OCCURRED_AT,
                confidence_score=0.95
            )
            await service.create_relationship(rel)
            relationships_count += 1

        # Connect People to Locations (VISITED / LIVED_IN)
        # Each person has visited or lived in 1-3 locations
        for person_name, person_id in people_map.items():
            locs = random.sample(location_names, k=random.randint(1, 3))
            for loc_name in locs:
                loc_id = locations_map[loc_name]
                rtype = random.choice([RelationType.VISITED, RelationType.LIVED_IN])
                rel = Relationship(
                    source_id=person_id,
                    target_id=loc_id,
                    type=rtype,
                    confidence_score=0.8
                )
                await service.create_relationship(rel)
                relationships_count += 1

        # Connect People to People (KNOWS / FRIEND_OF / COLLEAGUE_OF)
        # Each person knows 2-4 other people
        for person_name, person_id in people_map.items():
            others = [p for p in people_names if p != person_name]
            friends = random.sample(others, k=random.randint(2, 4))
            for friend_name in friends:
                friend_id = people_map[friend_name]
                # Avoid duplicate reverse relationships ideally, but for noise it's fine
                rtype = random.choice([RelationType.KNOWS, RelationType.FRIEND_OF, RelationType.COLLEAGUE_OF])
                rel = Relationship(
                    source_id=person_id,
                    target_id=friend_id,
                    type=rtype,
                    confidence_score=0.85
                )
                await service.create_relationship(rel)
                relationships_count += 1

        print(f"Created {relationships_count} relationships.")
        print("Extended database population complete!")

    except Exception as e:
        print(f"Error during population: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await service.disconnect()

if __name__ == "__main__":
    asyncio.run(init_extended_db())
