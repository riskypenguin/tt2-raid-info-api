from typing import Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from src.domain.seed_data_repository import SeedDataRepository
from src.model.raid_data import RaidSeedDataEnhanced, RaidSeedDataRaw
from src.model.seed_type import SeedType
from src.scripts.enhance_seeds import enhance_seed_data
from src.utils.get_env import get_env
from src.utils.responses import RESPONSE_STANDARD_NOT_FOUND
from src.utils.sort_order import SortOrder
from src.utils.stream_response import create_stream_response

ENV_AUTH_SECRET = get_env(key='AUTH_SECRET')
# ENV_STAGE = get_env('STAGE')

DISPLAY_IN_DOCS = True  # ENV_STAGE != Stage.PRODUCTION.value if ENV_STAGE else False


def _verify_authorization(*, secret: Optional[str]):
    if not secret or secret != ENV_AUTH_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to make this request.")


def _factory_list_seed_identifiers(*, repo: SeedDataRepository):

    async def list_seed_identifiers(
        seed_type: SeedType,
        *,
        sort_order: Optional[SortOrder] = SortOrder.ASCENDING,
    ) -> Tuple[str]:
        return repo.list_seed_identifiers(seed_type=seed_type,
                                          sort_order=sort_order)

    return list_seed_identifiers


def _factory_download_seed_file(*, repo: SeedDataRepository):

    async def download_seed_file(seed_type: SeedType,
                                 identifier: str) -> StreamingResponse:

        data = repo.get_seed_by_identifier(identifier=identifier,
                                           seed_type=seed_type)

        if data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{seed_type.value} seed {identifier} does not exist")

        return create_stream_response(data=data, filename=f"{identifier}.json")

    return download_seed_file


def _factory_enhance_seed():

    async def enhance_seed(
        *,
        download: bool = False,
        data: List[RaidSeedDataRaw],
    ) -> Union[StreamingResponse, List[RaidSeedDataEnhanced]]:

        enhanced_seed_data = enhance_seed_data(data=data)

        if download:
            return create_stream_response(data=enhanced_seed_data,
                                          filename="enhanced_custom_seed.json")

        return enhanced_seed_data

    return enhance_seed


def _factory_save_seed(*, repo: SeedDataRepository):

    async def save_seed(
        identifier: str,
        *,
        data: List[RaidSeedDataRaw],
        secret: Optional[str] = Header(None)) -> Dict:

        _verify_authorization(secret=secret)

        enhanced = enhance_seed_data(data=data)

        payload = (
            (identifier, SeedType.RAW, data),
            (identifier, SeedType.ENHANCED, enhanced),
        )

        success = repo.save_seeds(items=payload)

        if success is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to seed '{identifier}', it might already exist")

        return {
            "detail": f"Saved seed '{identifier}'",
            "identifier": identifier,
            "success": success,
        }

    return save_seed


def _factory_delete_seed(*, repo: SeedDataRepository):

    async def delete_seed(identifier: str,
                          *,
                          secret: Optional[str] = Header(None)) -> Dict:
        _verify_authorization(secret=secret)

        payload = (
            (identifier, SeedType.RAW),
            (identifier, SeedType.ENHANCED),
        )

        success = repo.delete_seeds(items=payload)

        if success is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete '{identifier}', it might not exist")

        return {
            "detail": f"Deleted seed '{identifier}'",
            "identifier": identifier,
            "success": success,
        }

    return delete_seed


def create_router(seed_data_repo: SeedDataRepository):

    router = APIRouter(
        prefix="/admin",
        tags=["Admin"],
        responses=RESPONSE_STANDARD_NOT_FOUND,
    )

    router.add_api_route(
        path="/seed_identifiers/{seed_type}",
        methods=["get"],
        endpoint=_factory_list_seed_identifiers(repo=seed_data_repo),
        include_in_schema=DISPLAY_IN_DOCS)

    router.add_api_route(
        path="/seed/{seed_type}/{identifier}",
        methods=["get"],
        endpoint=_factory_download_seed_file(repo=seed_data_repo),
        include_in_schema=DISPLAY_IN_DOCS)

    router.add_api_route(path="/enhance",
                         methods=["post"],
                         endpoint=_factory_enhance_seed(),
                         include_in_schema=DISPLAY_IN_DOCS)

    router.add_api_route(path="/save/{identifier}",
                         methods=["post"],
                         status_code=status.HTTP_201_CREATED,
                         endpoint=_factory_save_seed(repo=seed_data_repo),
                         include_in_schema=DISPLAY_IN_DOCS)

    router.add_api_route(path="/delete/{identifier}",
                         methods=["delete"],
                         endpoint=_factory_delete_seed(repo=seed_data_repo),
                         include_in_schema=DISPLAY_IN_DOCS)

    return router
