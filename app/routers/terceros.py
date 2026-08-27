from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams
from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.tercero import (
    TerceroCreate,
    TerceroResponse,
    TerceroUpdate,
)
from app.services.tercero_service import (
    actualizar_tercero,
    buscar_terceros,
    crear_tercero,
    eliminar_tercero,
    listar_terceros,
    listar_terceros_por_tipo,
    obtener_tercero,
    reactivar_tercero,
)


FiltroEstadoTercero = Literal[
    "TODOS",
    "ACTIVOS",
    "INACTIVOS",
]


router = APIRouter(
    prefix="/api/v1/terceros",
    tags=["Terceros"],
)


@router.get(
    "/",
    response_model=PaginatedResponse[TerceroResponse],
)
def get_terceros(
    pagination: Annotated[PaginationParams, Depends()],
    estado: FiltroEstadoTercero = Query(
        "TODOS",
        description="Filtra por TODOS, ACTIVOS o INACTIVOS.",
    ),
    db: Session = Depends(get_db),
):
    return listar_terceros(
        db=db,
        pagina=pagination.pagina,
        limite=pagination.limite,
        estado=estado,
    )


@router.get(
    "/buscar",
    response_model=list[TerceroResponse],
)
def search_terceros(
    texto: str = Query(..., min_length=2),
    estado: FiltroEstadoTercero = Query(
        "TODOS",
        description="Filtra por TODOS, ACTIVOS o INACTIVOS.",
    ),
    db: Session = Depends(get_db),
):
    return buscar_terceros(
        db,
        texto,
        estado=estado,
    )


@router.get(
    "/tipo/{tipo_tercero}",
    response_model=list[TerceroResponse],
)
def get_terceros_por_tipo(
    tipo_tercero: str,
    db: Session = Depends(get_db),
):
    return listar_terceros_por_tipo(
        db,
        tipo_tercero,
    )


@router.post(
    "/",
    response_model=TerceroResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_tercero(
    data: TerceroCreate,
    db: Session = Depends(get_db),
):
    return crear_tercero(db, data)


@router.get(
    "/{tercero_id}",
    response_model=TerceroResponse,
)
def get_tercero(
    tercero_id: int,
    db: Session = Depends(get_db),
):
    return obtener_tercero(db, tercero_id)


@router.put(
    "/{tercero_id}",
    response_model=TerceroResponse,
)
def put_tercero(
    tercero_id: int,
    data: TerceroUpdate,
    db: Session = Depends(get_db),
):
    return actualizar_tercero(
        db,
        tercero_id,
        data,
    )


@router.delete(
    "/{tercero_id}",
    response_model=TerceroResponse,
)
def delete_tercero(
    tercero_id: int,
    db: Session = Depends(get_db),
):
    return eliminar_tercero(
        db,
        tercero_id,
    )


@router.patch(
    "/{tercero_id}/reactivar",
    response_model=TerceroResponse,
)
def patch_reactivar_tercero(
    tercero_id: int,
    db: Session = Depends(get_db),
):
    return reactivar_tercero(
        db,
        tercero_id,
    )
