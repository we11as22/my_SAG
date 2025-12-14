"""
Elasticsearch index initialization script

Create all ES indices and verify
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sag.core.storage.documents import REGISTERED_DOCUMENTS
from sag.core.storage.elasticsearch import ElasticsearchClient
from sag.utils import get_logger

logger = get_logger("scripts.init_es_indices")


# Output helper functions
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


async def create_indices(es_client: ElasticsearchClient) -> dict[str, str]:
    """
    Create all ES indices

    If index already exists, skip creation (idempotency)

    Returns:
        dict: index name -> status ("created", "skipped", "failed")
    """
    print_header("Create Indices")
    logger.info("Starting index creation...")

    results = {}

    for document_cls in REGISTERED_DOCUMENTS:
        try:
            # Get index configuration from Document class
            index_name = document_cls.Index.name
            mapping = document_cls._doc_type.mapping.to_dict()
            settings = getattr(document_cls.Index, "settings", {})
        except AttributeError as e:
            print_error(f"Document class {document_cls.__name__} configuration retrieval failed: {e}")
            logger.error(f"Document class {document_cls.__name__} missing required attributes: {e}")
            results[document_cls.__name__] = "failed"
            continue

        # Check if index already exists
        exists = await es_client.index_exists(index_name)

        if exists:
            print_info(f"{index_name}: Already exists, skipping creation")
            logger.info(f"  - {index_name}: Already exists, skipping creation")
            results[index_name] = "skipped"
            continue

        # Create index
        try:
            print_info(f"{index_name}: Starting creation...")
            logger.info(f"  - {index_name}: Doesn't exist, starting creation")
            await es_client.create_index(
                index=index_name,
                mappings=mapping,
                settings=settings
            )
            print_success(f"{index_name}: Created successfully")
            logger.info(f"  ✓ Index created successfully: {index_name}")
            results[index_name] = "created"
        except Exception as e:
            print_error(f"{index_name}: Creation failed - {e}")
            logger.error(f"  ✗ Index creation failed: {index_name} - {e}")
            results[index_name] = "failed"

    return results


async def verify_indices(es_client: ElasticsearchClient) -> bool:
    """
    Verify all indices are created successfully

    Returns:
        bool: Whether all indices passed verification
    """
    print_header("Verify Indices")
    logger.info("Starting index verification...")

    all_success = True

    for document_cls in REGISTERED_DOCUMENTS:
        try:
            index_name = document_cls.Index.name
        except AttributeError as e:
            print_error(f"Document class {document_cls.__name__} index name retrieval failed: {e}")
            logger.error(f"Document class {document_cls.__name__} missing Index.name: {e}")
            all_success = False
            continue

        exists = await es_client.index_exists(index_name)

        if exists:
            print_success(f"{index_name}: Verification passed")
            logger.info(f"✓ {index_name}: Exists")
        else:
            print_error(f"{index_name}: Verification failed, index does not exist")
            logger.error(f"✗ {index_name}: Does not exist")
            all_success = False

    return all_success


async def main() -> None:
    """
    Main function
    """
    es_client = None

    try:
        print_header("SAG Elasticsearch Index Initialization")
        logger.info("=" * 60)
        logger.info("SAG Elasticsearch Index Initialization")
        logger.info("=" * 60)

        # 1. Create ES client
        print_info("Connecting to Elasticsearch...")
        es_client = ElasticsearchClient()

        # 2. Check connection
        if not await es_client.check_connection():
            print_error("Elasticsearch connection failed, please check configuration")
            raise Exception("ES connection failed, please check configuration")

        print_success("Elasticsearch connection successful")

        # 3. Create indices
        create_results = await create_indices(es_client)

        # 4. Verify indices
        verify_success = await verify_indices(es_client)

        # 5. Summary
        print_header("Operation Summary")

        created_count = sum(1 for status in create_results.values() if status == "created")
        skipped_count = sum(1 for status in create_results.values() if status == "skipped")
        failed_count = sum(1 for status in create_results.values() if status == "failed")

        if created_count > 0:
            print_success(f"Newly created indices: {created_count}")
        if skipped_count > 0:
            print_info(f"Skipped indices: {skipped_count} (already exist)")
        if failed_count > 0:
            print_error(f"Failed indices: {failed_count}")

        if verify_success and failed_count == 0:
            print_success("All indices initialized successfully!")
            logger.info("=" * 60)
            logger.info("✓ Elasticsearch index initialization successful!")
            logger.info("=" * 60)
        else:
            print_error("Some indices initialization failed, please check details")
            raise Exception("Index initialization not fully successful")

        print("=" * 70 + "\n")

    except Exception as e:
        print_error(f"Index initialization failed: {e}")
        logger.error(f"Elasticsearch index initialization failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # Close connection
        if es_client:
            await es_client.close()


if __name__ == "__main__":
    asyncio.run(main())
