import re
import unicodedata
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asesor import Asesor
from app.models.usuario import Usuario
from app.services.calendario_service import listar_eventos
from app.schemas.agenda_agente import (
    AgendaAgenteRespuesta,
    AgendaAgenteVisita,
)


ZONA_COLOMBIA = ZoneInfo("America/Bogota")

ROLES_SUPERVISOR = (
    "ADMINISTRADOR",
    "COORDINADOR",
)

# Sentinel usado como "titular" cuando la consulta abarca
# a todos los asesores (equipo completo), en vez de a un
# asesor puntual. No es un id real de asesor.
TITULAR_EQUIPO = "EQUIPO"

_MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

_PATRON_FECHA_TEXTUAL = re.compile(
    r"\b(\d{1,2})\s+de\s+("
    + "|".join(_MESES.keys())
    + r")(?:\s+de\s+(\d{4}))?\b"
)

_PATRON_FECHA_NUMERICA = re.compile(
    r"\b(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{4}))?\b"
)


def _extraer_fecha_especifica(
    texto: str,
    hoy: date,
) -> date | None:
    """
    Reconoce fechas explícitas mencionadas en la pregunta,
    por ejemplo:
    - "el 25 de agosto"
    - "25 de agosto de 2026"
    - "25/08" o "25/08/2026"

    Si no se indica el año, se asume el año actual.
    Devuelve None si no se encuentra ninguna fecha o si la
    fecha no es válida (ej. "31 de febrero").
    """

    coincidencia = _PATRON_FECHA_TEXTUAL.search(texto)

    if coincidencia:
        dia = int(coincidencia.group(1))
        mes = _MESES[coincidencia.group(2)]
        anio = (
            int(coincidencia.group(3))
            if coincidencia.group(3)
            else hoy.year
        )

        try:
            return date(anio, mes, dia)
        except ValueError:
            return None

    coincidencia = _PATRON_FECHA_NUMERICA.search(texto)

    if coincidencia:
        dia = int(coincidencia.group(1))
        mes = int(coincidencia.group(2))
        anio = (
            int(coincidencia.group(3))
            if coincidencia.group(3)
            else hoy.year
        )

        if mes < 1 or mes > 12:
            return None

        try:
            return date(anio, mes, dia)
        except ValueError:
            return None

    return None


def _fecha_legible(valor: date) -> str:
    dias_semana = (
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    )

    nombres_mes = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre",
        "diciembre",
    )

    return (
        f"{dias_semana[valor.weekday()]} "
        f"{valor.day} de {nombres_mes[valor.month - 1]}"
    )


_PATRON_MES_COMPLETO = re.compile(
    r"\ben\s+("
    + "|".join(_MESES.keys())
    + r")(?:\s+de\s+(\d{4}))?\b"
)


def _ultimo_dia_mes(anio: int, mes: int) -> date:
    if mes == 12:
        siguiente = date(anio + 1, 1, 1)
    else:
        siguiente = date(anio, mes + 1, 1)

    return siguiente - timedelta(days=1)


def _extraer_mes_completo(
    texto: str,
    hoy: date,
) -> tuple[date, date, str] | None:
    """
    Reconoce referencias a un mes completo sin día
    puntual, por ejemplo "en septiembre" o "en
    septiembre de 2026". Devuelve (desde, hasta,
    nombre_mes) o None si no aplica.

    Se evalúa DESPUÉS de _extraer_fecha_especifica,
    así que una fecha puntual como "25 de agosto"
    siempre tiene prioridad sobre esta coincidencia
    más amplia.
    """

    coincidencia = _PATRON_MES_COMPLETO.search(texto)

    if not coincidencia:
        return None

    nombre_mes = coincidencia.group(1)
    mes = _MESES[nombre_mes]
    anio = (
        int(coincidencia.group(2))
        if coincidencia.group(2)
        else hoy.year
    )

    desde = date(anio, mes, 1)
    hasta = _ultimo_dia_mes(anio, mes)

    return desde, hasta, nombre_mes


def _normalizar(texto: str) -> str:
    texto = texto.strip().lower()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    return re.sub(r"\s+", " ", texto)


def _codigo_visita(visita_id: int) -> str:
    return f"VIS-{visita_id:06d}"


def _valor_ubicacion(
    ubicacion,
    atributo: str,
    predeterminado=None,
):
    return getattr(
        ubicacion,
        atributo,
        predeterminado,
    )


