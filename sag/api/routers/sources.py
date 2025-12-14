"""Source management API

Provides CRUD operations for sources
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from sag.api.deps import get_db
from sag.api.schemas.common import PaginatedResponse, SuccessResponse
from sag.api.schemas.source import (
    SourceConfigCreateRequest,
    SourceConfigResponse,
    SourceConfigUpdateRequest,
)
from sag.api.services.source_service import SourceService

router = APIRouter()


@router.post(
    "/sources",
    response_model=SuccessResponse[SourceConfigResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_source(
    request: SourceConfigCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create source

    **Features**:
    - Create new source
    - Auto-generate unique ID
    - Initialize default configuration

    **Parameters**:
    - name: Source name (required)
    - description: Description
    - config: Preference settings, e.g., {"focus": ["AI"], "language": "zh"}
    """
    service = SourceService(db)
    source = await service.create_source(
        name=request.name,
        description=request.description,
        config=request.config,
    )
    return SuccessResponse(data=source, message="Source created successfully")


@router.get("/sources", response_model=PaginatedResponse[SourceConfigResponse])
async def list_sources(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Name filter"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get source list

    **Features**:
    - Paginated source query
    - Support name fuzzy search
    """
    service = SourceService(db)
    sources, total = await service.list_sources(
        page=page,
        page_size=page_size,
        name_filter=name,
    )
    return PaginatedResponse.create(
        data=sources,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sources/{source_config_id}", response_model=SuccessResponse[SourceConfigResponse])
async def get_source(
    source_config_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get source details

    **Parameters**:
    - source_config_id: Source ID
    """
    service = SourceService(db)
    source = await service.get_source(source_config_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_config_id}",
        )
    return SuccessResponse(data=source)


@router.patch("/sources/{source_config_id}", response_model=SuccessResponse[SourceConfigResponse])
async def update_source(
    source_config_id: str,
    request: SourceConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update source

    **Parameters**:
    - source_config_id: Source ID
    - name: New name (optional)
    - description: New description (optional)
    - config: New configuration (optional)
    """
    service = SourceService(db)
    source = await service.update_source(
        source_config_id=source_config_id,
        name=request.name,
        description=request.description,
        config=request.config,
    )
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_config_id}",
        )
    return SuccessResponse(data=source, message="Source updated successfully")


@router.delete("/sources/{source_config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_config_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete source

    **Note**:
    - Will cascade delete all data under this source
    - Including articles, events, entities, etc.
    - This operation is irreversible

    **Parameters**:
    - source_config_id: Source ID
    """
    service = SourceService(db)
    success = await service.delete_source(source_config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_config_id}",
        )

