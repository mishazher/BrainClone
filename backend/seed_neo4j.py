"""Seed Neo4j from data/graph_data.json.

WARNING: this WIPES all existing nodes/relationships in the target Neo4j
database and replaces them with the contents of data/graph_data.json.

Run from the backend/ directory:
    python seed_neo4j.py
Neo4j connection comes from env vars / .env (NEO4J_URI, NEO4J_USER, ...).
"""

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from src.services.neo4j_service import Neo4jService
from src.models.entities import Entity, EntityType
from src.models.relationships import Relationship, RelationType

load_dotenv()

DATA_FILE = Path(__file__).parent / "data" / "graph_data.json"


def load_data() -> tuple[list[dict], list[dict]]:
    """Load entities and relationships from the JSON data file."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    if not entities:
        raise ValueError(f"No entities found in {DATA_FILE}")
    return entities, relationships


async def seed() -> None:
    entities_data, rels_data = load_data()
    print(f"Loaded {len(entities_data)} entities and {len(rels_data)} relationships from {DATA_FILE.name}")

    service = Neo4jService()
    try:
        await service.connect()
        print("Connected to Neo4j.")

        # --- WIPE: replace all current data ---
        print("Wiping all existing nodes and relationships...")
        await service.execute_cypher("MATCH (n) DETACH DELETE n")

        await service.create_indices()
        print("Schema (indices) ensured.")

        # --- Create entities, mapping local 'key' -> generated UUID ---
        key_to_id: dict[str, str] = {}
        for raw in entities_data:
            try:
                etype = EntityType(str(raw["type"]).lower())
            except ValueError as exc:
                raise ValueError(
                    f"Entity '{raw.get('name', raw.get('key'))}' has invalid type "
                    f"'{raw.get('type')}'. {exc}"
                ) from exc

            entity = Entity(
                type=etype,
                name=raw["name"],
                description=raw.get("description"),
                tags=raw.get("tags", []),
                properties=raw.get("properties", {}),
                confidence_score=raw.get("confidence_score", 1.0),
            )
            eid = await service.create_entity(entity)

            key = str(raw.get("key") or raw["name"])
            if key in key_to_id:
                raise ValueError(f"Duplicate entity key '{key}' in {DATA_FILE.name}")
            key_to_id[key] = eid
        print(f"Created {len(key_to_id)} entities.")

        # --- Create relationships, resolving keys to ids ---
        rel_count = 0
        for raw in rels_data:
            src = key_to_id.get(str(raw["source"]))
            tgt = key_to_id.get(str(raw["target"]))
            if not src or not tgt:
                print(
                    f"  ! Skipping relationship {raw.get('source')} -[{raw.get('type')}]-> "
                    f"{raw.get('target')}: unknown entity key"
                )
                continue
            try:
                rtype = RelationType(str(raw["type"]).lower())
            except ValueError as exc:
                raise ValueError(
                    f"Relationship {raw.get('source')}->{raw.get('target')} has invalid "
                    f"type '{raw.get('type')}'. {exc}"
                ) from exc

            rel = Relationship(
                source_id=src,
                target_id=tgt,
                type=rtype,
                weight=raw.get("weight", 1.0),
                confidence_score=raw.get("confidence_score", 1.0),
                properties=raw.get("properties", {}),
            )
            await service.create_relationship(rel)
            rel_count += 1

        print(f"Created {rel_count} relationships.")
        print("Done. Neo4j now contains only your data.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(seed())