def _convertir_visita(evento) -> AgendaAgenteVisita:
    ubicacion = evento.ubicacion

    latitud = _valor_ubicacion(
        ubicacion,
        "latitud",
    )
    longitud = _valor_ubicacion(
        ubicacion,
        "longitud",
    )

    return AgendaAgenteVisita(
        id=evento.id,
        codigo=_codigo_visita(evento.id),
        fecha=evento.fecha_visita,
        hora_inicio=evento.hora_inicio,
        hora_fin=evento.hora_fin,
        empresa=evento.cliente.empresa,
        servicio=evento.servicio,
        tipo_visita=evento.tipo_visita,
        estado=evento.estado,
        ciudad=ubicacion.ciudad,
        departamento=ubicacion.departamento,
        ubicacion_validada=bool(
            _valor_ubicacion(
                ubicacion,
                "ubicacion_validada",
                False,
            )
        ),
        tiene_coordenadas=(
            latitud is not None
            and longitud is not None
        ),
    )


def _ordenar_eventos(eventos: list) -> list:
    return sorted(
        eventos,
        key=lambda evento: (
            evento.fecha_visita,
            evento.hora_inicio is None,
            evento.hora_inicio,
            evento.id,
        ),
    )


def _hora_texto(valor) -> str:
    if valor is None:
        return "sin hora definida"

    return valor.strftime("%H:%M")


def _ubicacion_texto(visita: AgendaAgenteVisita) -> str:
    partes = [
        visita.ciudad,
        visita.departamento,
    ]

    ubicacion = ", ".join(
        parte
        for parte in partes
        if parte
    )

    return ubicacion or "sin ubicación registrada"


def _sujeto_posesivo(titular: str | None) -> str:
    """
    'tu' / 'del equipo' / 'de Natalia Martínez'
    """
    if titular is None:
        return "tu"

    if titular == TITULAR_EQUIPO:
        return "del equipo"

    return f"de {titular}"


def _verbo_tener(titular: str | None) -> str:
    """
    'Tienes' / 'El equipo tiene' / 'Natalia Martínez tiene'
    """
    if titular is None:
        return "Tienes"

    if titular == TITULAR_EQUIPO:
        return "El equipo tiene"

    return f"{titular} tiene"


def _verbo_no_tener(titular: str | None) -> str:
    """
    'No tienes' / 'El equipo no tiene' / 'Natalia Martínez no tiene'
    """
    if titular is None:
        return "No tienes"

    if titular == TITULAR_EQUIPO:
        return "El equipo no tiene"

    return f"{titular} no tiene"


def _articulo_posesivo(titular: str | None) -> str:
    """
    'Tu' / 'La' (para 'La siguiente visita del equipo/de Natalia')
    """
    if titular is None:
        return "Tu"

    return "La"


def _de_quien(titular: str | None) -> str:
    """
    '' / ' del equipo' / ' de Natalia Martínez'
    """
    if titular is None:
        return ""

    if titular == TITULAR_EQUIPO:
        return " del equipo"

    return f" de {titular}"


def _resumen_visitas(
    visitas: list[AgendaAgenteVisita],
    estado: str | None = None,
    ciudad: str | None = None,
    titular: str | None = None,
) -> str:
    if not visitas:
        etiquetas_estado = {
            "PROGRAMADA": "programadas",
            "EN_PROCESO": "en proceso",
            "FINALIZADA": "finalizadas",
            "CANCELADA": "canceladas",
        }

        ciudad_texto = None
        if ciudad and _normalizar(ciudad) != "sin_ciudad":
            ciudad_texto = ciudad.strip()

        no_tiene = _verbo_no_tener(titular)

        if estado:
            etiqueta = etiquetas_estado.get(estado, estado.lower())
            if ciudad_texto:
                return (
                    f"{no_tiene} visitas {etiqueta} en "
                    f"{ciudad_texto} para ese período."
                )
            return f"{no_tiene} visitas {etiqueta} para ese período."

        if ciudad_texto:
            return f"{no_tiene} visitas en {ciudad_texto} para ese período."

        return f"{no_tiene} visitas para ese período."

    lineas: list[str] = []

    for visita in visitas:
        lineas.append(
            (
                f"{_hora_texto(visita.hora_inicio)} "
                f"{visita.codigo}, "
                f"{visita.empresa}, "
                f"{_ubicacion_texto(visita)}."
            )
        )

    tiene = _verbo_tener(titular)

    if len(visitas) == 1:
        encabezado = f"{tiene} 1 visita: "
    else:
        encabezado = f"{tiene} {len(visitas)} visitas: "

    return encabezado + " ".join(lineas)


