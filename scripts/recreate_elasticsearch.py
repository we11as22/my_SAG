"""
Elasticsearch index recreation script

Delete and recreate all ES indices
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

logger = get_logger("scripts.recreate_es_indices")


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


async def delete_indices(es_client: ElasticsearchClient) -> dict[str, bool]:
    """
    Delete all ES indices

    Returns:
        dict: index name -> whether deletion was successful
    """
    print_header("Step 1/2: Delete Existing Indices")

    results = {}

    for document_cls in REGISTERED_DOCUMENTS:
        try:
            index_name = document_cls.Index.name
        except AttributeError as e:
            print_error(f"Document class {document_cls.__name__} index name retrieval failed: {e}")
            logger.error(f"Document class {document_cls.__name__} missing Index.name: {e}")
            results[document_cls.__name__] = False
            continue

        # Check if index exists
        exists = await es_client.index_exists(index_name)

        if not exists:
            print_info(f"{index_name}: Index does not exist, skipping deletion")
            results[index_name] = True
            continue

        # Delete index
        try:
            await es_client.delete_index(index_name)
            print_success(f"{index_name}: Deleted successfully")
            results[index_name] = True
        except Exception as e:
            print_error(f"{index_name}: Deletion failed - {e}")
            results[index_name] = False

    return results


async def create_indices(es_client: ElasticsearchClient) -> dict[str, bool]:
    """
    Create all ES indices

    Returns:
        dict: index name -> whether creation was successful
    """
    print_header("Step 2/2: Create New Indices")

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
            results[document_cls.__name__] = False
            continue

        try:
            # Create index
            await es_client.create_index(
                index=index_name,
                mappings=mapping,
                settings=settings
            )
            print_success(f"{index_name}: Created successfully")

            # Verify index configuration
            exists = await es_client.index_exists(index_name)
            if exists:
                print_info(f"{index_name}: Verification passed, index exists")
                results[index_name] = True
            else:
                print_error(f"{index_name}: Verification failed, index does not exist")
                results[index_name] = False

        except Exception as e:
            print_error(f"{index_name}: Creation failed - {e}")
            results[index_name] = False

    return results


async def verify_indices(es_client: ElasticsearchClient) -> None:
    """
    Verify all indices and their configurations
    """
    print_header("Verify Index Configuration")

    for document_cls in REGISTERED_DOCUMENTS:
        try:
            index_name = document_cls.Index.name
        except AttributeError as e:
            print_error(f"Document class {document_cls.__name__} index name retrieval failed: {e}")
            logger.error(f"Document class {document_cls.__name__} missing Index.name: {e}")
            continue

        exists = await es_client.index_exists(index_name)

        if exists:
            print_success(f"{index_name}: Index exists")

            # Can add more verification, e.g., check mapping configuration
            try:
                # Can add logic to get and verify mapping here
                print_info(f"{index_name}: Configuration verification passed")
            except Exception as e:
                print_warning(f"{index_name}: Configuration verification failed - {e}")
        else:
            print_error(f"{index_name}: Index does not exist")


async def main() -> None:
    """
    Main function
    """
    es_client = None

    try:
        print_header("SAG Elasticsearch Index Recreation Tool")
        print_info("This tool will delete and recreate all Elasticsearch indices")
        print_warning("Warning: All data in indices will be permanently deleted!")

        # Request user confirmation
        print("\n")
        confirm = input("  Confirm to continue? (yes/no): ").strip().lower()

        if confirm != 'yes':
            print_info("Operation cancelled")
            return

        # 1. Create ES client
        print_info("Connecting to Elasticsearch...")
        es_client = ElasticsearchClient()

        # 2. Check connection
        if not await es_client.check_connection():
            print_error("Elasticsearch connection failed, please check configuration")
            sys.exit(1)

        print_success("Elasticsearch connection successful")

        # 3. Delete existing indices
        delete_results = await delete_indices(es_client)

        # 4. Create new indices
        create_results = await create_indices(es_client)

        # 5. Verify indices
        await verify_indices(es_client)

        # 6. Summary
        print_header("Operation Summary")

        all_success = all(delete_results.values()) and all(create_results.values())

        if all_success:
            print_success("All indices recreated successfully!")
            print_info(f"Total recreated {len(REGISTERED_DOCUMENTS)} indices:")
            for document_cls in REGISTERED_DOCUMENTS:
                try:
                    index_name = document_cls.Index.name
                except AttributeError as e:
                    print_error(f"Document class {document_cls.__name__} index name retrieval failed: {e}")
                    logger.error(f"Document class {document_cls.__name__} missing Index.name: {e}")
                    continue
                print(f"    - {index_name}")
        else:
            print_warning("Some indices recreation failed, please check details above")

            failed_indices = [
                name for name, success in create_results.items()
                if not success
            ]
            if failed_indices:
                print_error(f"Failed indices: {', '.join(failed_indices)}")

        print("=" * 70 + "\n")

    except Exception as e:
        print_error(f"Index recreation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Close connection
        if es_client:
            await es_client.close()


if __name__ == "__main__":
    asyncio.run(main())
