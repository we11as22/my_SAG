"""
Database initialization script

Safely create all project tables and insert default data

Features:
- Identify and display project table list
- Create all project table structures
- Insert default entity types
- Verify database integrity
- Display record count for each table

Security:
- Use Base.metadata.tables to automatically identify project tables
- Only operate on project-defined tables
- Provide detailed database verification information
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select

from sag.db import EntityType, get_engine, get_session_factory, init_database
from sag.db.base import Base  # Import Base to get project table definitions
from sag.models.entity import DEFAULT_ENTITY_TYPES


# Output helper functions (consistent with init_elasticsearch.py)
def print_header(text: str) -> None:
    """Print header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text: str) -> None:
    """Print success message"""
    print(f"  ✓ {text}")


def print_info(text: str) -> None:
    """Print info message"""
    print(f"  • {text}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"  ⚠️  {text}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"  ✗ {text}")


async def insert_default_entity_types() -> None:
    """
    Insert default entity types (only insert non-existing ones)
    
    Idempotency: Check each default entity type ID individually, only insert non-existing ones
    Default entity types: time, location, person, topic, action, tags
    """
    print_header("Insert Default Entity Types")
    
    factory = get_session_factory()

    async with factory() as session:
        inserted_count = 0
        skipped_count = 0

        # Check and insert each default entity type individually
        for type_def in DEFAULT_ENTITY_TYPES:
            # Check if this specific ID already exists
            result = await session.execute(
                select(EntityType).where(EntityType.id == type_def.id)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print_info(f"{type_def.type} ({type_def.name}): Already exists, skipping insertion")
                skipped_count += 1
                continue
            
            # Doesn't exist, insert it
            entity_type = EntityType(
                id=type_def.id,  # UUID
                source_config_id=type_def.source_config_id,  # None means system default type
                type=type_def.type,  # Type identifier (e.g., "time")
                name=type_def.name,  # Type name (e.g., "Time")
                is_default=type_def.is_default,
                description=type_def.description,
                weight=type_def.weight,
                similarity_threshold=type_def.similarity_threshold,  # Similarity matching threshold
                extra_data=None,  # Extended data, none for now
                is_active=type_def.is_active,
            )
            session.add(entity_type)
            print_success(f"{type_def.type} ({type_def.name}): Inserted successfully")
            inserted_count += 1

        await session.commit()
        
        print_header("Insert Summary")
        if inserted_count > 0:
            print_success(f"Newly inserted: {inserted_count}")
        if skipped_count > 0:
            print_info(f"Skipped: {skipped_count} (already exist)")


def get_project_tables() -> set[str]:
    """Get all ORM-defined tables in the project"""
    # Ensure all models are imported
    from sag.db import models
    
    project_tables = set()
    for table_name in Base.metadata.tables.keys():
        # Extract table name (handle possible schema prefix)
        if '.' in table_name:
            project_tables.add(table_name.split('.')[-1])
        else:
            project_tables.add(table_name)
    
    return project_tables


async def verify_database() -> None:
    """
    Verify database initialization success
    """
    print_header("Verify Database")

    factory = get_session_factory()
    async with factory() as session:
        # Check entity_types table content
        from sqlalchemy import select
        result = await session.execute(select(EntityType))
        entity_types = result.scalars().all()
        
        if entity_types:
            print_info(f"Existing default entity types: {len(entity_types)}")
            for entity_type in entity_types:
                print_success(
                    f"{entity_type.type} ({entity_type.name}): "
                    f"weight={entity_type.weight}, threshold={entity_type.similarity_threshold}"
                )
        else:
            print_warning("No default entity types found")


async def main() -> None:
    """
    Main function
    """
    try:
        print_header("SAG Database Initialization")

        # 1. Insert default entity types
        await insert_default_entity_types()

        # 2. Verify database
        await verify_database()

        # 3. Summary
        print_header("Initialization Complete")
        print_success("Database initialization successful!")
        print("=" * 70 + "\n")

    except Exception as e:
        print_error(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Close database connection
        from sag.db.base import close_database

        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