def _inicio_fin_semana(
    referencia: date,
) -> tuple[date, date]:
    inicio = referencia - timedelta(
        days=referencia.weekday()
    )
    fin = inicio + timedelta(days=6)

    return inicio, fin


def _consultar(
    db: Session,
    asesor_id: int | None,
    desde: date,
    hasta: date,
    estado: str | None = None,
) -> list:
    return _ordenar_eventos(
        listar_eventos(
            db=db,
            desde=desde,
            hasta=hasta,
            asesor_id=asesor_id,
            estado=estado,
        )
    )


def _fin_mes(referencia: date) -> date:
    if referencia.month == 12:
        siguiente = date(referencia.year + 1, 1, 1)
    else:
        siguiente = date(
            referencia.year,
            referencia.month + 1,
            1,
        )

    return siguiente - timedelta(days=1)


def _resolver_periodo(
    periodo: str,
    hoy: date,
) -> tuple[date, date] | None:
    if periodo == "HOY":
        return hoy, hoy

    if periodo == "MANANA":
        manana = hoy + timedelta(days=1)
        return manana, manana

    if periodo == "ESTA_SEMANA":
        return _inicio_fin_semana(hoy)

    if periodo == "RESTO_SEMANA":
        _, fin = _inicio_fin_semana(hoy)
        return hoy, fin

    if periodo == "ESTE_MES":
        inicio = date(hoy.year, hoy.month, 1)
        return inicio, _fin_mes(hoy)

    if periodo == "RESTO_MES":
        return hoy, _fin_mes(hoy)

    return None


def _filtrar_ciudad(
    eventos: list,
    ciudad: str | None,
) -> list:
    if not ciudad or _normalizar(ciudad) == "sin_ciudad":
        return eventos

    ciudad_objetivo = _normalizar(ciudad)

    return [
        evento
        for evento in eventos
        if evento.ubicacion
        and evento.ubicacion.ciudad
        and _normalizar(evento.ubicacion.ciudad)
        == ciudad_objetivo
    ]


def _respuesta_fuera_dominio() -> AgendaAgenteRespuesta:
    return AgendaAgenteRespuesta(
        respuesta=(
            "Soy el Asistente de Agenda de SICOE. "
            "Puedo ayudarte únicamente con tus visitas, "
            "horarios, ubicaciones y actividades programadas."
        ),
        intencion="FUERA_DE_DOMINIO",
        fuera_de_dominio=True,
    )


def _respuesta_solo_mi_agenda() -> AgendaAgenteRespuesta:
    return AgendaAgenteRespuesta(
        respuesta=(
            "Por seguridad solo puedo consultar "
            "tu propia agenda de visitas."
        ),
        intencion="OTRO_ASESOR_NO_AUTORIZADO",
        fuera_de_dominio=False,
    )


def _respuesta_sin_asesor() -> AgendaAgenteRespuesta:
    return AgendaAgenteRespuesta(
        respuesta=(
            "Tu usuario no tiene un asesor asociado. "
            "No puedo consultar una agenda personal "
            "hasta que se configure esa asociación."
        ),
        intencion="USUARIO_SIN_ASESOR",
    )


def _parece_consulta_otro_asesor(
    texto: str,
) -> bool:
    """
    Detecta intentos explícitos de consultar la agenda
    de otra persona. Usado SOLO para el rol ASESOR
    (bloqueo por privacidad entre compañeros).

    Ejemplos:
    - agenda de Natalia
    - visitas de Natalia
    - que visitas tiene Natalia hoy
    - que tiene Natalia manana
    """

    patrones = (
        r"\bagenda de [a-z][a-z\s]{1,60}\b",
        r"\bvisitas de [a-z][a-z\s]{1,60}\b",
        r"\bque visitas tiene [a-z][a-z\s]{1,60}(?: hoy| manana| esta semana)?\b",
        r"\bque tiene [a-z][a-z\s]{1,60}(?: hoy| manana| esta semana)?\b",
    )

    if any(
        referencia in texto
        for referencia in _REFERENCIAS_PROPIAS
    ):
        return False

    return any(
        re.search(patron, texto)
        for patron in patrones
    )


