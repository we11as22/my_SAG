"""信息源服务"""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from sag.api.schemas.source import SourceConfigResponse
from sag.db.models import SourceConfig, Article, EntityType


class SourceService:
    """Source service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_source(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> SourceConfigResponse:
        """Create source"""
        try:
            source = SourceConfig(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                config=config or {},
            )

            self.db.add(source)
            await self.db.flush()  # Flush to get the ID, but don't commit yet
            await self.db.refresh(source)
            # Note: commit is handled by get_db() dependency

            return SourceConfigResponse.model_validate(source)
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Error creating source: {e}")
            print(traceback.format_exc())
            raise

    async def get_source(self, source_config_id: str) -> Optional[SourceConfigResponse]:
        """Get source"""
        result = await self.db.execute(
            select(SourceConfig).where(SourceConfig.id == source_config_id)
        )
        source = result.scalar_one_or_none()

        if source:
            return SourceConfigResponse.model_validate(source)
        return None

    async def list_sources(
        self,
        page: int = 1,
        page_size: int = 20,
        name_filter: Optional[str] = None,
    ) -> Tuple[List[SourceConfigResponse], int]:
        """Get source list (including document count and entity type count)"""
        # Subquery: Count documents for each source (all statuses)
        document_count_subq = (
            select(
                Article.source_config_id,
                func.count(Article.id).label("document_count")
            )
            .group_by(Article.source_config_id)
            .subquery()
        )

        # Subquery: Count source-specific entity types (exclude global types)
        entity_types_count_subq = (
            select(
                EntityType.source_config_id,
                func.count(EntityType.id).label("entity_types_count")
            )
            .where(EntityType.source_config_id.isnot(None))  # Only count source-specific types, exclude global types where source_config_id is NULL
            .group_by(EntityType.source_config_id)
            .subquery()
        )

        # Main query: Get source information and JOIN two statistical subqueries
        query = (
            select(
                SourceConfig,
                func.coalesce(document_count_subq.c.document_count, 0).label("document_count"),
                func.coalesce(entity_types_count_subq.c.entity_types_count, 0).label("entity_types_count")
            )
            .outerjoin(document_count_subq, SourceConfig.id == document_count_subq.c.source_config_id)
            .outerjoin(entity_types_count_subq, SourceConfig.id == entity_types_count_subq.c.source_config_id)
        )

        if name_filter:
            query = query.where(SourceConfig.name.like(f"%{name_filter}%"))

        # Get total count (number of sources)
        count_query = select(func.count()).select_from(SourceConfig)
        if name_filter:
            count_query = count_query.where(SourceConfig.name.like(f"%{name_filter}%"))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Pagination and sorting
        query = query.order_by(SourceConfig.created_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        rows = result.all()

        # Build response
        sources = []
        for source, document_count, entity_types_count in rows:
            source_dict = {
                "id": source.id,
                "name": source.name,
                "description": source.description,
                "config": source.config,
                "created_time": source.created_time,
                "updated_time": source.updated_time,
                "document_count": document_count,
                "entity_types_count": entity_types_count,
            }
            sources.append(SourceConfigResponse.model_validate(source_dict))

        return sources, total

    async def update_source(
        self,
        source_config_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Optional[SourceConfigResponse]:
        """Update source"""
        result = await self.db.execute(
            select(SourceConfig).where(SourceConfig.id == source_config_id)
        )
        source = result.scalar_one_or_none()

        if not source:
            return None

        if name is not None:
            source.name = name
        if description is not None:
            source.description = description
        if config is not None:
            source.config = config

        await self.db.flush()  # Flush changes, commit is handled by get_db()
        await self.db.refresh(source)

        return SourceConfigResponse.model_validate(source)

    async def delete_source(self, source_config_id: str) -> bool:
        """Delete source"""
        result = await self.db.execute(
            select(SourceConfig).where(SourceConfig.id == source_config_id)
        )
        source = result.scalar_one_or_none()

        if not source:
            return False

        await self.db.delete(source)
        # Note: commit is handled by get_db() dependency

        return True

