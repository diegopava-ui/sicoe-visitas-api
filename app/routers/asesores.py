from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asesor import Asesor
from app.schemas.asesor import (
    AsesorActualizar,
    AsesorCrear,
    AsesorRespuesta,
)

router = APIRouter(
    prefix="/api/v1/asesores",
    tags=["Asesores"],
)


@router.get("", response_model=list[AsesorRespuesta])
def listar_asesores(
    buscar: str | None = Query(default=None),
    limite: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Asesor]:
    consulta = select(Asesor).where(Asesor.deleted_at.is_(None))

    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(
            or_(
                Asesor.identificacion.ilike(patron),
                Asesor.primer_nombre.ilike(patron),
                Asesor.primer_apellido.ilike(patron),
                Asesor.email.ilike(patron),
            )
        )

    consulta = consulta.order_by(Asesor.id).offset(offset).limit(limite)

    return list(db.scalars(consulta).all())


@router.get("/{asesor_id}", response_model=AsesorRespuesta)
def obtener_asesor(
    asesor_id: int,
    db: Session = Depends(get_db),
) -> Asesor:
    asesor = db.scalar(
        select(Asesor).where(
            Asesor.id == asesor_id,
            Asesor.deleted_at.is_(None),
        )
    )

    if asesor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asesor no encontrado",
        )

    return asesor


@router.post(
    "",
    response_model=AsesorRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_asesor(
    datos: AsesorCrear,
    db: Session = Depends(get_db),
) -> Asesor:
    asesor = Asesor(**datos.model_dump())
    db.add(asesor)

    try:
        db.commit()
        db.refresh(asesor)
        return asesor
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La identificación o el correo ya están registrados",
        ) from exc

@router.put("/{asesor_id}", response_model=AsesorRespuesta)
def actualizar_asesor(
    asesor_id: int,
    datos: AsesorActualizar,
    db: Session = Depends(get_db),
) -> Asesor:
    asesor = db.scalar(
        select(Asesor).where(
            Asesor.id == asesor_id,
            Asesor.deleted_at.is_(None),
        )
    )

    if asesor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asesor no encontrado",
        )

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(asesor, campo, valor)

    try:
        db.commit()
        db.refresh(asesor)
        return asesor
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La identificación o el correo ya están registrados",
        ) from exc
    
@router.delete(
    "/{asesor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_asesor(
    asesor_id: int,
    db: Session = Depends(get_db),
) -> Response:
    asesor = db.scalar(
        select(Asesor).where(
            Asesor.id == asesor_id,
            Asesor.deleted_at.is_(None),
        )
    )

    if asesor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asesor no encontrado",
        )

    ahora = datetime.now(timezone.utc)

    asesor.activo = False
    asesor.deleted_at = ahora
    asesor.updated_at = ahora

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)    