_REFERENCIAS_PROPIAS = (
    "mi agenda",
    "mis visitas",
    "que visitas tengo",
    "que tengo hoy",
    "que tengo manana",
)


_PATRONES_NOMBRE_ASESOR = (
    r"\bagenda de ([a-z][a-z\s]{1,60})",
    r"\bvisitas de ([a-z][a-z\s]{1,60})",
    r"\bque visitas tiene ([a-z][a-z\s]{1,60})",
    r"\bque tiene ([a-z][a-z\s]{1,60})",
)

_SUFIJOS_TIEMPO = (
    "hoy",
    "manana",
    "esta semana",
    "para hoy",
    "para manana",
)


def _extraer_nombre_asesor_consultado(
    texto: str,
) -> str | None:
    """
    Usado SOLO para roles supervisores (ADMINISTRADOR/
    COORDINADOR). Extrae el nombre mencionado en preguntas
    como 'agenda de Natalia hoy' -> 'natalia'.

    Devuelve None si la pregunta es sobre la propia agenda
    del usuario (mi agenda, mis visitas...) o si no se
    detecta ningún nombre.
    """

    if any(
        referencia in texto
        for referencia in _REFERENCIAS_PROPIAS
    ):
        return None

    for patron in _PATRONES_NOMBRE_ASESOR:
        coincidencia = re.search(patron, texto)

        if not coincidencia:
            continue

        nombre = coincidencia.group(1).strip()

        for sufijo in _SUFIJOS_TIEMPO:
            if nombre.endswith(sufijo):
                nombre = nombre[: -len(sufijo)].strip()

        return nombre or None

    return None


def _nombre_completo_asesor(asesor: Asesor) -> str:
    partes = [
        asesor.primer_nombre,
        asesor.segundo_nombre,
        asesor.primer_apellido,
        asesor.segundo_apellido,
    ]

    return " ".join(
        parte.strip()
        for parte in partes
        if parte and parte.strip()
    )


def _buscar_asesores_por_nombre(
    db: Session,
    nombre_consulta: str,
) -> list[Asesor]:
    objetivo = _normalizar(nombre_consulta)

    if not objetivo:
        return []

    asesores = db.scalars(
        select(Asesor).where(Asesor.activo.is_(True))
    ).all()

    coincidencias = []

    for asesor in asesores:
        nombre_completo = _normalizar(
            _nombre_completo_asesor(asesor)
        )

        partes_normalizadas = [
            _normalizar(parte)
            for parte in (
                asesor.primer_nombre,
                asesor.segundo_nombre,
                asesor.primer_apellido,
                asesor.segundo_apellido,
            )
            if parte
        ]

        if (
            objetivo in nombre_completo
            or objetivo in partes_normalizadas
        ):
            coincidencias.append(asesor)

    return coincidencias


def _resolver_alcance_supervisor(
    db: Session,
    usuario_actual: Usuario,
    texto: str,
) -> tuple[int | None, str | None, AgendaAgenteRespuesta | None]:
    """
    Determina de quién es la agenda que un ADMINISTRADOR
    o COORDINADOR está consultando.

    Devuelve (asesor_id_filtro, titular, respuesta_error):
    - Si respuesta_error no es None, hay que devolverla
      inmediatamente sin continuar.
    - asesor_id_filtro=None significa "todos los asesores"
      (titular=TITULAR_EQUIPO en ese caso).
    """

    nombre_consulta = _extraer_nombre_asesor_consultado(texto)

    if nombre_consulta:
        encontrados = _buscar_asesores_por_nombre(
            db,
            nombre_consulta,
        )

        if not encontrados:
            return (
                None,
                None,
                AgendaAgenteRespuesta(
                    respuesta=(
                        f'No encontré ningún asesor activo '
                        f'llamado "{nombre_consulta}".'
                    ),
                    intencion="ASESOR_NO_ENCONTRADO",
                ),
            )

        if len(encontrados) > 1:
            nombres = ", ".join(
                _nombre_completo_asesor(asesor)
                for asesor in encontrados
            )

            return (
                None,
                None,
                AgendaAgenteRespuesta(
                    respuesta=(
                        f'Hay varios asesores que coinciden '
                        f'con "{nombre_consulta}": {nombres}. '
                        f'¿Puedes ser más específico?'
                    ),
                    intencion="ASESOR_AMBIGUO",
                ),
            )

        asesor = encontrados[0]

        return (
            asesor.id,
            _nombre_completo_asesor(asesor),
            None,
        )

    es_consulta_propia = any(
        referencia in texto
        for referencia in _REFERENCIAS_PROPIAS
    )

    if (
        es_consulta_propia
        and usuario_actual.asesor_id is not None
    ):
        return (
            usuario_actual.asesor_id,
            None,
            None,
        )

    # Sin nombre puntual: agenda combinada de todo el equipo.
    return (
        None,
        TITULAR_EQUIPO,
        None,
    )


