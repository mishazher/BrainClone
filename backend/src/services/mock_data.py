"""Mock data service for BrainClone demo - brings memories to life!"""

import random
from typing import List, Dict, Any
from datetime import datetime, timedelta

class MockDataService:
    """Service that provides sample memory data for BrainClone demo"""
    
    def __init__(self):
        self.memories = self._generate_sample_memories()
        self.relationships = self._generate_relationships()
    
    def _generate_sample_memories(self) -> List[Dict[str, Any]]:
        """Generate multiple networks of sample memories - people, places, and moments"""
        return [
            # === COLLEGE NETWORK ===
            {
                "id": "person_sarah",
                "name": "Sarah Chen",
                "type": "person",
                "category": "Person",
                "description": "College roommate and best friend",
                "confidence_score": 0.95,
                "metadata": {
                    "age": 28,
                    "occupation": "Software Engineer",
                    "location": "San Francisco",
                    "relationship": "close_friend",
                    "network": "college"
                }
            },
            {
                "id": "person_alex",
                "name": "Alex Kim",
                "type": "person",
                "category": "Person",
                "description": "Study partner and CS lab partner",
                "confidence_score": 0.90,
                "metadata": {
                    "age": 27,
                    "occupation": "Data Scientist",
                    "location": "Seattle",
                    "relationship": "friend",
                    "network": "college"
                }
            },
            {
                "id": "person_prof_wilson",
                "name": "Professor Wilson",
                "type": "person",
                "category": "Person",
                "description": "Computer Science professor and mentor",
                "confidence_score": 0.88,
                "metadata": {
                    "age": 45,
                    "occupation": "Professor",
                    "location": "Stanford",
                    "relationship": "mentor",
                    "network": "college"
                }
            },
            {
                "id": "place_college",
                "name": "Stanford University",
                "type": "location",
                "category": "Location",
                "description": "Alma mater where I studied computer science",
                "confidence_score": 0.94,
                "metadata": {
                    "country": "USA",
                    "state": "California",
                    "type": "university",
                    "graduation_year": 2018,
                    "network": "college"
                }
            },
            {
                "id": "place_cs_lab",
                "name": "Computer Science Lab",
                "type": "location",
                "category": "Location",
                "description": "Late night coding sessions with Alex",
                "confidence_score": 0.89,
                "metadata": {
                    "building": "Gates Computer Science",
                    "type": "academic",
                    "network": "college"
                }
            },
            {
                "id": "event_graduation",
                "name": "College Graduation",
                "type": "event",
                "category": "Event",
                "description": "Proud moment walking across the stage",
                "confidence_score": 0.99,
                "metadata": {
                    "date": "2018-06-15",
                    "type": "milestone",
                    "importance": "high",
                    "network": "college"
                }
            },
            {
                "id": "event_final_project",
                "name": "Senior Capstone Project",
                "type": "event",
                "category": "Event",
                "description": "Built an AI-powered study app with Alex",
                "confidence_score": 0.92,
                "metadata": {
                    "date": "2018-05-01",
                    "type": "academic",
                    "project": "AI Study App",
                    "network": "college"
                }
            },

            # === ADVENTURE NETWORK ===
            {
                "id": "person_mike",
                "name": "Mike Rodriguez",
                "type": "person", 
                "category": "Person",
                "description": "High school friend and hiking buddy",
                "confidence_score": 0.92,
                "metadata": {
                    "age": 29,
                    "occupation": "Photographer",
                    "location": "Denver",
                    "relationship": "friend",
                    "network": "adventure"
                }
            },
            {
                "id": "person_emma",
                "name": "Emma Thompson",
                "type": "person",
                "category": "Person",
                "description": "Rock climbing instructor and adventure partner",
                "confidence_score": 0.87,
                "metadata": {
                    "age": 26,
                    "occupation": "Outdoor Guide",
                    "location": "Boulder",
                    "relationship": "friend",
                    "network": "adventure"
                }
            },
            {
                "id": "place_yosemite",
                "name": "Yosemite National Park",
                "type": "location",
                "category": "Location",
                "description": "Breathtaking national park with granite cliffs and waterfalls",
                "confidence_score": 0.96,
                "metadata": {
                    "country": "USA",
                    "state": "California",
                    "type": "national_park",
                    "visited_date": "2023-06-15",
                    "network": "adventure"
                }
            },
            {
                "id": "place_rocky_mountains",
                "name": "Rocky Mountain National Park",
                "type": "location",
                "category": "Location",
                "description": "Stunning mountain landscapes and alpine lakes",
                "confidence_score": 0.91,
                "metadata": {
                    "country": "USA",
                    "state": "Colorado",
                    "type": "national_park",
                    "visited_date": "2023-08-20",
                    "network": "adventure"
                }
            },
            {
                "id": "place_climbing_gym",
                "name": "Boulder Rock Club",
                "type": "location",
                "category": "Location",
                "description": "Indoor climbing gym where I learned to climb",
                "confidence_score": 0.85,
                "metadata": {
                    "type": "recreation",
                    "network": "adventure"
                }
            },
            {
                "id": "event_hiking",
                "name": "Half Dome Hike",
                "type": "event",
                "category": "Event",
                "description": "Challenging 16-mile hike to the top of Half Dome",
                "confidence_score": 0.93,
                "metadata": {
                    "date": "2023-06-15",
                    "type": "adventure",
                    "difficulty": "extreme",
                    "duration": "12_hours",
                    "network": "adventure"
                }
            },
            {
                "id": "event_rock_climbing",
                "name": "First Outdoor Climb",
                "type": "event",
                "category": "Event",
                "description": "Learned outdoor climbing with Emma in Rocky Mountains",
                "confidence_score": 0.89,
                "metadata": {
                    "date": "2023-08-20",
                    "type": "adventure",
                    "route": "Beginner's Route",
                    "network": "adventure"
                }
            },

            # === FAMILY NETWORK ===
            {
                "id": "person_grandma",
                "name": "Grandma Rose",
                "type": "person",
                "category": "Person", 
                "description": "Beloved grandmother who taught me to cook",
                "confidence_score": 0.98,
                "metadata": {
                    "age": 78,
                    "occupation": "Retired Teacher",
                    "location": "Chicago",
                    "relationship": "family",
                    "network": "family"
                }
            },
            {
                "id": "person_dad",
                "name": "Dad",
                "type": "person",
                "category": "Person",
                "description": "Supportive father who taught me to fish",
                "confidence_score": 0.97,
                "metadata": {
                    "age": 55,
                    "occupation": "Engineer",
                    "location": "Chicago",
                    "relationship": "family",
                    "network": "family"
                }
            },
            {
                "id": "person_mom",
                "name": "Mom",
                "type": "person",
                "category": "Person",
                "description": "Loving mother and family historian",
                "confidence_score": 0.98,
                "metadata": {
                    "age": 52,
                    "occupation": "Teacher",
                    "location": "Chicago",
                    "relationship": "family",
                    "network": "family"
                }
            },
            {
                "id": "place_family_home",
                "name": "Family Home",
                "type": "location",
                "category": "Location",
                "description": "Childhood home in Chicago suburbs",
                "confidence_score": 0.95,
                "metadata": {
                    "country": "USA",
                    "state": "Illinois",
                    "type": "residential",
                    "network": "family"
                }
            },
            {
                "id": "place_lake_michigan",
                "name": "Lake Michigan",
                "type": "location",
                "category": "Location",
                "description": "Beautiful lake where Dad taught me to fish",
                "confidence_score": 0.90,
                "metadata": {
                    "country": "USA",
                    "state": "Illinois",
                    "type": "natural",
                    "network": "family"
                }
            },
            {
                "id": "event_cooking",
                "name": "Learning Grandma's Recipes",
                "type": "event",
                "category": "Event",
                "description": "Special time learning family recipes and stories",
                "confidence_score": 0.96,
                "metadata": {
                    "date": "2021-12-25",
                    "type": "family_tradition",
                    "recipes_learned": ["apple_pie", "chicken_soup"],
                    "network": "family"
                }
            },
            {
                "id": "event_fishing",
                "name": "First Fishing Trip",
                "type": "event",
                "category": "Event",
                "description": "Dad taught me to fish at Lake Michigan",
                "confidence_score": 0.94,
                "metadata": {
                    "date": "2010-07-15",
                    "type": "family_bonding",
                    "caught": "3 fish",
                    "network": "family"
                }
            },

            # === TRAVEL NETWORK ===
            {
                "id": "person_travel_buddy",
                "name": "Jake Martinez",
                "type": "person",
                "category": "Person",
                "description": "Travel companion and backpacking partner",
                "confidence_score": 0.88,
                "metadata": {
                    "age": 30,
                    "occupation": "Freelance Writer",
                    "location": "Nomadic",
                    "relationship": "friend",
                    "network": "travel"
                }
            },
            {
                "id": "place_paris",
                "name": "Paris, France",
                "type": "location",
                "category": "Location",
                "description": "City of lights - romantic trip with Sarah",
                "confidence_score": 0.97,
                "metadata": {
                    "country": "France",
                    "type": "city",
                    "visited_date": "2022-09-20",
                    "network": "travel"
                }
            },
            {
                "id": "place_tokyo",
                "name": "Tokyo, Japan",
                "type": "location",
                "category": "Location",
                "description": "Amazing city with Jake - neon lights and sushi",
                "confidence_score": 0.93,
                "metadata": {
                    "country": "Japan",
                    "type": "city",
                    "visited_date": "2023-03-10",
                    "network": "travel"
                }
            },
            {
                "id": "place_iceland",
                "name": "Reykjavik, Iceland",
                "type": "location",
                "category": "Location",
                "description": "Northern lights and hot springs adventure",
                "confidence_score": 0.91,
                "metadata": {
                    "country": "Iceland",
                    "type": "city",
                    "visited_date": "2023-11-15",
                    "network": "travel"
                }
            },
            {
                "id": "event_paris_trip",
                "name": "Paris Adventure",
                "type": "event",
                "category": "Event",
                "description": "Amazing week exploring Paris with Sarah",
                "confidence_score": 0.95,
                "metadata": {
                    "date": "2022-09-20",
                    "type": "travel",
                    "duration": "7_days",
                    "highlights": ["eiffel_tower", "louvre", "croissants"],
                    "network": "travel"
                }
            },
            {
                "id": "event_tokyo_backpacking",
                "name": "Tokyo Backpacking",
                "type": "event",
                "category": "Event",
                "description": "Two weeks exploring Tokyo with Jake",
                "confidence_score": 0.90,
                "metadata": {
                    "date": "2023-03-10",
                    "type": "travel",
                    "duration": "14_days",
                    "highlights": ["sushi", "temples", "neon_lights"],
                    "network": "travel"
                }
            },
            {
                "id": "event_northern_lights",
                "name": "Northern Lights Hunt",
                "type": "event",
                "category": "Event",
                "description": "Magical night watching aurora borealis in Iceland",
                "confidence_score": 0.96,
                "metadata": {
                    "date": "2023-11-15",
                    "type": "travel",
                    "duration": "5_days",
                    "highlights": ["aurora", "hot_springs", "volcanoes"],
                    "network": "travel"
                }
            },

            # === WORK NETWORK ===
            {
                "id": "person_boss",
                "name": "Lisa Chen",
                "type": "person",
                "category": "Person",
                "description": "Inspiring manager and career mentor",
                "confidence_score": 0.89,
                "metadata": {
                    "age": 35,
                    "occupation": "Engineering Manager",
                    "location": "San Francisco",
                    "relationship": "professional",
                    "network": "work"
                }
            },
            {
                "id": "person_teammate",
                "name": "David Park",
                "type": "person",
                "category": "Person",
                "description": "Collaborative teammate and coding partner",
                "confidence_score": 0.86,
                "metadata": {
                    "age": 26,
                    "occupation": "Software Engineer",
                    "location": "San Francisco",
                    "relationship": "colleague",
                    "network": "work"
                }
            },
            {
                "id": "place_office",
                "name": "Tech Startup Office",
                "type": "location",
                "category": "Location",
                "description": "Modern office with great views of the city",
                "confidence_score": 0.88,
                "metadata": {
                    "country": "USA",
                    "state": "California",
                    "type": "office",
                    "network": "work"
                }
            },
            {
                "id": "event_product_launch",
                "name": "Product Launch Success",
                "type": "event",
                "category": "Event",
                "description": "Successfully launched our AI product with the team",
                "confidence_score": 0.92,
                "metadata": {
                    "date": "2023-10-15",
                    "type": "professional",
                    "product": "AI Assistant",
                    "network": "work"
                }
            },
            {
                "id": "event_team_retreat",
                "name": "Team Building Retreat",
                "type": "event",
                "category": "Event",
                "description": "Amazing team retreat in Napa Valley",
                "confidence_score": 0.87,
                "metadata": {
                    "date": "2023-07-20",
                    "type": "professional",
                    "location": "Napa Valley",
                    "network": "work"
                }
            }
        ]
    
    def _generate_relationships(self) -> List[Dict[str, Any]]:
        """Generate relationships between memories across multiple networks"""
        return [
            # === COLLEGE NETWORK RELATIONSHIPS ===
            {
                "source": "person_sarah",
                "target": "event_graduation", 
                "type": "ATTENDED",
                "strength": 0.9,
                "description": "Sarah attended my graduation"
            },
            {
                "source": "person_alex",
                "target": "event_final_project",
                "type": "COLLABORATED_ON",
                "strength": 0.95,
                "description": "Built the AI study app together"
            },
            {
                "source": "person_prof_wilson",
                "target": "event_final_project",
                "type": "MENTORED",
                "strength": 0.88,
                "description": "Professor Wilson mentored our project"
            },
            {
                "source": "person_alex",
                "target": "place_cs_lab",
                "type": "STUDIED_AT",
                "strength": 0.92,
                "description": "Late night coding sessions together"
            },
            {
                "source": "event_graduation",
                "target": "place_college",
                "type": "OCCURRED_AT",
                "strength": 1.0,
                "description": "Graduation ceremony at Stanford"
            },
            {
                "source": "event_final_project",
                "target": "place_cs_lab",
                "type": "DEVELOPED_AT",
                "strength": 0.94,
                "description": "Project developed in the CS lab"
            },

            # === ADVENTURE NETWORK RELATIONSHIPS ===
            {
                "source": "person_mike",
                "target": "event_hiking",
                "type": "HIKED_WITH",
                "strength": 0.92,
                "description": "Hiked Half Dome together"
            },
            {
                "source": "person_emma",
                "target": "event_rock_climbing",
                "type": "INSTRUCTED",
                "strength": 0.89,
                "description": "Emma taught me outdoor climbing"
            },
            {
                "source": "person_emma",
                "target": "place_climbing_gym",
                "type": "WORKS_AT",
                "strength": 0.87,
                "description": "Emma works at the climbing gym"
            },
            {
                "source": "event_hiking",
                "target": "place_yosemite",
                "type": "OCCURRED_AT",
                "strength": 1.0,
                "description": "Half Dome hike in Yosemite"
            },
            {
                "source": "event_rock_climbing",
                "target": "place_rocky_mountains",
                "type": "OCCURRED_AT",
                "strength": 1.0,
                "description": "First outdoor climb in Rocky Mountains"
            },
            {
                "source": "person_mike",
                "target": "place_yosemite",
                "type": "PHOTOGRAPHED",
                "strength": 0.88,
                "description": "Photographed the beautiful landscapes"
            },

            # === FAMILY NETWORK RELATIONSHIPS ===
            {
                "source": "person_grandma",
                "target": "event_cooking",
                "type": "TAUGHT",
                "strength": 0.98,
                "description": "Taught me family recipes"
            },
            {
                "source": "person_dad",
                "target": "event_fishing",
                "type": "TAUGHT",
                "strength": 0.96,
                "description": "Dad taught me to fish"
            },
            {
                "source": "person_mom",
                "target": "event_graduation",
                "type": "ATTENDED",
                "strength": 0.99,
                "description": "Mom attended my graduation"
            },
            {
                "source": "event_cooking",
                "target": "place_family_home",
                "type": "OCCURRED_AT",
                "strength": 1.0,
                "description": "Cooking lessons at family home"
            },
            {
                "source": "event_fishing",
                "target": "place_lake_michigan",
                "type": "OCCURRED_AT",
                "strength": 1.0,
                "description": "Fishing trip at Lake Michigan"
            },
            {
                "source": "person_dad",
                "target": "place_lake_michigan",
                "type": "TAUGHT_AT",
                "strength": 0.94,
                "description": "Dad taught me to fish at the lake"
            },

            # === TRAVEL NETWORK RELATIONSHIPS ===
            {
                "source": "person_sarah",
                "target": "event_paris_trip",
                "type": "TRAVELED_WITH",
                "strength": 0.95,
                "description": "Traveled to Paris together"
            },
            {
                "source": "person_travel_buddy",
                "target": "event_tokyo_backpacking",
                "type": "BACKPACKED_WITH",
                "strength": 0.93,
                "description": "Backpacked through Tokyo together"
            },
            {
                "source": "person_travel_buddy",
                "target": "event_northern_lights",
                "type": "EXPLORED_WITH",
                "strength": 0.91,
                "description": "Explored Iceland together"
            },
            {
                "source": "event_paris_trip",
                "target": "place_paris",
                "type": "OCCURRED_AT",
                "strength": 1.0,
                "description": "Paris adventure in the city"
            },
            {
                "source": "event_tokyo_backpacking",
                "target": "place_tokyo",
                "type": "OCCURRED_AT",
                "strength": 1.0,
                "description": "Tokyo backpacking adventure"
            },
            {
                "source": "event_northern_lights",
                "target": "place_iceland",
                "type": "OCCURRED_AT",
                "strength": 1.0,
                "description": "Northern lights hunt in Iceland"
            },

            # === WORK NETWORK RELATIONSHIPS ===
            {
                "source": "person_boss",
                "target": "event_product_launch",
                "type": "LED",
                "strength": 0.92,
                "description": "Lisa led the product launch"
            },
            {
                "source": "person_teammate",
                "target": "event_product_launch",
                "type": "CONTRIBUTED_TO",
                "strength": 0.89,
                "description": "David contributed to the product"
            },
            {
                "source": "person_boss",
                "target": "event_team_retreat",
                "type": "ORGANIZED",
                "strength": 0.87,
                "description": "Lisa organized the team retreat"
            },
            {
                "source": "event_product_launch",
                "target": "place_office",
                "type": "LAUNCHED_FROM",
                "strength": 1.0,
                "description": "Product launched from the office"
            },
            {
                "source": "person_teammate",
                "target": "place_office",
                "type": "WORKS_AT",
                "strength": 0.91,
                "description": "David works at the office"
            },

            # === CROSS-NETWORK RELATIONSHIPS ===
            {
                "source": "person_sarah",
                "target": "person_mike",
                "type": "INTRODUCED_TO",
                "strength": 0.85,
                "description": "Introduced Sarah to Mike"
            },
            {
                "source": "person_grandma",
                "target": "person_sarah",
                "type": "MET",
                "strength": 0.82,
                "description": "Grandma met Sarah at graduation"
            },
            {
                "source": "person_sarah",
                "target": "place_paris",
                "type": "VISITED",
                "strength": 0.94,
                "description": "Visited Paris together"
            },
            {
                "source": "person_grandma",
                "target": "place_college",
                "type": "PROUD_OF",
                "strength": 0.96,
                "description": "Proud of my college achievement"
            },
            {
                "source": "person_sarah",
                "target": "person_travel_buddy",
                "type": "INTRODUCED_TO",
                "strength": 0.78,
                "description": "Introduced Sarah to Jake"
            },
            {
                "source": "person_mike",
                "target": "person_emma",
                "type": "INTRODUCED_TO",
                "strength": 0.81,
                "description": "Introduced Mike to Emma"
            },
            {
                "source": "person_alex",
                "target": "person_teammate",
                "type": "COLLABORATED_WITH",
                "strength": 0.83,
                "description": "Alex and David collaborated on projects"
            },
            {
                "source": "person_boss",
                "target": "person_prof_wilson",
                "type": "CONNECTED_TO",
                "strength": 0.79,
                "description": "Lisa connected through academic network"
            }
        ]
    
    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Get all memory entities"""
        return self.memories
    
    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships between memories"""
        return self.relationships
    
    def get_graph_data(self) -> Dict[str, Any]:
        """Get formatted graph data for visualization"""
        nodes = []
        links = []
        
        # Convert memories to nodes
        for memory in self.memories:
            node = {
                "id": memory["id"],
                "name": memory["name"],
                "type": memory["type"],
                "val": 1,
                "color": self._get_node_color(memory["type"]),
                "metadata": {
                    "description": memory["description"],
                    "category": memory["category"],
                    "confidence": memory["confidence_score"]
                }
            }
            nodes.append(node)
        
        # Convert relationships to links
        for rel in self.relationships:
            link = {
                "source": rel["source"],
                "target": rel["target"],
                "relationship": rel["type"],
                "strength": rel["strength"]
            }
            links.append(link)
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    def _get_node_color(self, node_type: str) -> str:
        """Get color for node type"""
        colors = {
            "person": "#3B82F6",      # Blue for people
            "location": "#10B981",    # Green for places  
            "event": "#F59E0B"        # Orange for events
        }
        return colors.get(node_type, "#6B7280")  # Gray default
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search through memories"""
        query_lower = query.lower()
        results = []
        
        for memory in self.memories:
            if (query_lower in memory["name"].lower() or 
                query_lower in memory["description"].lower()):
                results.append(memory)
        
        return results
