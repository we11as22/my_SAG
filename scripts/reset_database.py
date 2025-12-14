"""
Reset database and Alembic migration version

Smart reset process:
1. Delete project model-related tables + alembic_version table
2. Check if migration files exist
3. If migration files exist: execute migration directly
4. If no migration files: generate initial migration
5. Execute migration and insert default data
"""
import asyncio
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sag.db import get_session_factory
from sag.db.base import Base
from sag.utils import get_logger

logger = get_logger("reset_database")


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


async def drop_project_and_version_tables():
    """Delete project tables and alembic_version table, protect other tables"""
    logger.info("Starting deletion of project tables and version table...")

    project_tables = get_project_tables()
    logger.info(f"Project-defined tables ({len(project_tables)}): {sorted(project_tables)}")

    factory = get_session_factory()
    async with factory() as session:
        # Disable foreign key checks
        await session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        # Get all tables in the database
        result = await session.execute(text("SHOW TABLES"))
        all_tables = {row[0] for row in result.fetchall()}

        logger.info(f"Total tables in database: {len(all_tables)}")

        # Find tables to delete
        tables_to_drop = []
        protected_tables = []
        
        for table in all_tables:
            # Delete project tables
            if table in project_tables:
                tables_to_drop.append(table)
                logger.info(f"  Preparing to delete project table: {table}")
            # Delete alembic_version table
            elif table == 'alembic_version':
                tables_to_drop.append(table)
                logger.info(f"  Preparing to delete version table: {table}")
            # Protect other tables
            else:
                protected_tables.append(table)
                logger.warning(f"  Protecting non-project table: {table}")

        if not tables_to_drop:
            logger.info("No tables found to delete")
        else:
            # Delete tables
            for table in tables_to_drop:
                logger.info(f"  Deleting table: {table}")
                await session.execute(text(f"DROP TABLE IF EXISTS `{table}`"))

        # Enable foreign key checks
        await session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        await session.commit()

        logger.info(f"✓ Table deletion completed!")
        logger.info(f"  - Deleted {len(tables_to_drop)} tables")
        logger.info(f"  - Protected {len(protected_tables)} other tables")


def check_migration_files() -> bool:
    """Check if migration files exist"""
    versions_dir = project_root / "migrations" / "versions"
    if not versions_dir.exists():
        return False
    
    # Check for .py files (exclude __init__.py and __pycache__)
    migration_files = [
        f for f in versions_dir.glob("*.py") 
        if f.name != "__init__.py"
    ]
    
    return len(migration_files) > 0


def generate_initial_migration():
    """Generate initial migration"""
    logger.info("Generating initial migration...")
    try:
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "initial migration"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("✓ Initial migration generated")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration generation failed: {e.stderr}")
        raise


def run_alembic_upgrade():
    """Execute Alembic migration"""
    logger.info("Executing database migration...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("✓ Database migration completed")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e.stderr}")
        raise


async def main():
    try:
        logger.info("=" * 60)
        logger.info("Reset Database and Alembic Version")
        logger.info("=" * 60)
        
        # 1. Delete project tables and version table
        logger.info("\n[1/4] Deleting project tables and version table...")
        await drop_project_and_version_tables()
        
        # 2. Check if migration files exist
        logger.info("\n[2/4] Checking migration files...")
        has_migrations = check_migration_files()
        
        if has_migrations:
            logger.info("✓ Existing migration files detected, will execute migration directly")
        else:
            logger.info("⚠️  No migration files detected, will generate initial migration")
            generate_initial_migration()
        
        # 3. Execute migration
        logger.info("\n[3/4] Executing database migration...")
        run_alembic_upgrade()
        
        # 4. Insert default data
        logger.info("\n[4/4] Inserting default data...")
        from scripts.init_database import insert_default_entity_types
        await insert_default_entity_types()
        
        logger.info("=" * 60)
        logger.info("✓ Reset completed! Database is ready")
        logger.info("\nVerification command:")
        logger.info("  alembic current")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Reset failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        from sag.db.base import close_database
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
