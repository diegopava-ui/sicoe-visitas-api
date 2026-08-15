import math
from datetime import date, datetime, time

from app.repositories.tercero_repository import tercero_repository

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import tercero, visita
from app.models.visita import Visita
from app.repositories.usuario_repository import buscar_asesor_activo
from app.repositories.visita_repository import (
        actualizar_visita as actualizar_visita_repository,
        buscar_visita_por_id,
        buscar_visita_por_id_incluyendo_eliminadas,
        contar_visitas,
        desactivar_visita as desactivar_visita_repository,
        guardar_visita,
        listar_visitas as listar_visitas_repository,
        reactivar_visita as reactivar_visita_repository,
)
from app.services.notificacion_programacion_service import programar_notificaciones_visita

from app.schemas.visita import (
    EstadoVisita,
    TipoVisita,
    VisitaActualizar,
    VisitaCrear,
    VisitaListado,
)


def calcular_duracion_minutos(
    hora_inicio: time | None,
    hora_fin: time | None,
) -> int | None:
    if hora_inicio is None or hora_fin is None:
        return None

    fecha_referencia = date.today()

    inicio = datetime.combine(
        fecha_referencia,
        hora_inicio,
    )

    fin = datetime.combine(
        fecha_referencia,
        hora_fin,
    )

    if fin < inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La hora de finalización no puede ser "
                "anterior a la hora de inicio"
            ),
        )

    diferencia = fin - inicio

    return int(
        diferencia.total_seconds() // 60
    )


def validar_proxima_visita(
    fecha_visita: date,
    proxima_visita: date | None,
) -> None:
    if proxima_visita is None:
        return

    if proxima_visita < fecha_visita:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La próxima visita no puede ser anterior "
                "a la fecha de la visita actual"
            ),
        )

TRANSICIONES_ESTADO_PERMITIDAS: dict[str, set[str]] = {
    "PROGRAMADA": {
        "PROGRAMADA",
        "EN_PROCESO",
        "CANCELADA",
    },
    "EN_PROCESO": {
        "EN_PROCESO",
        "FINALIZADA",
        "CANCELADA",
    },
    "FINALIZADA": {
        "FINALIZADA",
    },
    "CANCELADA": {
        "CANCELADA",
        "PROGRAMADA",
    },
}


def validar_transicion_estado(
    estado_actual: str,
    nuevo_estado: str,
) -> None:
    estados_permitidos = TRANSICIONES_ESTADO_PERMITIDAS.get(
        estado_actual,
        set(),
    )

    if nuevo_estado not in estados_permitidos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No es posible cambiar una visita de "
                f"{estado_actual} a {nuevo_estado}"
            ),
        )

        tercero = tercero_repository.get_by_id(
            db,
            data.tercero_id,
        )

        if not tercero:
            raise HTTPException(
                status_code=404,
                detail="El tercero no existe.",
            )

