from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tercero import Tercero
from app.repositories.tercero_repository import tercero_repository
from app.schemas.tercero import TerceroCreate, TerceroUpdate
from app.services.geocodificacion_service import geocodificar


TIPOS_TERCERO_PERMITIDOS = {
    "cliente",
    "proveedor",
    "prospecto",
    "aliado",
    "contratista",
    "otro",
}

ESTADOS_FILTRO_TERCERO = {
    "TODOS",
    "ACTIVOS",
    "INACTIVOS",
}

# Campos que, si cambian, ameritan volver a geocodificar.
_CAMPOS_UBICACION = {"direccion", "ciudad", "departamento"}


def normalizar_texto(valor: str | None) -> str | None:
    if valor is None:
        return None

    valor_limpio = valor.strip()
    return valor_limpio if valor_limpio else None


def normalizar_tipo_tercero(tipo_tercero: str) -> str:
    tipo_normalizado = tipo_tercero.strip().lower()

    if tipo_normalizado not in TIPOS_TERCERO_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El tipo de tercero no es válido. "
                f"Valores permitidos: {sorted(TIPOS_TERCERO_PERMITIDOS)}"
            ),
        )

    return tipo_normalizado


def normalizar_filtro_estado(estado: str) -> str:
    estado_normalizado = estado.strip().upper()

    if estado_normalizado not in ESTADOS_FILTRO_TERCERO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El filtro de estado no es válido. "
                "Valores permitidos: TODOS, ACTIVOS, INACTIVOS."
            ),
        )

    return estado_normalizado


def listar_terceros(
    db: Session,
    pagina: int = 1,
    limite: int = 20,
    estado: str = "TODOS",
) -> dict:
    estado_normalizado = normalizar_filtro_estado(estado)
    offset = (pagina - 1) * limite

    terceros = tercero_repository.list_by_estado(
        db,
        estado=estado_normalizado,
        offset=offset,
        limit=limite,
    )

    total = tercero_repository.count_by_estado(
        db,
        estado=estado_normalizado,
    )

    total_paginas = ceil(total / limite) if total > 0 else 0

    return {
        "items": terceros,
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": total_paginas,
    }


def obtener_tercero(
    db: Session,
    tercero_id: int,
) -> Tercero:
    tercero = tercero_repository.get_by_id(db, tercero_id)

    if tercero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tercero no encontrado.",
        )

    return tercero


def obtener_tercero_incluyendo_inactivos(
    db: Session,
    tercero_id: int,
) -> Tercero:
    tercero = tercero_repository.get_by_id(
        db,
        tercero_id,
        incluir_inactivos=True,
    )

    if tercero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tercero no encontrado.",
        )

    return tercero


def listar_terceros_por_tipo(
    db: Session,
    tipo_tercero: str,
) -> list[Tercero]:
    tipo_normalizado = normalizar_tipo_tercero(tipo_tercero)

    return tercero_repository.get_by_tipo(
        db,
        tipo_normalizado,
    )


def buscar_terceros(
    db: Session,
    texto: str,
    estado: str = "TODOS",
) -> list[Tercero]:
    texto_limpio = texto.strip()
    estado_normalizado = normalizar_filtro_estado(estado)

    if len(texto_limpio) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La búsqueda debe contener al menos 2 caracteres.",
        )

    return tercero_repository.search(
        db,
        texto_limpio,
        estado=estado_normalizado,
    )