def consultar_agenda_estructurada(
    db: Session,
    usuario_actual: Usuario,
    periodo: str,
    ciudad: str = "SIN_CIUDAD",
    estado: str = "SIN_ESTADO",
) -> AgendaAgenteRespuesta:
    """
    Consulta operativa para n8n.

    Seguridad:
    - No recibe asesor_id explícito en el request.
    - ASESOR: siempre usa usuario_actual.asesor_id (propio).
    - ADMINISTRADOR/COORDINADOR: si no tienen asesor_id
      propio, consultan la agenda combinada de todo el
      equipo en vez de recibir un bloqueo.
    """

    es_supervisor = usuario_actual.rol in ROLES_SUPERVISOR

    if usuario_actual.asesor_id is None and not es_supervisor:
        return _respuesta_sin_asesor()

    asesor_id_filtro = usuario_actual.asesor_id
    titular = None

    if usuario_actual.asesor_id is None and es_supervisor:
        asesor_id_filtro = None
        titular = TITULAR_EQUIPO

    hoy = datetime.now(ZONA_COLOMBIA).date()
    rango = _resolver_periodo(periodo, hoy)

    if rango is None:
        return AgendaAgenteRespuesta(
            respuesta=(
                "Indícame el período de la agenda que deseas "
                "consultar, por ejemplo hoy, mañana, esta "
                "semana o este mes."
            ),
            intencion="FALTA_PERIODO",
        )

    desde, hasta = rango
    estado_filtro = (
        None
        if estado == "SIN_ESTADO"
        else estado
    )

    eventos = _consultar(
        db=db,
        asesor_id=asesor_id_filtro,
        desde=desde,
        hasta=hasta,
        estado=estado_filtro,
    )

    eventos = _filtrar_ciudad(
        eventos,
        ciudad,
    )

    visitas = [
        _convertir_visita(evento)
        for evento in eventos
    ]

    return AgendaAgenteRespuesta(
        respuesta=_resumen_visitas(
            visitas,
            estado=estado_filtro,
            ciudad=ciudad,
            titular=titular,
        ),
        intencion="CONSULTAR_AGENDA",
        fecha_desde=desde,
        fecha_hasta=hasta,
        total_visitas=len(visitas),
        visitas=visitas,
    )