def crear_visita(
    db: Session,
    datos: VisitaCrear,
    usuario_actual_id: int,
) -> Visita:
    asesor = buscar_asesor_activo(
        db,
        datos.asesor_id,
    )

    if asesor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El asesor indicado no existe o está inactivo",
        )

    tercero = tercero_repository.get_by_id(
        db,
        datos.tercero_id,
    )

    if tercero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El tercero indicado no existe o está inactivo",
        )

    validar_proxima_visita(
        fecha_visita=datos.fecha_visita,
        proxima_visita=datos.proxima_visita,
    )

    duracion_calculada = calcular_duracion_minutos(
        hora_inicio=datos.hora_inicio,
        hora_fin=datos.hora_fin,
    )

    datos_visita = datos.model_dump()

    # Compatibilidad temporal con las columnas antiguas de visitas.
    datos_visita["empresa"] = tercero.razon_social
    datos_visita["nit"] = tercero.identificacion

    # Completar información desde el tercero solamente cuando
    # no haya sido enviada expresamente en la visita.
    datos_visita["ciudad"] = (
        datos_visita.get("ciudad")
        or tercero.ciudad
    )

    datos_visita["departamento"] = (
        datos_visita.get("departamento")
        or tercero.departamento
    )

    datos_visita["direccion"] = (
        datos_visita.get("direccion")
        or tercero.direccion
    )

    datos_visita["contacto_nombre"] = (
        datos_visita.get("contacto_nombre")
        or tercero.contacto_nombre
    )

    datos_visita["telefono_contacto"] = (
        datos_visita.get("telefono_contacto")
        or tercero.contacto_telefono
    )

    datos_visita["email_contacto"] = (
        datos_visita.get("email_contacto")
        or tercero.contacto_email
    )

    if duracion_calculada is not None:
        datos_visita["duracion_minutos"] = duracion_calculada

    visita = Visita(
        **datos_visita,
        created_by=usuario_actual_id,
        updated_by=usuario_actual_id,
    )

    try:
        visita_guardada = guardar_visita(
            db,
            visita,
        )
        # La visita debe conservarse aunque no exista consentimiento
        # o no sea posible programar mensajes. El servicio devuelve
        # las omisiones sin interrumpir el registro principal.
        programar_notificaciones_visita(
            db,
            visita_guardada,
        )
        return visita_guardada

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No fue posible crear la visita. "
                "Verifique los datos proporcionados"
            ),
        ) from exc


def obtener_visita(
    db: Session,
    visita_id: int,
) -> Visita:
    visita = buscar_visita_por_id(
        db,
        visita_id,
    )

    if visita is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visita no encontrada",
        )

    return visita


def obtener_visitas(
    db: Session,
    buscar: str | None = None,
    asesor_id: int | None = None,
    tercero_id: int | None = None,
    estado: EstadoVisita | None = None,
    tipo_visita: TipoVisita | None = None,
    servicio: str | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    activo: bool | None = None,
    pagina: int = 1,
    limite: int = 50,
) -> VisitaListado:
    if pagina < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La página debe ser mayor o igual a 1",
        )

    if limite < 1 or limite > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El límite debe estar entre 1 y 100",
        )

    if (
        fecha_inicio is not None
        and fecha_fin is not None
        and fecha_fin < fecha_inicio
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La fecha final no puede ser anterior "
                "a la fecha inicial"
            ),
        )

    if asesor_id is not None:
        asesor = buscar_asesor_activo(
            db,
            asesor_id,
        )

        if asesor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El asesor indicado no existe o está inactivo",
            )

    offset = (pagina - 1) * limite

    resultados = listar_visitas_repository(
        db=db,
        buscar=buscar,
        asesor_id=asesor_id,
        tercero_id=tercero_id,
        estado=estado,
        tipo_visita=tipo_visita,
        servicio=servicio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activo=activo,
        limite=limite,
        offset=offset,
    )

    total = contar_visitas(
        db=db,
        buscar=buscar,
        asesor_id=asesor_id,
        tercero_id=tercero_id,
        estado=estado,
        tipo_visita=tipo_visita,
        servicio=servicio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activo=activo,
    )

    paginas = (
        math.ceil(total / limite)
        if total > 0
        else 0
    )

    return VisitaListado(
        total=total,
        pagina=pagina,
        limite=limite,
        paginas=paginas,
        resultados=resultados,
    )

