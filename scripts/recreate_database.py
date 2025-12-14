"""
Safe database recreation script

Only delete project-related tables and recreate them, protect other tables and alembic version information

Features:
- Only delete project-defined ORM tables (12 tables)
- Protect non-project tables (e.g., other application tables)
- Protect alembic_version version management table
- Recreate project table structures
- Insert default data

Security:
- Use Base.metadata.tables to automatically identify project tables
- Clearly distinguish between project tables and non-project tables
- Detailed logs show operations and protection status
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from sag.db import get_engine, get_session_factory, init_database
from sag.db.base import Base  # Import Base to get project table definitions
from sag.utils import get_logger

logger = get_logger("scripts.recreate_database")


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


async def drop_project_tables() -> None:
    """
    Only delete project-related tables, protect other tables and alembic version information
    """
    logger.info("Starting safe deletion of project tables...")

    project_tables = get_project_tables()
    logger.info(f"Project-defined tables: {sorted(project_tables)}")

    factory = get_session_factory()
    async with factory() as session:
        # Disable foreign key checks
        await session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        # Get all tables in the database
        result = await session.execute(text("SHOW TABLES"))
        all_tables = {row[0] for row in result.fetchall()}

        logger.info(f"Total tables in database: {len(all_tables)}")

        # Find project tables to delete (project tables that exist in database)
        tables_to_drop = []
        protected_tables = []
        
        for table in all_tables:
            if table in project_tables:
                tables_to_drop.append(table)
                logger.info(f"  Preparing to delete project table: {table}")
            else:
                protected_tables.append(table)
                if 'alembic' in table.lower():
                    logger.info(f"  Protecting version management table: {table}")
                else:
                    logger.warning(f"  Protecting non-project table: {table}")

        if not tables_to_drop:
            logger.info("No project tables found to delete")
        else:
            # Delete project tables
            for table in tables_to_drop:
                logger.info(f"  Deleting project table: {table}")
                await session.execute(text(f"DROP TABLE IF EXISTS `{table}`"))

        # Enable foreign key checks
        await session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        await session.commit()

        logger.info(f"✓ Table deletion completed!")
        logger.info(f"  - Deleted {len(tables_to_drop)} project tables")
        logger.info(f"  - Protected {len(protected_tables)} other tables")


async def main() -> None:
    """
    Main function
    """
    try:
        logger.info("=" * 60)
        logger.info("SAG Database Recreation")
        logger.info("=" * 60)

        # 1. Safely delete project tables
        await drop_project_tables()

        # 2. Initialize database (create all tables)
        await init_database()

        # 3. Insert default entity types (called by init_database)
        from scripts.init_database import insert_default_entity_types, verify_database

        await insert_default_entity_types()

        # 4. Verify database
        await verify_database()

        logger.info("=" * 60)
        logger.info("✓ Database recreation successful!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Database recreation failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # Close database connection
        from sag.db.base import close_database

        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