def crear_tercero(
    db: Session,
    data: TerceroCreate,
) -> Tercero:
    identificacion = data.identificacion.strip()

    if not identificacion:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La identificación es obligatoria.",
        )

    existente = tercero_repository.get_by_identificacion_including_deleted(
        db,
        identificacion,
    )

    if existente:
        if existente.deleted_at is not None or not existente.activo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Ya existe un tercero inactivo con esta identificación. "
                    "Debe reactivarse en lugar de crear uno nuevo."
                ),
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un tercero con esta identificación.",
        )

    tipo_normalizado = normalizar_tipo_tercero(data.tipo_tercero)

    direccion_normalizada = normalizar_texto(data.direccion)
    ciudad_normalizada = normalizar_texto(data.ciudad)
    departamento_normalizado = normalizar_texto(data.departamento)

    # Geocodificación automática: nunca lanza excepción,
    # si falla simplemente deja lat/long en None.
    latitud, longitud, fuente_ubicacion = geocodificar(
        direccion_normalizada,
        ciudad_normalizada,
        departamento_normalizado,
    )

    datos_normalizados = data.model_copy(
        update={
            "tipo_tercero": tipo_normalizado,
            "tipo_identificacion": data.tipo_identificacion.strip().upper(),
            "identificacion": identificacion,
            "razon_social": data.razon_social.strip(),
            "nombre_comercial": normalizar_texto(data.nombre_comercial),
            "telefono": normalizar_texto(data.telefono),
            "direccion": direccion_normalizada,
            "ciudad": ciudad_normalizada,
            "departamento": departamento_normalizado,
            "latitud": latitud,
            "longitud": longitud,
            "fuente_ubicacion": fuente_ubicacion,
            "contacto_nombre": normalizar_texto(data.contacto_nombre),
            "contacto_telefono": normalizar_texto(data.contacto_telefono),
            "observaciones": normalizar_texto(data.observaciones),
        }
    )

    try:
        return tercero_repository.create(db, datos_normalizados)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No fue posible crear el tercero porque existen datos duplicados."
            ),
        )


def actualizar_tercero(
    db: Session,
    tercero_id: int,
    data: TerceroUpdate,
) -> Tercero:
    tercero = obtener_tercero(db, tercero_id)
    cambios = data.model_dump(exclude_unset=True)

    if "tipo_tercero" in cambios:
        cambios["tipo_tercero"] = normalizar_tipo_tercero(
            cambios["tipo_tercero"]
        )

    if "tipo_identificacion" in cambios:
        cambios["tipo_identificacion"] = (
            cambios["tipo_identificacion"].strip().upper()
        )

    if "identificacion" in cambios:
        nueva_identificacion = cambios["identificacion"].strip()

        existente = (
            tercero_repository.get_by_identificacion_including_deleted(
                db,
                nueva_identificacion,
            )
        )

        if existente and existente.id != tercero_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe otro tercero con esta identificación.",
            )

        cambios["identificacion"] = nueva_identificacion

    campos_texto = {
        "razon_social",
        "nombre_comercial",
        "telefono",
        "direccion",
        "ciudad",
        "departamento",
        "contacto_nombre",
        "contacto_telefono",
        "observaciones",
    }

    for campo in campos_texto:
        if campo in cambios:
            cambios[campo] = normalizar_texto(cambios[campo])

    # Si cambió dirección, ciudad o departamento, volvemos
    # a geocodificar usando los valores finales (los nuevos
    # si vienen en la actualización, o los que ya tenía el
    # tercero si ese campo puntual no cambió).
    if _CAMPOS_UBICACION & cambios.keys():
        direccion_efectiva = cambios.get(
            "direccion", tercero.direccion
        )
        ciudad_efectiva = cambios.get(
            "ciudad", tercero.ciudad
        )
        departamento_efectivo = cambios.get(
            "departamento", tercero.departamento
        )

        latitud, longitud, fuente_ubicacion = geocodificar(
            direccion_efectiva,
            ciudad_efectiva,
            departamento_efectivo,
        )

        cambios["latitud"] = latitud
        cambios["longitud"] = longitud
        cambios["fuente_ubicacion"] = fuente_ubicacion

    datos_actualizacion = TerceroUpdate(**cambios)

    try:
        return tercero_repository.update(
            db,
            tercero,
            datos_actualizacion,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible actualizar el tercero.",
        )


def eliminar_tercero(
    db: Session,
    tercero_id: int,
) -> Tercero:
    tercero = obtener_tercero(db, tercero_id)
    return tercero_repository.soft_delete(db, tercero)


def reactivar_tercero(
    db: Session,
    tercero_id: int,
) -> Tercero:
    tercero = obtener_tercero_incluyendo_inactivos(db, tercero_id)

    if tercero.activo and tercero.deleted_at is None:
        return tercero

    return tercero_repository.reactivate(db, tercero)