def actualizar_visita(
    db: Session,
    visita_id: int,
    datos: VisitaActualizar,
    usuario_actual_id: int,
) -> Visita:
    visita = buscar_visita_por_id(
        db,
        visita_id,
    )

    if visita is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visita no encontrada",
        )

    cambios = datos.model_dump(
        exclude_unset=True,
    )

    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se enviaron datos para actualizar",
        )

    campos_obligatorios = {
        "asesor_id",
        "fecha_visita",
        "servicio",
        "tipo_visita",
        "estado",
        "origen_registro",
    }

    campos_nulos = [
        campo
        for campo in campos_obligatorios
        if campo in cambios and cambios[campo] is None
    ]

    if campos_nulos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Los siguientes campos no pueden quedar vacíos: "
                + ", ".join(campos_nulos)
            ),
        )

    if "asesor_id" in cambios:
        asesor = buscar_asesor_activo(
            db,
            cambios["asesor_id"],
        )

    if "tercero_id" in cambios:
        tercero = tercero_repository.get_by_id(
        db,
        cambios["tercero_id"],
    )

    if tercero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El tercero indicado no existe o está inactivo",
        )

    # Mantener sincronizadas las columnas heredadas.
    cambios["empresa"] = tercero.razon_social
    cambios["nit"] = tercero.identificacion  

    if asesor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El asesor indicado no existe o está inactivo",
            )

    if "estado" in cambios:
        validar_transicion_estado(
            estado_actual=visita.estado,
            nuevo_estado=cambios["estado"],
        )

    fecha_resultante = cambios.get(
        "fecha_visita",
        visita.fecha_visita,
    )

    proxima_visita_resultante = cambios.get(
        "proxima_visita",
        visita.proxima_visita,
    )

    validar_proxima_visita(
        fecha_visita=fecha_resultante,
        proxima_visita=proxima_visita_resultante,
    )

    hora_inicio_resultante = cambios.get(
        "hora_inicio",
        visita.hora_inicio,
    )

    hora_fin_resultante = cambios.get(
        "hora_fin",
        visita.hora_fin,
    )

    se_modificaron_horas = (
        "hora_inicio" in cambios
        or "hora_fin" in cambios
    )

    if se_modificaron_horas:
        duracion_calculada = calcular_duracion_minutos(
            hora_inicio=hora_inicio_resultante,
            hora_fin=hora_fin_resultante,
        )

        cambios["duracion_minutos"] = duracion_calculada

    elif (
        "duracion_minutos" in cambios
        and visita.hora_inicio is not None
        and visita.hora_fin is not None
    ):
        cambios["duracion_minutos"] = calcular_duracion_minutos(
            hora_inicio=visita.hora_inicio,
            hora_fin=visita.hora_fin,
        )

    for campo, valor in cambios.items():
        setattr(
            visita,
            campo,
            valor,
        )

    visita.updated_by = usuario_actual_id

    try:
        visita_actualizada = actualizar_visita_repository(
            db,
            visita,
        )
        campos_programacion = {
            "asesor_id",
            "tercero_id",
            "fecha_visita",
            "hora_inicio",
            "estado",
            "telefono_contacto",
        }
        if campos_programacion.intersection(cambios):
            programar_notificaciones_visita(
                db,
                visita_actualizada,
                reemplazar_pendientes=True,
            )
        return visita_actualizada

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No fue posible actualizar la visita. "
                "Verifique los datos proporcionados"
            ),
        ) from exc

def desactivar_visita(
    db: Session,
    visita_id: int,
    usuario_actual_id: int,
) -> Visita:
    visita = buscar_visita_por_id(
        db,
        visita_id,
    )

    if visita is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visita no encontrada",
        )

    if visita.estado == "EN_PROCESO":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se puede desactivar una visita que se "
                "encuentra en proceso"
            ),
        )

    visita.updated_by = usuario_actual_id

    try:
        return desactivar_visita_repository(
            db,
            visita,
        )

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible desactivar la visita",
        ) from exc

def reactivar_visita(
    db: Session,
    visita_id: int,
    usuario_actual_id: int,
) -> Visita:
    visita = buscar_visita_por_id_incluyendo_eliminadas(
        db,
        visita_id,
    )

    if visita is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visita no encontrada",
        )

    if visita.activo and visita.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La visita ya se encuentra activa",
        )

    visita.updated_by = usuario_actual_id

    try:
        return reactivar_visita_repository(
            db,
            visita,
        )

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible reactivar la visita",
        ) from exc