def responder_pregunta_agenda(
    db: Session,
    usuario_actual: Usuario,
    pregunta: str,
) -> AgendaAgenteRespuesta:
    """
    Motor de Agenda.

    - ASESOR: dominio cerrado a su propia agenda. No puede
      consultar la agenda de otro asesor.
    - ADMINISTRADOR/COORDINADOR: pueden consultar la agenda
      combinada de todo el equipo, o la de un asesor
      específico mencionándolo por nombre
      (ej. "agenda de Natalia hoy").
    """

    texto = _normalizar(pregunta)

    es_supervisor = usuario_actual.rol in ROLES_SUPERVISOR

    if (
        not es_supervisor
        and _parece_consulta_otro_asesor(texto)
    ):
        return _respuesta_solo_mi_agenda()

    if not _es_dominio_agenda(texto):
        return _respuesta_fuera_dominio()

    if es_supervisor:
        (
            asesor_id,
            titular,
            error,
        ) = _resolver_alcance_supervisor(
            db,
            usuario_actual,
            texto,
        )

        if error is not None:
            return error
    else:
        if usuario_actual.asesor_id is None:
            return _respuesta_sin_asesor()

        asesor_id = usuario_actual.asesor_id
        titular = None

    hoy = datetime.now(
        ZONA_COLOMBIA
    ).date()

    fecha_especifica = _extraer_fecha_especifica(
        texto,
        hoy,
    )

    if fecha_especifica is not None:
        eventos = _consultar(
            db,
            asesor_id,
            fecha_especifica,
            fecha_especifica,
        )

        visitas = [
            _convertir_visita(evento)
            for evento in eventos
        ]

        no_tiene = _verbo_no_tener(titular)
        tiene = _verbo_tener(titular)
        fecha_texto = _fecha_legible(fecha_especifica)

        if not visitas:
            respuesta = (
                f"{no_tiene} visitas programadas "
                f"para el {fecha_texto}."
            )
        elif len(visitas) == 1:
            respuesta = (
                f"{tiene} 1 visita el {fecha_texto}: "
                + " ".join(
                    f"{_hora_texto(v.hora_inicio)} "
                    f"{v.codigo}, {v.empresa}, "
                    f"{_ubicacion_texto(v)}."
                    for v in visitas
                )
            )
        else:
            respuesta = (
                f"{tiene} {len(visitas)} visitas "
                f"el {fecha_texto}: "
                + " ".join(
                    f"{_hora_texto(v.hora_inicio)} "
                    f"{v.codigo}, {v.empresa}, "
                    f"{_ubicacion_texto(v)}."
                    for v in visitas
                )
            )

        return AgendaAgenteRespuesta(
            respuesta=respuesta,
            intencion="AGENDA_FECHA_ESPECIFICA",
            fecha_desde=fecha_especifica,
            fecha_hasta=fecha_especifica,
            total_visitas=len(visitas),
            visitas=visitas,
        )

    mes_completo = _extraer_mes_completo(
        texto,
        hoy,
    )

    if mes_completo is not None:
        desde, hasta, nombre_mes = mes_completo

        eventos = _consultar(
            db,
            asesor_id,
            desde,
            hasta,
        )

        visitas = [
            _convertir_visita(evento)
            for evento in eventos
        ]

        no_tiene = _verbo_no_tener(titular)
        tiene = _verbo_tener(titular)

        if not visitas:
            respuesta = (
                f"{no_tiene} visitas programadas "
                f"en {nombre_mes}."
            )
        else:
            lineas = " ".join(
                f"{v.fecha.strftime('%d/%m')} "
                f"{_hora_texto(v.hora_inicio)} "
                f"{v.codigo}, {v.empresa}, "
                f"{_ubicacion_texto(v)}."
                for v in visitas
            )

            if len(visitas) == 1:
                respuesta = (
                    f"{tiene} 1 visita en {nombre_mes}: "
                    f"{lineas}"
                )
            else:
                respuesta = (
                    f"{tiene} {len(visitas)} visitas "
                    f"en {nombre_mes}: {lineas}"
                )

        return AgendaAgenteRespuesta(
            respuesta=respuesta,
            intencion="AGENDA_MES_ESPECIFICO",
            fecha_desde=desde,
            fecha_hasta=hasta,
            total_visitas=len(visitas),
            visitas=visitas,
        )

    if "manana" in texto:
        objetivo = hoy + timedelta(days=1)

        eventos = _consultar(
            db,
            asesor_id,
            objetivo,
            objetivo,
        )

        visitas = [
            _convertir_visita(evento)
            for evento in eventos
        ]

        return AgendaAgenteRespuesta(
            respuesta=_resumen_visitas(
                visitas,
                titular=titular,
            ),
            intencion="AGENDA_MANANA",
            fecha_desde=objetivo,
            fecha_hasta=objetivo,
            total_visitas=len(visitas),
            visitas=visitas,
        )

    if (
        "esta semana" in texto
        or "semana" in texto
    ):
        desde, hasta = _inicio_fin_semana(hoy)

        eventos = _consultar(
            db,
            asesor_id,
            desde,
            hasta,
        )

        visitas = [
            _convertir_visita(evento)
            for evento in eventos
        ]

        return AgendaAgenteRespuesta(
            respuesta=_resumen_visitas(
                visitas,
                titular=titular,
            ),
            intencion="AGENDA_SEMANA",
            fecha_desde=desde,
            fecha_hasta=hasta,
            total_visitas=len(visitas),
            visitas=visitas,
        )

    if (
        "proxima" in texto
        or "proximo" in texto
        or "siguiente" in texto
    ):
        hasta = hoy + timedelta(days=60)

        eventos = _consultar(
            db,
            asesor_id,
            hoy,
            hasta,
        )

        futuras = [
            _convertir_visita(evento)
            for evento in eventos
            if evento.estado != "CANCELADA"
        ]

        if not futuras:
            no_tiene = _verbo_no_tener(titular)

            return AgendaAgenteRespuesta(
                respuesta=(
                    f"{no_tiene} próximas visitas "
                    f"en los siguientes 60 días."
                ),
                intencion="PROXIMA_VISITA",
                fecha_desde=hoy,
                fecha_hasta=hasta,
            )

        visita = futuras[0]

        articulo = _articulo_posesivo(titular)
        de_quien = _de_quien(titular)

        if (
            "donde" in texto
            or "ubicacion" in texto
        ):
            respuesta = (
                f"{articulo} siguiente visita{de_quien} es "
                f"{visita.codigo} con "
                f"{visita.empresa}, "
                f"en {_ubicacion_texto(visita)}, "
                f"a las {_hora_texto(visita.hora_inicio)}."
            )
        else:
            respuesta = (
                f"{articulo} siguiente visita{de_quien} es "
                f"{visita.codigo} con "
                f"{visita.empresa}, el "
                f"{visita.fecha.strftime('%d/%m/%Y')} "
                f"a las {_hora_texto(visita.hora_inicio)}."
            )

        return AgendaAgenteRespuesta(
            respuesta=respuesta,
            intencion="PROXIMA_VISITA",
            fecha_desde=hoy,
            fecha_hasta=hasta,
            total_visitas=1,
            visitas=[visita],
        )

    # Consultas sobre HOY: por defecto dentro del dominio.
    eventos = _consultar(
        db,
        asesor_id,
        hoy,
        hoy,
    )

    visitas = [
        _convertir_visita(evento)
        for evento in eventos
    ]

    if "termino" in texto or "ultima" in texto:
        articulo = _articulo_posesivo(titular)
        de_quien = _de_quien(titular)

        if not visitas:
            no_tiene = _verbo_no_tener(titular)
            respuesta = (
                f"{no_tiene} visitas programadas para hoy."
            )
        else:
            ultima = visitas[-1]
            fin = (
                ultima.hora_fin
                or ultima.hora_inicio
            )
            respuesta = (
                f"{articulo} última visita de hoy{de_quien} es "
                f"{ultima.codigo} con "
                f"{ultima.empresa}. "
                f"{articulo} jornada de visitas{de_quien} "
                f"termina aproximadamente a las "
                f"{_hora_texto(fin)}."
            )

        return AgendaAgenteRespuesta(
            respuesta=respuesta,
            intencion="FIN_JORNADA_HOY",
            fecha_desde=hoy,
            fecha_hasta=hoy,
            total_visitas=len(visitas),
            visitas=visitas,
        )

    if "primera" in texto:
        articulo = _articulo_posesivo(titular)
        de_quien = _de_quien(titular)

        if not visitas:
            no_tiene = _verbo_no_tener(titular)
            respuesta = (
                f"{no_tiene} visitas programadas para hoy."
            )
            seleccionadas: list[
                AgendaAgenteVisita
            ] = []
        else:
            primera = visitas[0]
            seleccionadas = [primera]
            respuesta = (
                f"{articulo} primera visita de hoy{de_quien} es "
                f"{primera.codigo} con "
                f"{primera.empresa} a las "
                f"{_hora_texto(primera.hora_inicio)}, "
                f"en {_ubicacion_texto(primera)}."
            )

        return AgendaAgenteRespuesta(
            respuesta=respuesta,
            intencion="PRIMERA_VISITA_HOY",
            fecha_desde=hoy,
            fecha_hasta=hoy,
            total_visitas=len(seleccionadas),
            visitas=seleccionadas,
        )

    return AgendaAgenteRespuesta(
        respuesta=_resumen_visitas(
            visitas,
            titular=titular,
        ),
        intencion="AGENDA_HOY",
        fecha_desde=hoy,
        fecha_hasta=hoy,
        total_visitas=len(visitas),
        visitas=visitas,
    )


def _es_dominio_agenda(texto: str) -> bool:
    palabras = (
        "agenda",
        "visita",
        "visitas",
        "tengo hoy",
        "tengo manana",
        "tengo mañana",
        "proxima",
        "proximo",
        "siguiente",
        "horario",
        "ubicacion",
        "ubicación",
        "donde queda",
        "dónde queda",
        "a que hora",
        "qué hora",
        "termino hoy",
        "semana",
    )

    return any(
        palabra in texto
        for palabra in palabras
    )
