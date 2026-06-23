
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

# Data Banks for Synthetic Generation
FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Oliver", "Isabella", "Elijah", "Sophia", "Lucas",
    "Mia", "Mason", "Charlotte", "Logan", "Amelia", "Alexander", "Harper", "Ethan", "Evelyn", "Jacob",
    "Abigail", "Michael", "Emily", "Daniel", "Elizabeth", "Henry", "Sofia", "Jackson", "Avery", "Sebastian",
    "Ella", "Aiden", "Scarlett", "Matthew", "Grace", "Samuel", "Chloe", "David", "Victoria", "Joseph",
    "Riley", "Carter", "Aria", "Owen", "Lily", "Wyatt", "Aubrey", "John", "Zoey", "Jack"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
]

LOCATIONS_PREFIX = ["Grand", "Central", "North", "South", "East", "West", "New", "Old", "Silicon", "Golden"]
LOCATIONS_SUFFIX = ["Park", "Valley", "Center", "Square", "Plaza", "Heights", "Beach", "Bay", "Garden", "Campus"]
CITIES = ["San Francisco", "New York", "London", "Tokyo", "Berlin", "Paris", "Toronto", "Sydney", "Singapore", "Austin"]

EVENT_TOPICS = ["AI", "Blockchain", "Cloud Computing", "Design", "Marketing", "Sustainability", "Gaming", "Music", "Film", "Science"]
EVENT_TYPES = ["Conference", "Summit", "Meetup", "Hackathon", "Festival", "Workshop", "Gala", "Expo"]

def generate_random_person():
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    desc = f"A {random.choice(['software engineer', 'designer', 'student', 'artist', 'entrepreneur'])} interested in {random.choice(EVENT_TOPICS)}."
    return {"name": name, "description": desc, "type": EntityType.PERSON}

def generate_random_location():
    if random.random() < 0.3:
        name = random.choice(CITIES)
    else:
        name = f"{random.choice(LOCATIONS_PREFIX)} {random.choice(LOCATIONS_SUFFIX)}"
    
    desc = f"A popular destination for {random.choice(['tourists', 'locals', 'techies', 'artists'])}."
    return {"name": name, "description": desc, "type": EntityType.LOCATION}

def generate_random_event():
    name = f"{random.choice(LOCATIONS_PREFIX)} {random.choice(EVENT_TOPICS)} {random.choice(EVENT_TYPES)} 2025"
    desc = f"Waitlist-only event focusing on {random.choice(EVENT_TOPICS).lower()} innovations."
    return {"name": name, "description": desc, "type": EntityType.EVENT}

async def init_db():
    print("Connecting to Neo4j...")
    service = Neo4jService()
    try:
        await service.connect()
        print("Connected!")
        
        # Initialize schema (indices)
        await service.create_indices()
        print("Schema initialized.")
        
        # Lists to keep track of created IDs for relationship building
        created_people = []
        created_locations = []
        created_events = []

        # --- GENERATION CONFIG ---
        NUM_PEOPLE = 40
        NUM_LOCATIONS = 15
        NUM_EVENTS = 20
        # -------------------------

        # Create People
        print(f"Generating {NUM_PEOPLE} people...")
        for _ in range(NUM_PEOPLE):
            p_data = generate_random_person()
            entity = Entity(
                name=p_data["name"],
                type=p_data["type"],
                description=p_data["description"]
            )
            eid = await service.create_entity(entity)
            created_people.append(eid)
            # print(f"Created Person: {p_data['name']}")

        # Create Locations
        print(f"Generating {NUM_LOCATIONS} locations...")
        for _ in range(NUM_LOCATIONS):
            l_data = generate_random_location()
            entity = Entity(
                name=l_data["name"],
                type=l_data["type"],
                description=l_data["description"]
            )
            eid = await service.create_entity(entity)
            created_locations.append(eid)
            # print(f"Created Location: {l_data['name']}")

        # Create Events
        print(f"Generating {NUM_EVENTS} events...")
        for _ in range(NUM_EVENTS):
            e_data = generate_random_event()
            entity = Entity(
                name=e_data["name"],
                type=e_data["type"],
                description=e_data["description"]
            )
            eid = await service.create_entity(entity)
            created_events.append(eid)
            # print(f"Created Event: {e_data['name']}")

        # Create Relationships
        print("Linking entities with relationships...")
        
        rel_count = 0

        # Person -> Person (KNOWS)
        for person_id in created_people:
            # Each person knows 1-5 other people
            num_friends = random.randint(1, 5)
            friends = random.sample(created_people, num_friends) # Sample with replacement? No, sample returns unique elements
            for friend_id in friends:
                if person_id == friend_id: continue
                
                rel = Relationship(
                    source_id=person_id,
                    target_id=friend_id,
                    type=RelationType.KNOWS,
                    confidence_score=round(random.uniform(0.5, 1.0), 2)
                )
                await service.create_relationship(rel)
                rel_count += 1

        # Person -> Event (ATTENDED)
        for person_id in created_people:
            # Each person attended 0-3 events
            num_events = random.randint(0, 3)
            events_attended = random.sample(created_events, num_events)
            for event_id in events_attended:
                rel = Relationship(
                    source_id=person_id,
                    target_id=event_id,
                    type=RelationType.ATTENDED,
                    confidence_score=round(random.uniform(0.8, 1.0), 2)
                )
                await service.create_relationship(rel)
                rel_count += 1

        # Event -> Location (OCCURRED_AT)
        # Each event must have one location
        for event_id in created_events:
            location_id = random.choice(created_locations)
            rel = Relationship(
                source_id=event_id,
                target_id=location_id,
                type=RelationType.OCCURRED_AT,
                confidence_score=1.0
            )
            await service.create_relationship(rel)
            rel_count += 1
            
        # Person -> Location (LOCATED_AT) - e.g. lives in or is currently at
        for person_id in created_people:
            if random.random() < 0.7: # 70% chance to have a location set
                location_id = random.choice(created_locations)
                rel = Relationship(
                    source_id=person_id,
                    target_id=location_id,
                    type=RelationType.LOCATED_AT,
                    confidence_score=round(random.uniform(0.6, 0.9), 2)
                )
                await service.create_relationship(rel)
                rel_count += 1

        print(f"Done! Created {len(created_people)} people, {len(created_locations)} locations, {len(created_events)} events, and {rel_count} relationships.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await service.disconnect()

if __name__ == "__main__":
    asyncio.run(init_db())
